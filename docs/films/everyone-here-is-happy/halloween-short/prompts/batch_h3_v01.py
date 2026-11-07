"""Single-pass H3 batch for every shot except S24-S26 (covered by the 15 s continuous take).

    python batch_h3_v01.py <depth_all.mp4 Cloud name> <out.json>

Each item: Pika H3 Flex ref2va LoRA -> MiniMax H3 Fun ControlNet on that shot's slice of the joined
inverse-depth video (36 x 124 frames) -> BasicGuider; LCM + ManualSigmas; 124 frames, 9:16.
Picture refs come from the locked style keys. One take per shot (Josh 2026-10-31: batch, single pass,
rough assembly, resubmit bad takes after).
"""
import json, sys

K = {
    "party": "5c90d4bab53db5a503bcef6c8062c5e3fdb4edaecfbc7aff08cfb541fd71fefc.png",
    "mascot": "682b09df3ab691335398c3abac8437154dc1fc9b05fcfd0ab85be620b07497b8.png",
    "pit": "22df8380adf787f84f4203ea3961aea6effcbf94fcdeb4fee1cf1d4839c49cd3.png",
    "tube": "723c38e5ea6b233f56836c0a176ce036439d7c880e74cef624c2e2e1f63583af.png",
    "junction": "fab1bdc6b71279cd4a2878182f7422872fdf268ed13f4cb6de511d55eeff3b81.png",
    "sarah": "aa3e743e448b406c5d0321b85fca4f2dab372a8292b4b194b93e0ecfc57ee451.png",
    "slide": "4461501730de79ed771e5b537b0367bffe317c9768f39837cf11fe6afc632a92.png",
    "playways": "05d166539983d8dc8d26c71b8f5ae5faf750431927477dc62f41a4bb79d394c4.png",
    "idol": "8c92a1285baeb92a3fbefa2a80d7b2037afa58541cfc8f54536291af20fd71ae.png",
}
DESC = {
    "party": "Happy Hank's Pizza & Play in <Picture {n}>: a cheap 1990s pizza-and-games party room, drop ceiling with flat fluorescent panels, laminate party tables with paper tablecloths and balloons, purple patterned carpet, arcade glow, a yellow-poled play structure with red, blue and teal tubes behind a ball pit. Ordinary, loud, a little grubby.",
    "mascot": "the party mascot in <Picture {n}>: one person in a cheap worn orange plush costume with a foam head, fixed wide grin, yellow belly, oversized gloves. Exactly one mascot.",
    "pit": "the ball pit in <Picture {n}>: low blue padded walls, colored plastic balls, a foam step, the yellow-poled play structure rising behind it.",
    "tube": "the play-structure tube in <Picture {n}>: dull faded rotomolded plastic, scuffed padded floor, round bolt caps at the joints, thin warm light through the plastic. Cramped for an adult, still ordinary.",
    "junction": "the junction chamber in <Picture {n}>: faded teal plastic walls, red and yellow tube mouths leading off, a strip of net overhead, scuffed padded floor.",
    "sarah": "Sarah, the girl in <Picture {n}>: about five, shoulder-length brown hair, blue long-sleeve top, dark grey leggings, cream velcro sneakers, a yellow star bracelet on her left wrist.",
    "slide": "the slide in <Picture {n}>: a dull faded orange rotomolded plastic tube slide, matte chalky plastic, plastic collars with fat round bolt caps.",
    "playways": "the Playways in <Picture {n}>: a dense knot of grimy faded tube slides, torn sagging net catwalks, dark mesh-caged towers, dusty bubble pods, endless towers of small amber windows in cold blue-grey haze, a vast sea of dull colored balls. No ceiling ever visible.",
    "idol": "the giant mascot idol in <Picture {n}>: the same grinning orange mascot face, as one enormous still statue. Exactly one. It never moves.",
}
HANDS = "The viewer's own two hands: a man in his mid-30s, light-to-medium warm skin, charcoal cotton overshirt cuffs. They are the only part of the viewer ever visible."
LOOK = {
    "party": "brighter, flatter fluorescent light, an ordinary room",
    "structure": "dim and warm, light leaking through plastic, getting dimmer",
    "slide": "dim orange glow through translucent plastic",
    "playways": "gloomy and underlit, cold desaturated blue-grey dark against weak amber practicals, drifting haze",
}

