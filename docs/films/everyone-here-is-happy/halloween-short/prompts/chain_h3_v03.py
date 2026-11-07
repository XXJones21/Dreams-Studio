"""v2 pass (2026-11-01): shot chunks chained the Dreams way. Shot N starts on shot N-1's last used frame.

Josh: "We should still make them in the shot chunks, its just that we take the last frame from the previous
shot and use that as the first frame, just like we did in dreams."

  S01      : Pika H3 Flex ref2va (party + sarah pictures) + Fun ControlNet on the new blockout depth.
             Same graph as batch_h3_v02, at the chain resolution.
  S02..Snn : one graph. H3 FL2VA + FL2V turbo 4-step LoRA (the Dreams graph), MiniMaxH3ImageToVideo with
             first_frame = previous shot's frame 120, + Fun ControlNet on that shot's depth slice.
             Each shot saves its video and its frame-120 PNG (the next shot's first frame).

Frame bookkeeping: a take is 124 frames, the edit uses frames 0-119, and frame 120 is the first frame of the
next shot (the depth slice for shot N is blockout frames a..a+123, so its frame 120 = shot N+1 frame 0).

    python chain_h3_v03.py s01 <depth name> <out.json>
    python chain_h3_v03.py chain <depth name> <first frame name> S02,S03,... <out.json>
    python chain_h3_v03.py refchain <depth name> <first frame name> S05,S06,... <out.json>

refchain (Josh 2026-11-01, after S05+ fell apart: "we should be providing the set on each shot with a reference image
in order to follow the last frame. All references we generated should also be in every shot because the entire layout
changes multiple times"): Pika H3 Flex ref2va + Fun ControlNet, all 9 reference pictures in every shot (this shot's refs
first), and MiniMaxH3AddGuide pins the previous shot's frame 120 at frame 0, so the seam stays exact.
Prompts come from tracker/shots.json through batch_h3_v02.prompt(), rewritten for image-to-video.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch_h3_v02 as v2

W, H, LEN, CUT = 768, 1344, 124, 120
CN = (0.35, 0.35)  # strength, end_percent (v02 test winner)
PREFIX = "ehih/halloween/v2chain"


def seed(sid):
    return 30000 + int(sid[1:]) * 10 + 1


def i2v_prompt(sid):
    """The v02 prompt, minus the picture references (I2V has no ref pictures; the first frame carries the look)."""
    p = v2.prompt(sid)
    p = p.replace("[reference generation] ", "")
    p = re.sub(r" (?:in|from) <Picture \d+>", "", p)
    p = re.sub(r"retention_analysis:\n(?:.*\n)*?No audio reference is used in this generation\.\n\n", "", p)
    p = p.replace("The shot opens where the last one ended:", "The shot opens exactly on the given first frame:")
    return p


def depth_slice(g, nid, depth, sid):
    start = (int(sid[1:]) - 1) * LEN / 24 + 0.01
    g[f"{nid}a"] = {"class_type": "Video Slice", "inputs": {"video": ["174", 0], "start_time": round(start, 4),
                                                            "duration": round(LEN / 24, 4), "strict_duration": False},
                    "_meta": {"title": f"{sid} depth slice"}}
    g[f"{nid}b"] = {"class_type": "GetVideoComponents", "inputs": {"video": [f"{nid}a", 0]}, "_meta": {"title": f"{sid} depth frames"}}
    return [f"{nid}b", 0]


def s01_graph(depth):
    g = v2.graph("S01", v2.prompt("S01"), depth, seed("S01"), CN, "a")
    g.pop("115")
    g["136"]["inputs"]["width"], g["136"]["inputs"]["height"] = W, H
    g["92"]["inputs"]["filename_prefix"] = f"{PREFIX}/S01_v2_s{seed('S01')}"
    g["93"] = {"class_type": "ImageFromBatch", "inputs": {"image": ["122", 0], "batch_index": CUT, "length": 1}}
    g["94"] = {"class_type": "SaveImage", "inputs": {"images": ["93", 0], "filename_prefix": f"{PREFIX}/S01_f120"}}
    for k, n in g.items():
        n.setdefault("_meta", {"title": f"{n['class_type']} {k}"})
    return g


def chain_graph(depth, first, shots):
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}, "_meta": {"title": "H3 FL2VA"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors", "strength_model": 1}, "_meta": {"title": "FL2V turbo 4-step"}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}, "_meta": {"title": "H3 text encoder"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}, "_meta": {"title": "Video VAE"}},
        "5": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}, "_meta": {"title": "Audio VAE"}},
        "6": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}, "_meta": {"title": "Sampler"}},
        "7": {"class_type": "BasicScheduler", "inputs": {"scheduler": "simple", "steps": 4, "denoise": 1, "model": ["2", 0]}, "_meta": {"title": "4 steps"}},
        "8": {"class_type": "LoadImage", "inputs": {"image": first}, "_meta": {"title": f"first frame of {shots[0]}"}},
        "173": {"class_type": "ModelPatchLoader", "inputs": {"name": "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors"}, "_meta": {"title": "Fun ControlNet"}},
        "174": {"class_type": "LoadVideo", "inputs": {"file": depth}, "_meta": {"title": "blockout depth v3"}},
    }
    prev = ["8", 0]
    for sid in shots:
        n = int(sid[1:]) * 100
        ctrl = depth_slice(g, n, depth, sid)
        g[f"{n + 1}"] = {"class_type": "MiniMaxH3FunControlNetApply", "inputs": {"model": ["2", 0], "model_patch": ["173", 0], "vae": ["4", 0],
                         "strength": CN[0], "start_percent": 0.0, "end_percent": CN[1], "control_video": ctrl}, "_meta": {"title": f"{sid} ControlNet"}}
        g[f"{n + 2}"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["3", 0], "vae": ["4", 0], "prompt": i2v_prompt(sid),
                         "width": W, "height": H, "length": LEN, "first_frame": prev}, "_meta": {"title": f"{sid} I2V"}}
        g[f"{n + 3}"] = {"class_type": "RandomNoise", "inputs": {"noise_seed": seed(sid)}, "_meta": {"title": f"{sid} seed"}}
        g[f"{n + 4}"] = {"class_type": "BasicGuider", "inputs": {"model": [f"{n + 1}", 0], "conditioning": [f"{n + 2}", 0]}, "_meta": {"title": f"{sid} guider"}}
        g[f"{n + 5}"] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": [f"{n + 3}", 0], "guider": [f"{n + 4}", 0], "sampler": ["6", 0],
                         "sigmas": ["7", 0], "latent_image": [f"{n + 2}", 1]}, "_meta": {"title": f"{sid} sample"}}
        g[f"{n + 6}"] = {"class_type": "VAEDecode", "inputs": {"samples": [f"{n + 5}", 0], "vae": ["4", 0]}, "_meta": {"title": f"{sid} decode"}}
        g[f"{n + 7}"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": [f"{n + 5}", 0], "vae": ["5", 0]}, "_meta": {"title": f"{sid} audio"}}
        g[f"{n + 8}"] = {"class_type": "CreateVideo", "inputs": {"images": [f"{n + 6}", 0], "audio": [f"{n + 7}", 0], "fps": 24}, "_meta": {"title": f"{sid} video"}}
        g[f"{n + 9}"] = {"class_type": "SaveVideo", "inputs": {"video": [f"{n + 8}", 0], "filename_prefix": f"{PREFIX}/{sid}_v2_s{seed(sid)}",
                         "format": "auto", "codec": "auto"}, "_meta": {"title": f"save {sid}"}}
        g[f"{n + 10}"] = {"class_type": "ImageFromBatch", "inputs": {"image": [f"{n + 6}", 0], "batch_index": CUT, "length": 1}, "_meta": {"title": f"{sid} frame 120"}}
        g[f"{n + 11}"] = {"class_type": "SaveImage", "inputs": {"images": [f"{n + 10}", 0], "filename_prefix": f"{PREFIX}/{sid}_f120"}, "_meta": {"title": f"save {sid} frame 120"}}
        prev = [f"{n + 10}", 0]
    return g


ALL_REFS = ["party", "mascot", "pit", "tube", "junction", "sarah", "slide", "playways", "idol"]


def in_shot(sid):
    """This shot's references: the tracker refs plus Sarah / the ball pit / the mascot when the shot's own text has them."""
    zone, refs, cast, beats, end, sound, extra = v2.S[sid]
    text = " ".join([cast, end, *beats])
    own = list(refs)
    if zone == "party":  # the party room and its ball pit are the set for every party shot
        own += [r for r in ("party", "pit") if r not in own]
    for r, key in (("sarah", "Sarah"), ("pit", "ball pit"), ("mascot", "mascot")):
        if key in text and r not in own and not (r == "mascot" and "giant mascot" in text):
            own.append(r)
    return own


def ref_order(sid):
    own = in_shot(sid)
    return own + [r for r in ALL_REFS if r not in own]


def refchain_prompt(sid):
    """v02 prompt with this shot's on-screen refs, plus every other reference as look-only, and a fixed first frame."""
    own = in_shot(sid)
    refs = ref_order(sid)
    saved = v2.S[sid]
    v2.S[sid] = (saved[0], own, *saved[2:])
    try:
        p = v2.prompt(sid)
    finally:
        v2.S[sid] = saved
    deep = int(sid[1:3]) >= 16
    extra_subs, extra_ret = [], []
    for k, r in enumerate(refs[len(own):], start=len(own) + 1):
        d = (v2.DESC_TUBE_DEEP if (r == "tube" and deep) else v2.DESC[r]).format(n=k)
        if int(sid[1:3]) >= 18:
            d = d.replace(", a yellow star bracelet on her left wrist", "")
        what = "she is not in this shot" if r == "sarah" else "a different part of the building; it does not appear in this shot"
        extra_subs.append(f"<Subject {k}> is {d} Look reference only: {what}.")
        extra_ret.append(f"<Subject {k}>: not shown in this shot.")
    NL = chr(10)
    head, rest = p.split(NL + NL + "summary:", 1)
    p = head + NL + NL.join(extra_subs) + NL + NL + "summary:" + rest
    p = p.replace("No audio reference is used in this generation.", NL.join(extra_ret) + NL + "No audio reference is used in this generation.")
    p = p.replace("The shot opens where the last one ended:", "The first frame is given and fixed; the shot opens exactly on it:")
    return p


