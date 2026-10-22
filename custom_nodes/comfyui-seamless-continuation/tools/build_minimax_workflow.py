"""Build the MiniMax-H3 continuation workflow (API format + UI format) from one node list.

The graph is the Oct 6 Pillars run as a single ComfyUI graph:
  keyframe -> H3 clip 1 -> Last Frame -> H3 clip 2 -> Last Frame -> H3 clip 3 -> Stitch -> Save Video
Models and settings match D:/dev/comfy-api-test/rebuild/scene_video_h3_i2v_pruned.json.

Usage: python tools/build_minimax_workflow.py [--server http://127.0.0.1:8189]
Reads /object_info for widget order and slot types, writes examples/minimax_continuation_{api,workflow}.json,
then validates both. Exits non-zero if validation finds problems.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES_DIR = Path(r"D:\dev\comfy-api-test\rebuild")
W, H, FRAMES, FPS, STEPS, SEED = 768, 1344, 124, 24, 4, 42
KEYFRAME = "pillars_still.png"

WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}


def load_prompts() -> list[str]:
    sys.path.insert(0, str(STYLES_DIR))
    from styles import POV, STYLES  # noqa: E402

    style = STYLES["pillars"]
    return [POV + style["look"] + beat for beat in style["beats"]]


def node_list(prompts: list[str]) -> list[dict]:
    """Each entry: id, class, title, group, col, row, inputs (API format: value or [src_id, slot])."""
    n = []

    def add(nid, cls, title, group, col, row, **inputs):
        n.append({"id": nid, "class": cls, "title": title, "group": group, "col": col, "row": row,
                  "inputs": inputs})

    add(1, "UnetLoaderGGUF", "H3 FL2VA pruned Q4_K_M", "Models", 0, 0,
        unet_name="MiniMax-H3-FL2VA-Pruned-Q4_K_M.gguf")
    add(2, "LoraLoaderModelOnly", "4-step turbo LoRA", "Models", 0, 1,
        model=[1, 0], lora_name="minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors",
        strength_model=1.0)
    add(3, "CLIPLoaderGGUF", "Qwen3-VL 32B text encoder", "Models", 0, 2,
        clip_name="qwen3vl_32b_minimax_h3-Q4_K_M.gguf", type="minimax")
    add(4, "VAELoader", "H3 video VAE", "Models", 0, 3, vae_name="minimax_h3_video_vae_int8_convrot.safetensors")
    add(5, "VAELoader", "H3 audio VAE", "Models", 0, 4, vae_name="minimax_h3_audio_vae_fp32.safetensors")
    add(6, "KSamplerSelect", None, "Models", 0, 5, sampler_name="res_multistep")
    add(7, "BasicScheduler", "4 steps (turbo)", "Models", 0, 6, model=[2, 0], scheduler="simple",
        steps=STEPS, denoise=1.0)
    add(8, "LoadImage", "Keyframe (Krea 2 still)", "Keyframe", 1, 0, image=KEYFRAME)

    first_frame = [8, 0]
    clip_videos = []
    for c in range(3):
        base = 100 * (c + 1)
        group, col = f"Clip {c + 1}", 2 + c
        add(base + 1, "MiniMaxH3ImageToVideo", f"Clip {c + 1}: image to video", group, col, 0,
            clip=[3, 0], vae=[4, 0], prompt=prompts[c], width=W, height=H, length=FRAMES, first_frame=first_frame)
        add(base + 2, "RandomNoise", None, group, col, 1, noise_seed=SEED + c + 1)
        add(base + 3, "BasicGuider", None, group, col, 2, model=[2, 0], conditioning=[base + 1, 0])
        add(base + 4, "SamplerCustomAdvanced", None, group, col, 3, noise=[base + 2, 0], guider=[base + 3, 0],
            sampler=[6, 0], sigmas=[7, 0], latent_image=[base + 1, 1])
        add(base + 5, "VAEDecode", None, group, col, 4, samples=[base + 4, 0], vae=[4, 0])
        add(base + 6, "VAEDecodeAudio", None, group, col, 5, samples=[base + 4, 0], vae=[5, 0])
        add(base + 7, "CreateVideo", None, group, col, 6, images=[base + 5, 0], audio=[base + 6, 0],
            fps=float(FPS), bit_depth=8, color_space="sRGB")
        clip_videos.append([base + 7, 0])
        if c < 2:
            add(base + 8, "SeamlessContinuationLastFrame", None, group, col, 7, video=[base + 7, 0])
            first_frame = [base + 8, 0]

    stitch_inputs = {f"clips.clip{i}": v for i, v in enumerate(clip_videos)}
    add(900, "SeamlessContinuationStitch", None, "Stitch", 5, 0, seam_frames=1, crf=18, **stitch_inputs)
    add(901, "SaveVideo", None, "Stitch", 5, 1, video=[900, 0], filename_prefix="seamless_minimax_h3",
        format="auto", codec="auto")  # same as the official H3 templates
    return n


def api_graph(nodes: list[dict]) -> dict:
    out = {}
    for node in nodes:
        inputs = {k: ([str(v[0]), v[1]] if isinstance(v, list) else v) for k, v in node["inputs"].items()}
        entry = {"class_type": node["class"], "inputs": inputs}
        if node["title"]:
            entry["_meta"] = {"title": node["title"]}
        out[str(node["id"])] = entry
    return out


def _spec_inputs(info: dict) -> list[tuple[str, list]]:
    """(name, spec) in the server's input order; Autogrow inputs are returned as-is.

    Inputs nested inside a DynamicCombo option (core SaveVideo's codec, under format) are also listed
    at the top level by /object_info; the frontend draws them once, inside the DynamicCombo, so skip them here.
    """
    order = info.get("input_order", {})
    specs = {**info["input"].get("required", {}), **info["input"].get("optional", {})}
    nested = set()
    for spec in specs.values():
        if spec[0] == "COMFY_DYNAMICCOMBO_V3":
            for choice in spec[1]["options"]:
                nested |= set(choice.get("inputs", {}).get("required", {}))
                nested |= set(choice.get("inputs", {}).get("optional", {}))
    names = order.get("required", []) + order.get("optional", [])
    return [(name, specs[name]) for name in names if name in specs and name not in nested]


def _is_widget(spec: list) -> bool:
    return isinstance(spec[0], list) or spec[0] in WIDGET_TYPES


def _widget_values(name: str, spec: list, values: dict) -> list:
    """Widget values for one input as the frontend stores them.

    DynamicCombo (COMFY_DYNAMICCOMBO_V3) stores the chosen key, then the widget values of the inputs
    that option adds, in order (core SaveVideo: format, then its nested codec).
    """
    options = spec[1] if len(spec) > 1 else {}
    if spec[0] == "COMFY_DYNAMICCOMBO_V3":
        choices = options["options"]
        value = values.get(name, options.get("default", choices[0]["key"]))
        chosen = next(c for c in choices if c["key"] == value)
        out = [value]
        nested = {**chosen.get("inputs", {}).get("required", {}), **chosen.get("inputs", {}).get("optional", {})}
        for sub_name, sub_spec in nested.items():
            out += _widget_values(sub_name, sub_spec, values)
        return out
    value = values.get(name)
    if value is None:
        value = options.get("default", spec[0][0] if isinstance(spec[0], list) and spec[0] else None)
    out = [value]
    if options.get("control_after_generate"):
        out.append("fixed")
    if options.get("image_upload"):
        out.append("image")
    return out


def _has_widgets(spec: list) -> bool:
    return _is_widget(spec) or spec[0] == "COMFY_DYNAMICCOMBO_V3"


NODE_W, NODE_H, COL_W, ROW_H, TOP = 360, 150, 460, 190, 260


def ui_graph(nodes: list[dict], object_info: dict) -> dict:
    links, link_id = [], 0
    ui_nodes = {}
    for order, node in enumerate(nodes):
        info = object_info[node["class"]]
        ui_inputs, widgets = [], []
        for name, spec in _spec_inputs(info):
            if spec[0] == "COMFY_AUTOGROW_V3":
                slot_type = list(spec[1]["template"]["input"]["required"].values())[0][0]
                for key in sorted(k for k in node["inputs"] if k.startswith(name + ".")):
                    ui_inputs.append({"name": key, "type": slot_type, "link": None, "_src": node["inputs"][key]})
                continue
            value = node["inputs"].get(name)
            if spec[0] == "COMFY_DYNAMICCOMBO_V3":
                widgets += _widget_values(name, spec, node["inputs"])
            elif _is_widget(spec):
                widgets += _widget_values(name, spec, node["inputs"])
                ui_inputs.append({"name": name, "type": "COMBO" if isinstance(spec[0], list) else spec[0],
                                  "widget": {"name": name}, "link": None})
            elif value is not None:
                ui_inputs.append({"name": name, "type": spec[0], "link": None, "_src": value})
            elif name in info["input"].get("required", {}):
                ui_inputs.append({"name": name, "type": spec[0], "link": None})
        outputs = [{"name": oname, "type": otype, "links": []}
                   for otype, oname in zip(info["output"], info.get("output_name", info["output"]))]
        group_rows = node["row"]
        ui = {"id": node["id"], "type": node["class"],
              "pos": [node["col"] * COL_W, TOP + group_rows * ROW_H],
              "size": [NODE_W, NODE_H], "flags": {}, "order": order, "mode": 0,
              "inputs": ui_inputs, "outputs": outputs,
              "properties": {"Node name for S&R": node["class"]}, "widgets_values": widgets}
        if node["title"]:
            ui["title"] = node["title"]
        ui_nodes[node["id"]] = ui

    for ui in ui_nodes.values():
        for slot, inp in enumerate(ui["inputs"]):
            src = inp.pop("_src", None)
            if src is None:
                continue
            link_id += 1
            origin = ui_nodes[src[0]]
            otype = origin["outputs"][src[1]]["type"]
            inp["link"] = link_id
            origin["outputs"][src[1]]["links"].append(link_id)
            links.append([link_id, src[0], src[1], ui["id"], slot, otype])

    groups = []
    for gid, title in enumerate(["Models", "Keyframe", "Clip 1", "Clip 2", "Clip 3", "Stitch"], start=1):
        members = [ui for ui, node in zip(ui_nodes.values(), nodes) if node["group"] == title]
        x0 = min(m["pos"][0] for m in members) - 20
        y0 = min(m["pos"][1] for m in members) - 50
        x1 = max(m["pos"][0] + m["size"][0] for m in members) + 20
        y1 = max(m["pos"][1] + m["size"][1] for m in members) + 20
        groups.append({"id": gid, "title": title, "bounding": [x0, y0, x1 - x0, y1 - y0],
                       "color": "#3f789e" if title.startswith("Clip") else "#8A8A8A",
                       "font_size": 24, "flags": {}})

    note = {"id": 999, "type": "MarkdownNote", "pos": [0, 0], "size": [1300, 200], "flags": {},
            "order": len(nodes), "mode": 0, "inputs": [], "outputs": [],
            "properties": {}, "title": "About this workflow",
            "widgets_values": [
                "## MiniMax-H3 continuation: three 5 s clips, one 15 s video\n"
                "Each clip starts on the **Last Frame** of the clip before it. **Stitch Continuation Clips** joins "
                "them and drops the repeated seam frame (with matching audio).\n\n"
                "Models and settings match the Oct 6 Pillars run (pruned FL2VA Q4_K_M GGUF, Qwen3-VL 32B GGUF, "
                "4-step turbo LoRA, 768x1344, 124 frames per clip).\n\n"
                "**Memory:** as one job, the three decoded clips stay in RAM next to H3. Run it on Comfy Cloud or a "
                "machine with more than 32 GB of RAM. On 32 GB, run each clip as its own job and stitch at the end."]}
    all_nodes = list(ui_nodes.values()) + [note]
    return {"id": str(uuid.uuid4()), "revision": 0, "last_node_id": max(u["id"] for u in all_nodes),
            "last_link_id": link_id, "nodes": all_nodes, "links": links, "groups": groups, "config": {},
            "extra": {"ds": {"scale": 0.55, "offset": [40, 40]}}, "version": 0.4}


def validate_api(graph: dict, object_info: dict) -> list[str]:
    problems = []
    for nid, node in graph.items():
        cls = node["class_type"]
        if cls not in object_info:
            problems.append(f"{nid}: unknown node {cls}")
            continue
        spec = object_info[cls]["input"]
        for name, s in spec.get("required", {}).items():
            if s[0] == "COMFY_AUTOGROW_V3":
                need = s[1]["template"]["min"]
                have = sum(1 for k in node["inputs"] if k.startswith(name + "."))
                if have < need:
                    problems.append(f"{nid} {cls}: {name} has {have} slots, needs {need}")
            elif name not in node["inputs"]:
                problems.append(f"{nid} {cls}: missing required input {name}")
        for name, value in node["inputs"].items():
            s = spec.get("required", {}).get(name) or spec.get("optional", {}).get(name)
            if s and isinstance(s[0], list) and not isinstance(value, list) and value not in s[0] and name != "image":
                problems.append(f"{nid} {cls}: {name}={value!r} is not installed or not an option")
    return problems


def validate_ui(workflow: dict, object_info: dict, node_values: dict) -> list[str]:
    problems = []
    out_refs, in_refs = {}, {}
    for node in workflow["nodes"]:
        for o in node.get("outputs", []):
            for lid in o.get("links") or []:
                out_refs[lid] = out_refs.get(lid, 0) + 1
        for i in node.get("inputs", []):
            if i.get("link") is not None:
                in_refs[i["link"]] = in_refs.get(i["link"], 0) + 1
        if node["type"] in object_info:
            expected = 0
            values = node_values.get(node["id"], {})
            for name, spec in _spec_inputs(object_info[node["type"]]):
                if spec[0] != "COMFY_AUTOGROW_V3" and _has_widgets(spec):
                    expected += len(_widget_values(name, spec, values))
            got = len(node.get("widgets_values") or [])
            if got != expected:
                problems.append(f"node {node['id']} {node['type']}: {got} widget values, expected {expected}")
    for link in workflow["links"]:
        lid = link[0]
        if out_refs.get(lid) != 1 or in_refs.get(lid) != 1:
            problems.append(f"link {lid}: on {out_refs.get(lid, 0)} outputs and {in_refs.get(lid, 0)} inputs")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8189")
    args = ap.parse_args()
    object_info = json.load(urllib.request.urlopen(f"{args.server}/object_info", timeout=60))

    nodes = node_list(load_prompts())
    api = api_graph(nodes)
    ui = ui_graph(nodes, object_info)
    examples = ROOT / "examples"
    (examples / "minimax_continuation_api.json").write_text(json.dumps(api, indent=1), encoding="utf-8")
    (examples / "minimax_continuation_workflow.json").write_text(json.dumps(ui, indent=1), encoding="utf-8")

    api_problems = validate_api(api, object_info)
    ui_problems = validate_ui(ui, object_info, {n["id"]: n["inputs"] for n in nodes})
    print(f"API graph: {len(api)} nodes, problems: {len(api_problems)}")
    print(f"UI graph: {len(ui['nodes'])} nodes, {len(ui['links'])} links, {len(ui['groups'])} groups, "
          f"problems: {len(ui_problems)}")
    for p in api_problems + ui_problems:
        print("  -", p)
    sys.exit(1 if api_problems or ui_problems else 0)


if __name__ == "__main__":
    main()