# id: (zone, refs, hands_visible, beats, sound, extra_avoid)
S = {
 "S01": ("party", ["party"], True, "At 0 seconds we sit at the party table holding a paper coffee cup in both hands, steam rising. Over five seconds the view pans slowly left to right across the birthday party: kids eating pizza, balloons, paper plates, the play structure at the back. The hands stay on the cup.", "Party din, kids shrieking, arcade bleeps, a distant birthday song, fluorescent hum."),
 "S02": ("party", ["party", "sarah"], True, "At 0 seconds a paper birthday crown drops down over the top of the view, its yellow zigzag edge filling the upper frame. One hand rises and lifts it. The view turns right to Sarah standing on the seat beside us, pleased with herself, reaching to straighten the crown.", "Paper rustle, Sarah giggles, party din."),
 "S03": ("party", ["party", "sarah"], False, "Sarah climbs down off the seat and walks to the edge of the table; the view follows her down and along. She turns back and says something with a serious little face.", "Sarah, small and clear: \"You say ready.\" Party din behind."),
 "S04": ("party", ["party", "sarah"], True, "A hand sets the paper crown on the table. The view lifts as Sarah hops over a line in the carpet pattern, lands, and looks back to check we saw.", "A tired man's voice off-screen: \"Ready.\" A small thump of sneakers on carpet. Party din."),
 "S05": ("party", ["mascot", "party"], False, "Across the room the mascot waves at a table of kids, turns slowly, and waves directly at us. Its grin never changes. It is a person in a costume, moving like one.", "Party din, a kid laughing, the muffled squeak of the costume."),
 "S06": ("party", ["party"], True, "The view tilts down to a phone lying face up on the sticky table, buzzing, the screen lighting up with a message notification. The words are not readable.", "Phone vibration rattling on laminate, party din."),
 "S07": ("party", ["party"], True, "The phone is in one hand, close. The thumb starts typing a reply, pauses, hovers, stops. The screen text is not readable.", "Soft thumb taps, then nothing, party din."),
 "S08": ("party", ["pit", "sarah"], False, "The view looks up from the table to the ball pit across the room: Sarah at the padded rail, waving both arms at us, bouncing.", "Sarah calls across the room: \"Dad. Watch this one.\" A man's voice nearby: \"One second.\""),
 "S09": ("party", ["pit", "sarah"], True, "The view dips down to the phone in hand for a moment, then back up: Sarah is climbing over the padded wall into the ball pit.", "Ball pit rattle, party din."),
 "S10": ("party", ["pit", "sarah"], False, "The view pushes in on the ball pit. A bigger boy in a pink shirt shoves Sarah off the foam step; she stumbles into the balls.", "A shove, balls clattering, Sarah's startled cry."),
 "S11": ("party", ["party"], True, "One hand flips the phone face down on the table and the view rises fast as we stand up from the bench.", "Sarah crying across the room cuts through the party noise. The bench scrapes."),
 "S12": ("party", ["party", "pit"], True, "Walking fast between the party tables toward the ball pit, tables and balloons sliding past, hands swinging into frame.", "A man's voice: \"Hey. Hey, I'm here.\" Footsteps, party din."),
 "S13": ("party", ["pit", "sarah"], False, "Sarah scrambles out of the ball pit crying and runs into the entrance of the play structure; the view follows her as she disappears inside.", "Sarah sobbing, sneakers on padding, party din."),
 "S14": ("party", ["pit", "tube"], True, "We crouch at the round mouth of a play tube; hands grip its rim. Deep inside, a pair of small cream sneakers vanishes around the bend.", "Hollow plastic echo, a sniffle fading away inside the tube."),
 "S15": ("structure", ["tube"], True, "Crawling forward through a padded play tube, both hands planted on the scuffed padded floor in front, the tube stretching ahead.", "Knees and palms on vinyl, breathing, a man's voice: \"Sarah?\" The party muffled outside."),
 "S16": ("structure", ["tube", "sarah"], True, "A net tunnel; far ahead at the corner, a flash of a blue long-sleeve top whips out of sight. Hands push forward on the net floor.", "Net creaking, distant small footsteps, the party fainter."),
 "S17": ("structure", ["junction"], True, "Inside the junction chamber the view looks left into one tube, right into another, then back to the middle and moves toward one.", "Breathing, plastic creaks, the party barely audible."),
 "S18": ("structure", ["tube"], True, "On the tube floor lies a small yellow plastic star charm. One hand picks it up, holds it close for a moment, and tucks it away.", "A tiny plastic click, breathing."),
 "S19": ("structure", ["tube"], False, "An endless straight tube ahead, the same joints repeating far past where the building should end. Slow push forward.", "Breathing, plastic, the party gone faint and far."),
 "S20": ("structure", ["junction"], False, "The same teal junction chamber again, from another side. The view pushes in on a single faded sticker on the wall, already seen once.", "Near silence, a low hum starting."),
 "S21": ("structure", ["tube"], True, "Padded steps lead down into a warmer, dimmer section; hands on the padded edges as we go down.", "Muffled thumps on padding, the hum growing."),
 "S22": ("structure", ["tube", "slide"], True, "A dark round slide mouth in the wall that was not there before; hands grip its rim and the view peers into the black.", "A man's voice into the dark: \"Sarah?\" It echoes far too long."),
 "S23": ("slide", ["slide", "tube"], True, "We climb into the slide mouth; the floor tips forward and we start to slide, hands grabbing at the tube walls as it drops away.", "Plastic squeal, a sharp breath, the slide roar starting."),
 "S27": ("playways", ["playways"], True, "Underwater-like darkness under the balls: dim colored balls pressed against the view, hands clawing at them, cold blue light leaking between from above.", "Muffled clatter, heartbeat, pressure."),
 "S28": ("playways", ["playways"], True, "The hands break the surface of the ball sea, balls spilling off; the view rises out into the hazy air of the Playways.", "Balls rolling off, a gasp, then silence and a low hum where the party was."),
 "S29": ("playways", ["playways"], False, "From the ball sea the view tilts slowly up the towers of the Playways, up and up into haze, no top in sight.", "A low enormous hum, distant creaks."),
 "S30": ("playways", ["playways"], True, "Wading through the balls to a padded ledge; the hands grab its edge and haul up onto it.", "Balls shifting, heavy breathing, vinyl creak."),
 "S31": ("playways", ["playways", "sarah"], False, "Far off on a net bridge high up stands one small figure in a blue long-sleeve top, back turned, perfectly still.", "A man's voice shouting: \"Sarah!\" It rolls away into the space with no answer."),
 "S32": ("playways", ["playways", "sarah"], False, "The view pans: another small figure in a blue top in a lit window, back turned; another at the top of a slide. All still.", "The hum, distant creaks."),
 "S33": ("playways", ["playways", "sarah"], False, "A fast whip pan across the bridges: dozens of small figures in blue tops on every bridge and catwalk, all with their backs turned, all still.", "Whoosh of the pan, then the hum."),
 "S34": ("playways", ["playways", "idol"], False, "The view tilts up the tiers of the Playways, every tier dotted with small still figures turned away, to the giant grinning mascot idol looking down.", "A deep swelling drone."),
 "S35": ("playways", ["playways"], True, "Looking down at one open hand holding the small yellow plastic star charm.", "The hum, a single breath."),
 "S36": ("playways", ["playways"], False, "A slow tilt up into a tower that never ends, rising into haze and dark; at the very end the frame goes to black.", "The hum swelling, then cut to silence."),
}