def refchain_graph(depth, first, shots, tag="v3", cn=None, prompt_fn=None, off=1):
    cn = cn or CN
    prompt_fn = prompt_fn or refchain_prompt
    g = {
        "127": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}, "_meta": {"title": "H3 ref2va"}},
        "145": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["127", 0], "lora_name": "pika_h3_flex_ref2va_v1_bf16.safetensors", "strength_model": 1}, "_meta": {"title": "Pika H3 Flex"}},
        "128": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}, "_meta": {"title": "H3 text encoder"}},
        "119": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}, "_meta": {"title": "Video VAE"}},
        "120": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}, "_meta": {"title": "Audio VAE"}},
        "123": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "lcm"}, "_meta": {"title": "Sampler"}},
        "147": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0"}, "_meta": {"title": "Sigmas"}},
        "173": {"class_type": "ModelPatchLoader", "inputs": {"name": "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors"}, "_meta": {"title": "Fun ControlNet"}},
        "174": {"class_type": "LoadVideo", "inputs": {"file": depth}, "_meta": {"title": "blockout depth"}},
    }
    if first:  # None: the first shot starts from the references alone (S01)
        g["8"] = {"class_type": "LoadImage", "inputs": {"image": first}, "_meta": {"title": f"first frame of {shots[0]}"}}
    for k, r in enumerate(ALL_REFS):
        g[f"15{k}"] = {"class_type": "LoadImage", "inputs": {"image": v2.K[r]}, "_meta": {"title": f"ref {r}"}}
    prev = ["8", 0] if first else None
    for sid in shots:
        n = int(sid[1:]) * 100
        ctrl = depth_slice(g, n, depth, sid)
        g[f"{n + 1}"] = {"class_type": "MiniMaxH3FunControlNetApply", "inputs": {"model": ["145", 0], "model_patch": ["173", 0], "vae": ["119", 0],
                         "strength": cn[0], "start_percent": 0.0, "end_percent": cn[1], "control_video": ctrl}, "_meta": {"title": f"{sid} ControlNet"}}
        r2v = {"clip": ["128", 0], "vae": ["119", 0], "audio_vae": ["120", 0], "prompt": prompt_fn(sid), "width": W, "height": H,
               "length": LEN, "ref_image_size": "match"}
        for k, r in enumerate(ref_order(sid)):
            r2v[f"ref_images.ref_image_{k}"] = [f"15{ALL_REFS.index(r)}", 0]
        g[f"{n + 2}"] = {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": r2v, "_meta": {"title": f"{sid} refs"}}
        if prev:
          g[f"{n + 12}"] = {"class_type": "MiniMaxH3AddGuide", "inputs": {"positive": [f"{n + 2}", 0], "latent": [f"{n + 2}", 1], "frame_idx": 0,
                          "vae": ["119", 0], "audio_vae": ["120", 0], "image": prev}, "_meta": {"title": f"{sid} first frame guide"}}
        g[f"{n + 3}"] = {"class_type": "RandomNoise", "inputs": {"noise_seed": seed(sid) + off}, "_meta": {"title": f"{sid} seed"}}
        g[f"{n + 4}"] = {"class_type": "BasicGuider", "inputs": {"model": [f"{n + 1}", 0], "conditioning": [f"{n + 12}" if prev else f"{n + 2}", 0]}, "_meta": {"title": f"{sid} guider"}}
        g[f"{n + 5}"] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": [f"{n + 3}", 0], "guider": [f"{n + 4}", 0], "sampler": ["123", 0],
                         "sigmas": ["147", 0], "latent_image": [f"{n + 2}", 1]}, "_meta": {"title": f"{sid} sample"}}
        g[f"{n + 6}"] = {"class_type": "VAEDecode", "inputs": {"samples": [f"{n + 5}", 0], "vae": ["119", 0]}, "_meta": {"title": f"{sid} decode"}}
        g[f"{n + 7}"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": [f"{n + 5}", 0], "vae": ["120", 0]}, "_meta": {"title": f"{sid} audio"}}
        g[f"{n + 8}"] = {"class_type": "CreateVideo", "inputs": {"images": [f"{n + 6}", 0], "audio": [f"{n + 7}", 0], "fps": 24}, "_meta": {"title": f"{sid} video"}}
        g[f"{n + 9}"] = {"class_type": "SaveVideo", "inputs": {"video": [f"{n + 8}", 0], "filename_prefix": f"{PREFIX}/{sid}_{tag}_s{seed(sid) + off}",
                         "format": "auto", "codec": "auto"}, "_meta": {"title": f"save {sid}"}}
        g[f"{n + 10}"] = {"class_type": "ImageFromBatch", "inputs": {"image": [f"{n + 6}", 0], "batch_index": CUT, "length": 1}, "_meta": {"title": f"{sid} frame 120"}}
        g[f"{n + 11}"] = {"class_type": "SaveImage", "inputs": {"images": [f"{n + 10}", 0], "filename_prefix": f"{PREFIX}/{sid}_{tag}_f120"}, "_meta": {"title": f"save {sid} frame 120"}}
        prev = [f"{n + 10}", 0]
    return g


# v4 (2026-11-01): the blockout is the source of truth. Log-depth control (scripts/depth_log.py: the old linear
# disparity left everything past ~2 m black, so the model only saw a table and a phone), a stronger ControlNet,
# and a camera/layout paragraph per shot read off the blockout (prompts/framing_from_blockout.json).
CN_V4 = (0.5, 0.5)
FRAMING = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "framing_from_blockout.json"), encoding="utf-8"))


