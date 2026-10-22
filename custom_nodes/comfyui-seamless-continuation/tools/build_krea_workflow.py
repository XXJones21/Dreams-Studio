"""Add a Krea 2 keyframe stage, a keyframe switch, a model unload, and shared-style prompts to the
user's saved MiniMax continuation workflow.

Input:  ComfyUI/user/default/workflows/minimax_continuation_workflow.json (left untouched)
Output: ComfyUI/user/default/workflows/minimax_continuation_krea_workflow.json
        examples/minimax_continuation_krea_workflow.json (same file, in the repo)
        examples/minimax_continuation_krea_api.json (API format, with override points)

Graph changes:
  [Style] + [Keyframe scene] -> Concatenate -> Krea 2 Turbo -> image
  Switch("Generate keyframe with Krea 2"): on -> Krea image, off -> Load Image (lazy: the unused branch never runs)
  VRAM Debug (KJNodes): unload all models + empty cache, image passthrough -> clip 1 first frame
  [Style] + [Clip N action] -> Concatenate -> clip N prompt

Usage: python tools/build_krea_workflow.py [--server http://127.0.0.1:8189]
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_minimax_workflow as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = Path(r"D:\Tools\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\user\default\workflows")
SOURCE = WORKFLOWS / "minimax_continuation_workflow.json"
TARGET_NAME = "minimax_continuation_krea_workflow.json"

STYLE = ("First-person POV, handheld, the camera is my own eyes, my hands enter the lower frame. "
         "1970s 35mm Kodachrome documentary footage, warm faded colors, soft film grain, gentle halation, "
         "bright natural daylight, deep blue sky with towering cumulus clouds, vast sense of scale, "
         "calm uncanny cosmic dread.")
SCENE = ("I stand at the start of a long, dim 1970s hallway with faded patterned wallpaper. "
         "A closed wooden door waits at the far end. My hands hang at my sides in the lower frame.")
ACTIONS = [
    "I walk slowly down the long hallway toward the closed door at the far end.",
    "I stop in front of the door and reach my hand out toward the brass doorknob.",
    "I turn the doorknob and push the door open. Bright light spills through the gap.",
]
KREA = {"unet": "krea2_turbo_fp8_scaled.safetensors", "clip": "qwen3vl_4b_fp8_scaled.safetensors",
        "vae": "qwen_image_vae.safetensors", "steps": 8, "cfg": 1.0, "sampler": "euler", "scheduler": "simple"}


def new_nodes() -> list[dict]:
    """New nodes in the builder's API-style form: id, class, title, inputs (value or [src_id, slot]), pos, size."""
    n = []

    def add(nid, cls, title, pos, size, **inputs):
        n.append({"id": nid, "class": cls, "title": title, "pos": pos, "size": size, "inputs": inputs})

    # Prompts column, left of the Models group.
    add(2001, "PrimitiveStringMultiline", "Style (shared by every prompt)", [-900, 270], [400, 190], value=STYLE)
    add(2002, "PrimitiveStringMultiline", "Keyframe scene", [-900, 490], [400, 130], value=SCENE)
    for i, action in enumerate(ACTIONS):
        add(2003 + i, "PrimitiveStringMultiline", f"Clip {i + 1} action", [-900, 650 + i * 160], [400, 130],
            value=action)
    for i, src in enumerate([2002, 2003, 2004, 2005]):
        title = "Keyframe prompt" if i == 0 else f"Clip {i} prompt"
        add(2011 + i, "StringConcatenate", title, [-470, 490 + i * 160], [400, 130],
            string_a=[2001, 0], string_b=[src, 0], delimiter=" ")

    # Krea 2 Turbo keyframe, under the Keyframe group.
    add(2101, "UNETLoader", "Krea 2 Turbo fp8", [460, 690], [360, 82], unet_name=KREA["unet"], weight_dtype="default")
    add(2102, "CLIPLoader", "Qwen3-VL 4B (Krea 2)", [460, 800], [360, 106], clip_name=KREA["clip"], type="krea2",
        device="default")
    add(2103, "VAELoader", "Qwen Image VAE", [460, 935], [360, 58], vae_name=KREA["vae"])
    add(2104, "CLIPTextEncode", None, [460, 1020], [360, 90], clip=[2102, 0], text=[2011, 0])
    add(2105, "ConditioningZeroOut", None, [460, 1140], [360, 26], conditioning=[2104, 0])
    add(2106, "EmptyLatentImage", None, [460, 1195], [360, 106], width=base.W, height=base.H, batch_size=1)
    add(2107, "KSampler", "Krea 2 sampler (8 steps)", [460, 1330], [360, 262], model=[2101, 0], positive=[2104, 0],
        negative=[2105, 0], latent_image=[2106, 0], seed=base.SEED, steps=KREA["steps"], cfg=KREA["cfg"],
        sampler_name=KREA["sampler"], scheduler=KREA["scheduler"], denoise=1.0)
    add(2108, "VAEDecode", None, [460, 1620], [360, 46], samples=[2107, 0], vae=[2103, 0])

    # Switch + unload, under the Krea group.
    add(2201, "ComfySwitchNode", "Generate keyframe with Krea 2?", [460, 1760], [360, 78], switch=True,
        on_false=[8, 0], on_true=[2108, 0])
    add(2202, "VRAM_Debug", "Unload models before H3", [460, 1870], [360, 170], empty_cache=True, gc_collect=True,
        unload_all_models=True, image_pass=[2201, 0])
    return n