def prompt(sid, zone, refs, hands, beats, sound):
    subs = []
    for i, r in enumerate(refs):
        subs.append(f"<Subject {i + 1}> is " + DESC[r].format(n=i + 1))
    if hands:
        subs.append(f"<Subject {len(refs) + 1}> is the viewer's own two hands, invented. " + HANDS)
    who = "Sarah appears exactly as defined." if "sarah" in refs else ""
    crowd = ("The small figures are all the same size and outfit as Sarah and never turn around." if sid in ("S31", "S32", "S33", "S34") else "")
    return "\n".join([
        "subject_definitions:", *subs, "",
        "summary:",
        f"[reference generation] A five-second single continuous first-person shot. {beats.split('.')[0]}.", "",
        "retention_analysis:",
        *[f"<Subject {i + 1}>: fully_preserved." for i in range(len(refs))],
        "No audio reference is used in this generation.", "",
        "detailed_description:",
        f"First-person point of view through the eyes of a tired father, handheld, photographic 35mm film look with 1990s grain and slight halation, {LOOK[zone]}. {who} {crowd}".strip(), "",
        f"[Shot 1] {beats}", "",
        "overall_soundscape:", sound, "",
        "non_diegetic_music:", "None.", "",
        "Avoid: cuts, a third-person view, the viewer's face or body beyond the hands, extra mascots, monsters, cartoon style, readable text, logos.",
    ])


