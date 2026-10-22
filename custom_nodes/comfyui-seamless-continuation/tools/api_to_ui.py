"""Convert comfy-local-mcp workflow files ({_meta, _overrides, graph}) into ComfyUI canvas workflows.

The MCP format wraps an API-format graph, which the ComfyUI canvas cannot load. This writes a UI-format
workflow per file: nodes laid out left to right by dependency depth, nodes the MCP overrides titled after
their override keys, and a note with the description, overrides, and required models.

Usage: python tools/api_to_ui.py OUT_DIR FILE.json [FILE.json ...] [--server http://127.0.0.1:8189]
Exits non-zero if any converted graph fails validation against the server's /object_info.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_minimax_workflow as base  # noqa: E402

COL_W, GAP = 440, 30
TALL = {"KSampler": 262, "KSamplerAdvanced": 300, "CLIPTextEncode": 200, "LoadImage": 320, "SaveImage": 270,
        "LoraLoader": 126, "DualCLIPLoader": 130, "ImageScale": 130, "EmptyLatentImage": 106,
        "EmptySD3LatentImage": 106}


def _depths(graph: dict) -> dict[str, int]:
    depth: dict[str, int] = {}

    def visit(nid: str) -> int:
        if nid not in depth:
            parents = [v[0] for v in graph[nid]["inputs"].values() if isinstance(v, list)]
            depth[nid] = 1 + max((visit(p) for p in parents), default=-1)
        return depth[nid]

    for nid in graph:
        visit(nid)
    return depth


def _titles(overrides: dict) -> dict[str, str]:
    titles: dict[str, list[str]] = {}
    for key, path in overrides.items():
        for p in path if isinstance(path, list) else [path]:
            titles.setdefault(p.split(".")[0], []).append(key)
    return {nid: " / ".join(keys).replace("_", " ") for nid, keys in titles.items()}


def convert(wrapper: dict, object_info: dict) -> dict:
    graph = wrapper.get("graph", wrapper)
    meta, overrides = wrapper.get("_meta", {}), wrapper.get("_overrides", {})
    depth, titles = _depths(graph), _titles(overrides)
    ui_nodes, y_by_col = {}, {}
    for order, nid in enumerate(sorted(graph, key=lambda n: (depth[n], int(n) if n.isdigit() else 0))):
        node = graph[nid]
        info = object_info[node["class_type"]]
        inputs, widgets = [], []
        for name, spec in base._spec_inputs(info):
            value = node["inputs"].get(name)
            if base._has_widgets(spec) and not isinstance(value, list):
                widgets += base._widget_values(name, spec, {k: v for k, v in node["inputs"].items()
                                                            if not isinstance(v, list)})
                if spec[0] != "COMFY_DYNAMICCOMBO_V3":
                    inputs.append({"name": name, "type": "COMBO" if isinstance(spec[0], list) else spec[0],
                                   "widget": {"name": name}, "link": None})
            elif isinstance(value, list) or not base._has_widgets(spec):
                inputs.append({"name": name, "type": spec[0], "link": None, "_src": value})
        col = depth[nid]
        height = TALL.get(node["class_type"], 90)
        y = y_by_col.get(col, 260)
        y_by_col[col] = y + height + GAP
        outputs = [{"name": oname, "type": otype, "links": []}
                   for otype, oname in zip(info["output"], info.get("output_name", info["output"]))]
        ui = {"id": int(nid), "type": node["class_type"], "pos": [col * COL_W, y], "size": [380, height],
              "flags": {}, "order": order, "mode": 0, "inputs": inputs, "outputs": outputs,
              "properties": {"Node name for S&R": node["class_type"]}, "widgets_values": widgets}
        title = titles.get(nid) or node.get("_meta", {}).get("title")
        if title:
            ui["title"] = title
        ui_nodes[nid] = ui

    links, link_id = [], 0
    for nid, ui in ui_nodes.items():
        for slot, inp in enumerate(ui["inputs"]):
            src = inp.pop("_src", None)
            if not isinstance(src, list):
                continue
            link_id += 1
            origin = ui_nodes[str(src[0])]
            inp["link"] = link_id
            origin["outputs"][src[1]]["links"].append(link_id)
            links.append([link_id, int(src[0]), src[1], int(nid), slot, origin["outputs"][src[1]]["type"]])

    lines = [f"## {meta.get('name', 'workflow')}", meta.get("description", "")]
    if overrides:
        lines.append("\n**Override points (comfy-local-mcp):** " + ", ".join(
            f"`{k}` → {v if isinstance(v, str) else ', '.join(v)}" for k, v in overrides.items()))
    if meta.get("required_models"):
        lines.append("\n**Models:** " + ", ".join(f"`{m}`" for m in meta["required_models"]))
    if meta.get("notes"):
        lines.append("\n" + meta["notes"])
    width = (max(depth.values()) + 1) * COL_W - 60
    note_id = max(int(n) for n in graph) + 100
    note = {"id": note_id, "type": "MarkdownNote", "pos": [0, 0], "size": [max(width, 900), 220], "flags": {},
            "order": len(ui_nodes), "mode": 0, "inputs": [], "outputs": [], "properties": {},
            "title": "About this workflow", "widgets_values": ["\n".join(lines)]}
    nodes = list(ui_nodes.values()) + [note]
    return {"id": str(uuid.uuid4()), "revision": 0, "last_node_id": note_id, "last_link_id": link_id,
            "nodes": nodes, "links": links, "groups": [], "config": {},
            "extra": {"ds": {"scale": 0.8, "offset": [40, 40]}}, "version": 0.4}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--server", default="http://127.0.0.1:8189")
    args = ap.parse_args()
    object_info = json.load(urllib.request.urlopen(f"{args.server}/object_info", timeout=60))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = False
    for f in args.files:
        wrapper = json.loads(Path(f).read_text(encoding="utf-8"))
        graph = wrapper.get("graph", wrapper)
        api_problems = base.validate_api(graph, object_info)
        ui = convert(wrapper, object_info)
        values = {int(k): {a: b for a, b in v["inputs"].items() if not isinstance(b, list)} for k, v in graph.items()}
        ui_problems = base.validate_ui(ui, object_info, values)
        (out_dir / Path(f).name).write_text(json.dumps(ui, indent=1), encoding="utf-8")
        print(f"{Path(f).name}: {len(graph)} nodes, {len(ui['links'])} links, "
              f"problems: {len(api_problems) + len(ui_problems)}")
        for p in api_problems + ui_problems:
            print("  -", p)
        failed |= bool(ui_problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
