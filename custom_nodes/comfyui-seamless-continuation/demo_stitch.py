"""Stitch three continuation clips with the Seamless Continuation node through the Comfy API.

Usage (defaults to the Oct 6 Pillars LTX-2.5 clips):
  COMFY_BASE_URL=http://127.0.0.1:8190 python demo_stitch.py [clip1.mp4 clip2.mp4 clip3.mp4]
"""
import json
import sys
import time
from pathlib import Path

from comfy_sdk import Comfy
from comfy_sdk.exceptions import JobFailed

import ffmpeg_util

HERE = Path(__file__).parent
DEFAULT = [Path(r"D:\dev\comfy-api-test\rebuild\seq") / f"pillars_ltx25_clip{i}.mp4" for i in (1, 2, 3)]


def main():
    clips = [Path(p) for p in sys.argv[1:4]] or DEFAULT
    client = Comfy()
    wf = client.workflows.from_json(json.loads((HERE / "examples" / "stitch_api.json").read_text()))
    for node_id, clip in zip(("1", "2", "3"), clips):
        wf.set_input(node_id, "file", client.assets.from_file(clip))
    t0 = time.perf_counter()
    try:
        job = client.submit(wf).result()
    except JobFailed as exc:
        raise SystemExit(f"stitch failed: {exc.error}")
    out_dir = HERE / "examples" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = job.get_outputs("20")[0]
    path = output.to_file(out_dir / output.name)
    info = ffmpeg_util.probe(path)
    print(f"{job.status} in {time.perf_counter() - t0:.1f}s -> {path}")
    print(f"frames={info.frames} duration={info.duration:.2f}s fps={float(info.fps):g} audio={info.has_audio}")


if __name__ == "__main__":
    main()