def _ui_node(spec: dict, object_info: dict, order: int) -> dict:
    """A UI node for one new node; link inputs are filled in later from spec['inputs']."""
    info = object_info[spec["class"]]
    inputs, widgets = [], []
    for name, s in base._spec_inputs(info):
        value = spec["inputs"].get(name)
        if s[0] == "COMFY_MATCHTYPE_V3":
            inputs.append({"name": name, "type": "IMAGE", "link": None})
        elif base._has_widgets(s):
            values = base._widget_values(name, s, {k: v for k, v in spec["inputs"].items() if not isinstance(v, list)})
            if s[0] == "STRING":  # a linked string widget still needs a value; show it empty, not null
                values = ["" if v is None else v for v in values]
            widgets += values
            if s[0] != "COMFY_DYNAMICCOMBO_V3":
                inputs.append({"name": name, "type": "COMBO" if isinstance(s[0], list) else s[0],
                               "widget": {"name": name}, "link": None})
        else:
            inputs.append({"name": name, "type": s[0], "link": None})
    out_types = ["IMAGE" if t == "COMFY_MATCHTYPE_V3" else t for t in info["output"]]
    outputs = [{"name": oname, "type": otype, "links": []}
               for otype, oname in zip(out_types, info.get("output_name", info["output"]))]
    node = {"id": spec["id"], "type": spec["class"], "pos": spec["pos"], "size": spec["size"], "flags": {},
            "order": order, "mode": 0, "inputs": inputs, "outputs": outputs,
            "properties": {"Node name for S&R": spec["class"]}, "widgets_values": widgets}
    if spec["title"]:
        node["title"] = spec["title"]
    return node


def _connect(workflow: dict, nodes: dict, src: list, dst_id: int, dst_input: str) -> None:
    dst = nodes[dst_id]
    slot = next(i for i, inp in enumerate(dst["inputs"]) if inp["name"] == dst_input)
    old = dst["inputs"][slot].get("link")
    if old is not None:  # rewire: drop the old link everywhere
        workflow["links"] = [l for l in workflow["links"] if l[0] != old]
        for n in nodes.values():
            for o in n["outputs"]:
                if old in (o.get("links") or []):
                    o["links"].remove(old)
    workflow["last_link_id"] += 1
    lid = workflow["last_link_id"]
    origin = nodes[src[0]]
    otype = origin["outputs"][src[1]]["type"]
    origin["outputs"][src[1]].setdefault("links", [])
    origin["outputs"][src[1]]["links"] = (origin["outputs"][src[1]]["links"] or []) + [lid]
    dst["inputs"][slot]["link"] = lid
    workflow["links"].append([lid, src[0], src[1], dst_id, slot, otype])


