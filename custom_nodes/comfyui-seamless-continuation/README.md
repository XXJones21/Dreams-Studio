# Seamless Continuation

Two ComfyUI nodes for chained video generation. **Last Frame** takes the final frame of a clip so the next image-to-video job can start from it. **Stitch Continuation Clips** joins the clips and removes the duplicate frame at each seam, with matching audio. Both nodes use the V3 node schema, and Stitch runs ffmpeg so the frames never all sit in memory.

## Why

Image-to-video models generate about 5 seconds per job. For a longer shot, you chain jobs: each new clip starts on the last frame of the previous clip. That makes every seam show the same frame twice, which reads as a one-frame stall.

Core ComfyUI has `Concatenate Video`, but it joins clips "without decoding", so the duplicate frames stay. Before this pack, the fix was a manual ffmpeg command outside ComfyUI. These two nodes move both steps into the graph, so a whole sequence can run through the Comfy API.

## Nodes

### Last Frame (Continuation)

| | |
|---|---|
| Node ID | `SeamlessContinuationLastFrame` |
| Category | `video/continuation` |
| Input | `video` (VIDEO): the clip to continue from |
| Output | `IMAGE`: the final frame, one image |

If the video is already in memory as frames (for example from core `Create Video`), the node slices the last frame directly. If the video comes from a file (for example `Load Video`), the node runs `ffmpeg -sseof -0.5`, which decodes only the last half second.

### Stitch Continuation Clips

| | |
|---|---|
| Node ID | `SeamlessContinuationStitch` |
| Category | `video/continuation` |
| Inputs | `clips` (2 to 16 VIDEO inputs, added as you connect them), `seam_frames` (INT, default 1), `crf` (INT, default 18, advanced) |
| Output | `VIDEO`: H.264 video with AAC audio |

`seam_frames` is the number of frames dropped from the start of clips 2 and later. Use 1 for a standard last-frame chain. Use 0 to join clips without trimming. The same span of audio is dropped, so sound stays in sync. A clip with no audio gets silence of the right length, so you can mix clips with and without sound.

## Install

1. Clone the repo into ComfyUI's `custom_nodes` folder:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/XXJones21/comfyui-seamless-continuation
   ```
   On Windows, you can instead link a working copy with a junction:
   ```bat
   mklink /J ComfyUI\custom_nodes\comfyui-seamless-continuation D:\dev\comfyui-seamless-continuation
   ```
2. Make sure ffmpeg is available. The nodes use `ffmpeg` from PATH first. If it is not there, they use the binary from `imageio-ffmpeg`:
   ```bash
   pip install imageio-ffmpeg   # in ComfyUI's Python environment
   ```
3. Restart ComfyUI. The nodes appear under **video/continuation**.

The pack has no Python dependencies beyond what ComfyUI already installs. It needs ComfyUI 0.39.0 or later (V3 schema with `Autogrow` inputs).

## Example: a 15-second chain

```
keyframe ─► image-to-video ─► Last Frame ─► image-to-video ─► Last Frame ─► image-to-video
                   │                               │                               │
                   └──────────────────► Stitch Continuation Clips ◄────────────────┘ ─► Save Video
```

`examples/minimax_continuation_workflow.json` is this chain with MiniMax-H3: drag it onto the ComfyUI canvas to see it. Run as one job, it keeps three decoded clips in memory next to the video model, so it needs more than 32 GB of RAM or Comfy Cloud. On a smaller machine, run each clip as its own job and stitch at the end, as in the next section.

## Use it through the Comfy API

`examples/stitch_api.json` loads three clips and stitches them. `demo_stitch.py` uploads the clips with the Comfy Python SDK and runs the graph:

```bash
COMFY_BASE_URL=http://127.0.0.1:8190 python demo_stitch.py clip1.mp4 clip2.mp4 clip3.mp4
```

Measured on three 121-frame LTX-2.5 clips: the job took 2.6 seconds and returned 361 frames (121 + 120 + 120), 15.04 seconds at 24 fps, with audio.

**API format for `clips`:** `clips` is an `Autogrow` input. In an API-format graph, each slot is its own key, joined with a dot:

```json
"inputs": {"clips.clip0": ["1", 0], "clips.clip1": ["2", 0], "clips.clip2": ["3", 0], "seam_frames": 1}
```

A link to a bare `"clips"` key passes validation but fails when the node runs. Use the dotted keys.

## Errors

Each error says what went wrong and where:

| Error | When | The message contains |
|---|---|---|
| `FFmpegNotFound` | ffmpeg is not on PATH and `imageio-ffmpeg` is not installed | How to install ffmpeg |
| `StitchInputError` | Fewer than 2 clips, a frame rate or size that does not match `clip0`, or `seam_frames` longer than a clip | The clip name, for example `clip1 is 30 fps but clip0 is 24 fps` |
| `FFmpegError` | ffmpeg or ffprobe exits with an error | The last 15 lines of ffmpeg's own error output |

## How it works

Stitch writes any in-memory clip to ComfyUI's temp folder, reads each clip's frame rate, size, and audio with `ffprobe` (or PyAV when ffprobe is missing), and then runs one ffmpeg command. For three clips with audio and `seam_frames=1`, the filter graph is:

```
[0:v]setpts=PTS-STARTPTS[v0];
[0:a]atrim=start=0.000000:end=5.041667,asetpts=PTS-STARTPTS,aresample=48000,aformat=...,apad=whole_dur=5.041667[a0];
[1:v]trim=start_frame=1,setpts=PTS-STARTPTS[v1];
[1:a]atrim=start=0.041667:end=5.041667,asetpts=PTS-STARTPTS,aresample=48000,aformat=...,apad=whole_dur=5.000000[a1];
[2:v]trim=start_frame=1,setpts=PTS-STARTPTS[v2];
[2:a]atrim=start=0.041667:end=5.041667,asetpts=PTS-STARTPTS,aresample=48000,aformat=...,apad=whole_dur=5.000000[a2];
[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]
```

Each clip's audio is cut to its own video span and padded to exactly that length (`atrim ... :end=`, `apad=whole_dur=`). Without this, an audio tail that runs past the last video frame (normal for AAC, NTSC frame rates, and many MKV files) makes `concat` hold the picture, and the seam stall comes back.

ffmpeg streams the frames, so memory use stays flat no matter how long the clips are.

## Tests

The ffmpeg layer (`ffmpeg_util.py`) has no ComfyUI imports, so it tests without a GPU:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install pytest av numpy    # .venv/bin/python on macOS and Linux
.venv/Scripts/python -m pytest tests -q
```

The tests build tiny clips with ffmpeg's `testsrc` and check: frame counts after seam trimming, plain joins, mixed audio and silent clips, clips with no audio, frame rate and size mismatches, seam length limits, the last-frame image, error messages that include ffmpeg's output, and the missing-ffmpeg message.

Node-level tests (cropped videos, in-memory videos) need ComfyUI itself. They skip in the plain venv; run them with ComfyUI's Python:

```bash
COMFYUI_DIR=/path/to/ComfyUI /path/to/ComfyUI/venv/python -m pytest tests/test_nodes_comfy.py -q
```

## License

MIT