def v4_prompt(sid):
    p = refchain_prompt(sid)
    lay = "Camera and layout, exactly as in the blockout: " + FRAMING[sid]
    if v2.S[sid][0] == "party" and sid != "S05":
        lay += " " + FRAMING["_room"]
    lay += " Keep everything at these distances and sizes; do not move the camera closer to the action than this."
    return p.replace("[Shot 1]", lay + chr(10) + chr(10) + "[Shot 1]", 1)


def v4_graph(depth, first, shots):
    return refchain_graph(depth, first, shots, tag="v4", cn=CN_V4, prompt_fn=v4_prompt, off=2)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "s01":
        g = s01_graph(sys.argv[2]); out = sys.argv[3]
    elif mode == "v4":
        g = v4_graph(sys.argv[2], None if sys.argv[3] == "none" else sys.argv[3], sys.argv[4].split(",")); out = sys.argv[5]
    elif mode == "refchain":
        g = refchain_graph(sys.argv[2], sys.argv[3], sys.argv[4].split(",")); out = sys.argv[5]
    else:
        g = chain_graph(sys.argv[2], sys.argv[3], sys.argv[4].split(",")); out = sys.argv[5]
    json.dump(g, open(out, "w", encoding="utf-8"), indent=1)
    print("wrote", out, len(g), "nodes")
