# Seamless Continuation nodes: design

Date: 2026-10-07. Status: approved in conversation.

## Goal

A small ComfyUI V3 custom node pack that makes chained video generation a pure ComfyUI graph. It
replaces the manual ffmpeg steps from the Oct 6 Comfy API test (tab 4 of the test notes): pulling
the last frame of a clip to seed the next clip, and stitching clips while dropping the duplicated
seam frame. It is the walkthrough piece for the 2026-10-07 5 PM hiring-manager interview.

Success means:
- Both nodes load in the local ComfyUI (core v0.39.0 at `7d9e5a04`) with no import errors.
- The stitch graph, run through the Comfy API v2 (comfy-sdk 0.4.0 -> comfy-api-proxy :8190 ->
  ComfyUI :8189), turns the three Oct 6 Pillars LTX-2.5 clips (121 frames each) into one video of
  361 frames, matching `rebuild/seq/pillars_ltx25_15s.mp4`.
- pytest passes for the ffmpeg layer without a GPU.
- A README explains the problem, the nodes, install, an example, and the Autogrow API-format key.

## Constraints

- V3 schema (`comfy_api.latest`: `io.ComfyNode`, `io.Schema`, `io.NodeOutput`, `ComfyExtension`,
  `comfy_entrypoint`).
- Memory: 16 GB VRAM / 32 GB RAM. Never decode whole videos to float tensors; ffmpeg streams.
- No new Python dependencies. ffmpeg comes from PATH, else `imageio_ffmpeg.get_ffmpeg_exe()`
  (already in the ComfyUI venv), else a clear error.
- Nothing is published to the Comfy Registry or pushed anywhere without explicit approval.

## Nodes

### SeamlessContinuationLastFrame ("Last Frame (Continuation)")
- Input: `video` (VIDEO). Output: `image` (IMAGE, shape 1 x H x W x 3, float 0..1).
- If `video.get_stream_source()` is a file path: run ffmpeg with `-sseof -0.5 ... -update 1` to a
  temp PNG and load it. Otherwise (in-memory, for example from core `CreateVideo`): take
  `video.get_components().images[-1:]`.
- Category `video/continuation`.

### SeamlessContinuationStitch ("Stitch Continuation Clips")
- Inputs:
  - `clips`: `io.Autogrow.Input` of `io.Video.Input`, `TemplatePrefix(prefix="clip", min=2, max=16)`.
    API-format keys are `clips.clip0`, `clips.clip1`, ...
  - `seam_frames`: INT, default 1, min 0, max 24. Frames dropped from the start of clips 2..n.
  - `crf`: INT, default 18, min 0, max 51, advanced.
- Output: `video` (VIDEO) = `VideoFromFile(<temp mp4>)`.
- Steps: materialize each clip as a file (`get_stream_source()` path, or `save_to(temp)`); probe
  frame rate, size, and audio presence with ffprobe; reject mismatched frame rates or sizes with an
  error that names the clip; build one `filter_complex`: for clip i > 0, `trim=start_frame=N`,
  `setpts=PTS-STARTPTS`, and `atrim=start=N/fps`, `asetpts=PTS-STARTPTS`; clips without audio get
  `anullsrc` of matching length; `concat=n=k:v=1:a=1`; encode libx264 `-crf`, yuv420p, AAC.

## ffmpeg layer (`ffmpeg_util.py`, no torch/ComfyUI imports)
- `find_ffmpeg()`: PATH first, then `imageio_ffmpeg.get_ffmpeg_exe()`, else raise
  `FFmpegNotFound` with install instructions.
- `probe()` uses `ffprobe` from PATH when present; otherwise PyAV (`av`, already a ComfyUI
  dependency). imageio-ffmpeg ships no ffprobe.
- `probe(path) -> ClipInfo(fps: Fraction, width, height, frames, has_audio, duration)`.
- `build_stitch_command(infos, paths, out, seam_frames, crf) -> list[str]` (pure, unit-tested).
- `run(cmd)`: subprocess; on failure raise `FFmpegError` whose message includes the last 15 lines
  of stderr. This is the `JobFailed` lesson: errors must carry their cause.
- `extract_last_frame(path, out_png)`.

## Files
```
comfyui-seamless-continuation/
  __init__.py          # comfy_entrypoint -> SeamlessContinuationExtension
  nodes.py             # the two nodes
  ffmpeg_util.py       # ffmpeg/ffprobe discovery, probe, command builder, runner
  pyproject.toml       # Comfy Registry metadata ([tool.comfy]), no dependencies
  README.md
  examples/stitch_api.json, examples/sequence_api.json   # API-format graphs
  demo_stitch.py, demo_sequence.py                       # SDK scripts
  tests/test_ffmpeg_util.py
```
Linked into ComfyUI with a directory junction:
`custom_nodes/comfyui-seamless-continuation -> D:\dev\comfyui-seamless-continuation`.

## Demos
1. Stitch (live, seconds, no GPU): upload the three clips as assets -> 3 x `LoadVideo` ->
   Stitch -> `SaveVideo`. Expect 361 frames.
2. Sequence (stretch, ~10 min, run once before the call): uploaded Pillars keyframe -> LTX-2.5
   I2V (graph from `scene_video_ltx25.json`) -> Last Frame -> I2V -> Last Frame -> I2V -> Stitch ->
   `SaveVideo`, one API job. LTX only, no Krea in the same job (RAM).

## Testing
- pytest with synthetic clips from `ffmpeg -f lavfi testsrc` (24 fps, 1 s, 64x48), with and
  without a `sine` audio track: frame count after trimming, durations, audio-less input, fps
  mismatch error, missing-ffmpeg error, stderr included in `FFmpegError`.
- Live: ComfyUI import log shows the pack loaded; the stitch demo returns 361 frames.

## Out of scope
Crossfades, frame interpolation at seams, Registry publishing, non-H.264 outputs.