def graph(sid, idx, refs, P, depth, seed):
    start = idx * 124 / 24 + 0.01
    g = {
        "127": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "145": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["127", 0], "lora_name": "pika_h3_flex_ref2va_v1_bf16.safetensors", "strength_model": 1}},
        "173": {"class_type": "ModelPatchLoader", "inputs": {"name": "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors"}},
        "174": {"class_type": "LoadVideo", "inputs": {"file": depth}},
        "705": {"class_type": "Video Slice", "inputs": {"video": ["174", 0], "start_time": round(start, 4), "duration": round(124 / 24, 4), "strict_duration": False}},
        "709": {"class_type": "GetVideoComponents", "inputs": {"video": ["705", 0]}},
        "172": {"class_type": "MiniMaxH3FunControlNetApply", "inputs": {"model": ["145", 0], "model_patch": ["173", 0], "vae": ["119", 0], "strength": 1.0, "start_percent": 0.0, "end_percent": 1.0, "control_video": ["709", 0]}},
        "128": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "119": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "120": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "115": {"class_type": "ResolutionSelector", "inputs": {"aspect_ratio": "9:16 (Portrait Widescreen)", "megapixels": 0.98, "multiple": 32}},
        "136": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"clip": ["128", 0], "vae": ["119", 0], "audio_vae": ["120", 0],
                "prompt": P, "width": ["115", 0], "height": ["115", 1], "length": 124, "ref_image_size": "match"}},
        "126": {"class_type": "BasicGuider", "inputs": {"model": ["172", 0], "conditioning": ["136", 0]}},
        "129": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "123": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "lcm"}},
        "147": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0"}},
        "125": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["129", 0], "guider": ["126", 0], "sampler": ["123", 0], "sigmas": ["147", 0], "latent_image": ["136", 1]}},
        "122": {"class_type": "VAEDecode", "inputs": {"samples": ["125", 0], "vae": ["119", 0]}},
        "121": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["125", 0], "vae": ["120", 0]}},
        "130": {"class_type": "CreateVideo", "inputs": {"images": ["122", 0], "audio": ["121", 0], "fps": 24}},
        "92": {"class_type": "SaveVideo", "inputs": {"video": ["130", 0], "filename_prefix": f"ehih/halloween/batch1/{sid}_h3_s{seed}", "format": "auto", "codec": "auto"}},
    }
    for i, r in enumerate(refs):
        g[str(150 + i)] = {"class_type": "LoadImage", "inputs": {"image": K[r]}}
        g["136"]["inputs"][f"ref_images.ref_image_{i}"] = [str(150 + i), 0]
    return g


if __name__ == "__main__":
    depth, out = sys.argv[1], sys.argv[2]
    items = []
    for sid, (zone, refs, hands, beats, sound) in S.items():
        idx = int(sid[1:]) - 1
        P = prompt(sid, zone, refs, hands, beats, sound)
        seed = 10000 + int(sid[1:]) * 10 + 1
        items.append({"tool": "submit_workflow", "description": f"{sid}_h3_s{seed}", "workflow": graph(sid, idx, refs, P, depth, seed)})
    json.dump(items, open(out, "w"))
    print(len(items), "items")