def build_ui(object_info: dict) -> dict:
    workflow = copy.deepcopy(json.loads(SOURCE.read_text(encoding="utf-8")))
    nodes = {n["id"]: n for n in workflow["nodes"]}
    specs = new_nodes()
    for i, spec in enumerate(specs):
        nodes[spec["id"]] = _ui_node(spec, object_info, len(workflow["nodes"]) + i)
        workflow["nodes"].append(nodes[spec["id"]])
    for spec in specs:
        for name, value in spec["inputs"].items():
            if isinstance(value, list):
                _connect(workflow, nodes, value, spec["id"], name)
    # Clip 1 starts on the switched, post-unload keyframe; each clip prompt comes from its Concatenate.
    _connect(workflow, nodes, [2202, 1], 101, "first_frame")
    for clip_node, concat in ((101, 2012), (201, 2013), (301, 2014)):
        _connect(workflow, nodes, [concat, 0], clip_node, "prompt")

    workflow["groups"] += [
        {"id": 7, "title": "Prompts (edit the Style box once; actions per clip)", "bounding": [-920, 210, 870, 950],
         "color": "#b58b2a", "font_size": 24, "flags": {}},
        {"id": 8, "title": "Keyframe: Krea 2 Turbo", "bounding": [440, 650, 400, 1040],
         "color": "#3f789e", "font_size": 24, "flags": {}},
        {"id": 9, "title": "Switch + unload", "bounding": [440, 1720, 400, 340],
         "color": "#a1309b", "font_size": 24, "flags": {}},
    ]
    note = nodes[999]
    note["widgets_values"][0] += (
        "\n\n**Keyframe switch:** on = Krea 2 makes the keyframe from Style + Keyframe scene; off = the Load Image "
        "keyframe is used and Krea never loads.\n**Unload:** VRAM Debug unloads every model after the keyframe, before "
        "H3 starts. It frees VRAM; RAM is freed when ComfyUI's cache needs the space.")
    workflow["last_node_id"] = max(n["id"] for n in workflow["nodes"])
    return workflow


def build_api() -> dict:
    """API format: the original builder's graph plus the new nodes, with override points in _meta."""
    nodes = base.node_list([""] * 3)
    api = base.api_graph(nodes)
    for spec in new_nodes():
        inputs = {k: ([str(v[0]), v[1]] if isinstance(v, list) else v) for k, v in spec["inputs"].items()}
        entry = {"class_type": spec["class"], "inputs": inputs}
        if spec["title"]:
            entry["_meta"] = {"title": spec["title"]}
        api[str(spec["id"])] = entry
    api["101"]["inputs"]["first_frame"] = ["2202", 1]
    for clip_node, concat in (("101", "2012"), ("201", "2013"), ("301", "2014")):
        api[clip_node]["inputs"]["prompt"] = [concat, 0]
    return api


OVERRIDES = {"style": "2001.inputs.value", "scene": "2002.inputs.value", "action_1": "2003.inputs.value",
             "action_2": "2004.inputs.value", "action_3": "2005.inputs.value",
             "use_krea": "2201.inputs.switch", "keyframe_image": "8.inputs.image", "keyframe_seed": "2107.inputs.seed"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8189")
    args = ap.parse_args()
    object_info = json.load(urllib.request.urlopen(f"{args.server}/object_info", timeout=60))

    ui = build_ui(object_info)
    api = build_api()
    text = json.dumps(ui, indent=1)
    (WORKFLOWS / TARGET_NAME).write_text(text, encoding="utf-8")
    (ROOT / "examples" / TARGET_NAME).write_text(text, encoding="utf-8")
    (ROOT / "examples" / "minimax_continuation_krea_api.json").write_text(
        json.dumps({"_overrides": OVERRIDES, "graph": api}, indent=1), encoding="utf-8")

    api_problems = base.validate_api(api, object_info)
    new_ids = {s["id"] for s in new_nodes()}
    ui_problems = [p for p in base.validate_ui(ui, object_info, {s["id"]: {k: v for k, v in s["inputs"].items()
                                                                       if not isinstance(v, list)}
                                                             for s in new_nodes()})
                   if p.startswith("link") or any(p.startswith(f"node {i} ") for i in new_ids)]
    print(f"API graph: {len(api)} nodes, problems: {len(api_problems)}")
    print(f"UI graph: {len(ui['nodes'])} nodes, {len(ui['links'])} links, {len(ui['groups'])} groups, "
          f"problems (new nodes + all links): {len(ui_problems)}")
    for p in api_problems + ui_problems:
        print("  -", p)
    sys.exit(1 if api_problems or ui_problems else 0)


if __name__ == "__main__":
    main()
