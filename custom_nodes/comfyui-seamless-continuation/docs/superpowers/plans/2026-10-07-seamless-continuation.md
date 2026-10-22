# Seamless Continuation Nodes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A ComfyUI V3 node pack with two nodes, Last Frame (Continuation) and Stitch Continuation Clips, that moves last night's manual ffmpeg steps into ComfyUI graphs callable through the Comfy API.

**Architecture:** `ffmpeg_util.py` holds all ffmpeg/ffprobe work (discovery, probe, command building, running) with no torch or ComfyUI imports, so pytest covers it without a GPU. `nodes.py` adapts core `VIDEO` objects to files and calls `ffmpeg_util`. `__init__.py` registers the nodes through `comfy_entrypoint`.

**Tech Stack:** Python 3.12 (ComfyUI venv), ComfyUI core v0.39.0 (`7d9e5a04`) V3 API (`comfy_api.latest`), ffmpeg/ffprobe 8.x on PATH (`C:\ffmpeg\bin`), PyAV 18, pytest, comfy-sdk 0.4.0 for demos.

**Spec:** `docs/superpowers/specs/2026-10-07-seamless-continuation-design.md`

## Global Constraints

- V3 schema only: `io.ComfyNode`, `io.Schema`, `io.NodeOutput`, `ComfyExtension`, `comfy_entrypoint`.
- Node IDs: `SeamlessContinuationLastFrame`, `SeamlessContinuationStitch`. Category: `video/continuation`.
- Never decode a whole file-backed video to float tensors. ffmpeg streams.
- No new runtime dependencies. ffmpeg from PATH, else `imageio_ffmpeg.get_ffmpeg_exe()`, else `FFmpegNotFound`.
- `ffmpeg_util.py` must not import torch, numpy, PIL, or anything from ComfyUI.
- Errors carry their cause: `FFmpegError` includes the last 15 lines of ffmpeg stderr; input errors name the clip (`clip0`, `clip1`, ...).
- Registry metadata: `PublisherId = "XXJones21"`, repository `https://github.com/XXJones21/comfyui-seamless-continuation`. Do not publish or push without explicit approval.
- Commit messages end with:
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01NvJUf6JVfFzszBWEPjoMwC`

## Review Focus

1. Clips with different frame rates or sizes: expect a clear error naming the clip, not an ffmpeg crash. (Task 2 tests.)
2. A clip with no audio track mixed with clips that have audio: expect silence for that span, and an output with audio. (Task 2 test.)
3. `seam_frames` greater than or equal to a clip's frame count: expect a clear error. (Task 2 test.)
4. Autogrow input order: `clip10` must come after `clip9`, not after `clip1`. (Task 3 `_ordered_clips` test.)
5. In-memory videos from core `CreateVideo` (not file-backed): Last Frame must slice in memory without ffmpeg, and Stitch must write them to temp files first. Not exercised by the Task 4 demo, which uses file-backed `LoadVideo`; covered by the code paths in `_as_file` and `LastFrame.execute`, and should be checked with a `CreateVideo` graph if time allows.

## Deferred from the spec

The spec's stretch demo (the whole 15 s sequence in one API job: I2V -> Last Frame -> I2V -> Last Frame -> I2V -> Stitch) has no task here. In one graph, the three decoded clips from core `CreateVideo` stay in RAM (about 4.5 GB at 121 frames, 768x1344) on top of LTX-2.5's ~31 GB, and the LTX run that worked on Oct 6 had only 348 MB free. The nodes support that graph; running it needs more RAM or Comfy Cloud. The README shows it as the intended use.

---

## File Structure

| File | Responsibility |
|---|---|
| `ffmpeg_util.py` | ffmpeg discovery, `run`, `probe` (ffprobe or PyAV), `build_stitch_command`, `stitch_files`, `extract_last_frame` |
| `nodes.py` | `LastFrame`, `Stitch` nodes; `_as_file`, `_ordered_clips`, `_temp_path` helpers |
| `__init__.py` | `SeamlessContinuationExtension`, `comfy_entrypoint` |
| `pyproject.toml`, `LICENSE`, `.gitignore` | Registry metadata, MIT license, ignores |
| `tests/conftest.py`, `tests/test_ffmpeg_util.py`, `tests/test_nodes_helpers.py` | pytest |
| `examples/stitch_api.json`, `demo_stitch.py` | Live API demo |
| `README.md` | User docs |

Test environment: a repo-local venv (`.venv`, git-ignored) with `pytest av numpy`.

---

### Task 1: ffmpeg discovery, runner, and probe

**Files:**
- Create: `ffmpeg_util.py`, `tests/conftest.py`, `tests/test_ffmpeg_util.py`, `.gitignore`

**Interfaces:**
- Produces: `FFmpegNotFound(RuntimeError)`, `FFmpegError(RuntimeError)`, `StitchInputError(ValueError)`, `find_ffmpeg() -> str`, `run(cmd: list[str]) -> None`, `ClipInfo(fps: Fraction, width: int, height: int, frames: int, has_audio: bool, duration: float)`, `probe(path) -> ClipInfo`; test helper `make_clip(path, seconds=1, fps=24, size="64x48", audio=True)` in `tests/conftest.py`.

- [ ] **Step 1: Create the test venv and ignore file**

```bash
cd /d/dev/comfyui-seamless-continuation
python -m venv .venv && ./.venv/Scripts/python -m pip install -q pytest av numpy
printf '.venv/\n__pycache__/\n.pytest_cache/\nexamples/out/\n' > .gitignore
```

- [ ] **Step 2: Write the conftest and failing tests**

`tests/conftest.py`:
```python
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ffmpeg_util  # noqa: E402


def make_clip(path, seconds=1, fps=24, size="64x48", audio=True):
    """Write a tiny H.264 test clip (testsrc pattern, optional 440 Hz tone)."""
    cmd = [ffmpeg_util.find_ffmpeg(), "-y", "-v", "error",
           "-f", "lavfi", "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={seconds}"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd.append(str(path))
    subprocess.run(cmd, check=True)
    return Path(path)
```

`tests/test_ffmpeg_util.py`:
```python
import shutil
import sys
from fractions import Fraction

import pytest

import ffmpeg_util
from conftest import make_clip


def test_probe_reads_clip(tmp_path):
    info = ffmpeg_util.probe(make_clip(tmp_path / "a.mp4"))
    assert info.fps == Fraction(24)
    assert (info.width, info.height) == (64, 48)
    assert info.frames == 24
    assert info.has_audio is True


def test_probe_without_ffprobe_uses_pyav(tmp_path, monkeypatch):
    clip = make_clip(tmp_path / "a.mp4", audio=False)
    real_which = shutil.which
    monkeypatch.setattr(ffmpeg_util.shutil, "which",
                        lambda name: None if name == "ffprobe" else real_which(name))
    info = ffmpeg_util.probe(clip)
    assert info.fps == Fraction(24)
    assert info.frames == 24
    assert info.has_audio is False


def test_run_error_includes_stderr(tmp_path):
    missing = tmp_path / "missing.mp4"
    with pytest.raises(ffmpeg_util.FFmpegError) as exc:
        ffmpeg_util.run([ffmpeg_util.find_ffmpeg(), "-v", "error", "-i", str(missing), str(tmp_path / "o.mp4")])
    assert "missing.mp4" in str(exc.value)


def test_find_ffmpeg_missing_gives_install_hint(monkeypatch):
    monkeypatch.setattr(ffmpeg_util.shutil, "which", lambda name: None)
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)
    with pytest.raises(ffmpeg_util.FFmpegNotFound, match="PATH"):
        ffmpeg_util.find_ffmpeg()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `./.venv/Scripts/python -m pytest tests -q`
Expected: FAIL / error with `ModuleNotFoundError: No module named 'ffmpeg_util'`.

- [ ] **Step 4: Write `ffmpeg_util.py` (discovery, runner, probe)**

```python
"""ffmpeg layer for the Seamless Continuation nodes.

No torch or ComfyUI imports here, so pytest can cover it without a GPU.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


class FFmpegNotFound(RuntimeError):
    """ffmpeg is not on PATH and imageio-ffmpeg is not installed."""


class FFmpegError(RuntimeError):
    """ffmpeg or ffprobe exited with an error. The message carries its stderr."""


class StitchInputError(ValueError):
    """The clips cannot be stitched as given (frame rate, size, or seam length)."""


INSTALL_HINT = (
    "ffmpeg was not found. Install ffmpeg and put it on PATH (https://ffmpeg.org/download.html), "
    "or run `pip install imageio-ffmpeg` in ComfyUI's Python environment."
)


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # ImportError, or imageio-ffmpeg without a binary
        raise FFmpegNotFound(INSTALL_HINT) from exc


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-15:])
        raise FFmpegError(f"{Path(cmd[0]).name} exited with code {proc.returncode}:\n{tail}")


@dataclass(frozen=True)
class ClipInfo:
    fps: Fraction
    width: int
    height: int
    frames: int
    has_audio: bool
    duration: float


def probe(path) -> ClipInfo:
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        return _probe_ffprobe(ffprobe, str(path))
    return _probe_pyav(str(path))


def _probe_ffprobe(ffprobe: str, path: str) -> ClipInfo:
    proc = subprocess.run([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise FFmpegError(f"ffprobe could not read {path}:\n{proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise StitchInputError(f"{path} has no video stream")
    fps = Fraction(video["r_frame_rate"])
    duration = float(video.get("duration") or data["format"]["duration"])
    frames = int(video["nb_frames"]) if video.get("nb_frames") else round(duration * fps)
    has_audio = any(s["codec_type"] == "audio" for s in data["streams"])
    return ClipInfo(fps, int(video["width"]), int(video["height"]), frames, has_audio, duration)


def _probe_pyav(path: str) -> ClipInfo:
    import av  # a ComfyUI dependency; only needed when ffprobe is missing

    with av.open(path) as container:
        if not container.streams.video:
            raise StitchInputError(f"{path} has no video stream")
        stream = container.streams.video[0]
        fps = Fraction(stream.average_rate)
        duration = float(stream.duration * stream.time_base) if stream.duration else container.duration / 1_000_000
        frames = stream.frames or round(duration * fps)
        return ClipInfo(fps, stream.width, stream.height, frames, bool(container.streams.audio), duration)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `./.venv/Scripts/python -m pytest tests -q`
Expected: `4 passed`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore ffmpeg_util.py tests/conftest.py tests/test_ffmpeg_util.py
git commit -m "feat: ffmpeg discovery, runner, and probe"
```

---

### Task 2: Stitch command builder and last-frame extraction

**Files:**
- Modify: `ffmpeg_util.py` (append)
- Modify: `tests/test_ffmpeg_util.py` (append)

**Interfaces:**
- Consumes: `find_ffmpeg`, `run`, `probe`, `ClipInfo`, `StitchInputError` from Task 1.
- Produces: `build_stitch_command(paths: list[str], infos: list[ClipInfo], out: str, seam_frames: int = 1, crf: int = 18, ffmpeg: str = "ffmpeg") -> list[str]`, `stitch_files(paths: list[str], out: str, seam_frames: int = 1, crf: int = 18) -> ClipInfo`, `extract_last_frame(path: str, out_png: str) -> None`.

- [ ] **Step 1: Append the failing tests**

```python
import av
import numpy as np


def _clips(tmp_path, n=3, **kw):
    return [str(make_clip(tmp_path / f"c{i}.mp4", **kw)) for i in range(n)]


def test_stitch_drops_seam_frames(tmp_path):
    out = ffmpeg_util.stitch_files(_clips(tmp_path), str(tmp_path / "out.mp4"), seam_frames=1)
    assert out.frames == 24 * 3 - 2
    assert out.has_audio
    assert abs(out.duration - 70 / 24) < 0.1


def test_stitch_seam_zero_is_plain_concat(tmp_path):
    out = ffmpeg_util.stitch_files(_clips(tmp_path, n=2), str(tmp_path / "out.mp4"), seam_frames=0)
    assert out.frames == 48


def test_stitch_fills_missing_audio_with_silence(tmp_path):
    paths = [str(make_clip(tmp_path / "a.mp4")), str(make_clip(tmp_path / "b.mp4", audio=False))]
    out = ffmpeg_util.stitch_files(paths, str(tmp_path / "out.mp4"))
    assert out.frames == 47
    assert out.has_audio


def test_stitch_without_any_audio_has_no_audio(tmp_path):
    out = ffmpeg_util.stitch_files(_clips(tmp_path, n=2, audio=False), str(tmp_path / "out.mp4"))
    assert out.frames == 47
    assert not out.has_audio


def test_fps_mismatch_names_the_clip(tmp_path):
    paths = [str(make_clip(tmp_path / "a.mp4")), str(make_clip(tmp_path / "b.mp4", fps=30))]
    with pytest.raises(ffmpeg_util.StitchInputError, match="clip1"):
        ffmpeg_util.stitch_files(paths, str(tmp_path / "out.mp4"))


def test_size_mismatch_names_the_clip(tmp_path):
    paths = [str(make_clip(tmp_path / "a.mp4")), str(make_clip(tmp_path / "b.mp4", size="32x24"))]
    with pytest.raises(ffmpeg_util.StitchInputError, match="clip1"):
        ffmpeg_util.stitch_files(paths, str(tmp_path / "out.mp4"))


def test_seam_longer_than_clip_is_rejected(tmp_path):
    with pytest.raises(ffmpeg_util.StitchInputError, match="seam_frames"):
        ffmpeg_util.stitch_files(_clips(tmp_path, n=2), str(tmp_path / "out.mp4"), seam_frames=24)


def test_needs_two_clips(tmp_path):
    with pytest.raises(ffmpeg_util.StitchInputError, match="at least 2"):
        ffmpeg_util.stitch_files(_clips(tmp_path, n=1), str(tmp_path / "out.mp4"))


def _frame_array(path, index=None):
    with av.open(str(path)) as c:
        frames = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
    return frames[-1] if index is None else frames[index]


def test_extract_last_frame_matches_final_frame(tmp_path):
    clip = make_clip(tmp_path / "a.mp4", audio=False)
    png = tmp_path / "last.png"
    ffmpeg_util.extract_last_frame(str(clip), str(png))
    got = _frame_array(png, 0).astype(int)
    want = _frame_array(clip).astype(int)
    first = _frame_array(clip, 0).astype(int)
    assert got.shape == want.shape == (48, 64, 3)
    assert np.abs(got - want).mean() < np.abs(got - first).mean()
```

- [ ] **Step 2: Run the tests to verify the new ones fail**

Run: `./.venv/Scripts/python -m pytest tests -q`
Expected: new tests FAIL with `AttributeError: module 'ffmpeg_util' has no attribute 'stitch_files'` (and `extract_last_frame`).

- [ ] **Step 3: Append the implementation to `ffmpeg_util.py`**

```python
def build_stitch_command(paths: list[str], infos: list[ClipInfo], out: str, seam_frames: int = 1,
                         crf: int = 18, ffmpeg: str = "ffmpeg") -> list[str]:
    """One ffmpeg command that joins clips and drops `seam_frames` from the start of clips 1..n-1.

    Each continuation clip starts on a copy of the previous clip's last frame, so the copy is
    trimmed (video by frame, audio by the same span in seconds). Clips with no audio get silence of
    the right length, so mixed inputs still produce one soundtrack.
    """
    if len(paths) < 2:
        raise StitchInputError(f"Stitch needs at least 2 clips, got {len(paths)}")
    first = infos[0]
    for i, info in enumerate(infos[1:], start=1):
        if info.fps != first.fps:
            raise StitchInputError(f"clip{i} is {float(info.fps):g} fps but clip0 is {float(first.fps):g} fps")
        if (info.width, info.height) != (first.width, first.height):
            raise StitchInputError(
                f"clip{i} is {info.width}x{info.height} but clip0 is {first.width}x{first.height}")
    for i, info in enumerate(infos[1:], start=1):
        if seam_frames >= info.frames:
            raise StitchInputError(f"seam_frames={seam_frames} but clip{i} has only {info.frames} frames")

    any_audio = any(info.has_audio for info in infos)
    cmd = [ffmpeg, "-y", "-v", "error"]
    for path in paths:
        cmd += ["-i", str(path)]
    parts = []
    for i, info in enumerate(infos):
        trim = seam_frames if i > 0 else 0
        v_trim = f"trim=start_frame={trim}," if trim else ""
        parts.append(f"[{i}:v]{v_trim}setpts=PTS-STARTPTS[v{i}]")
        if not any_audio:
            continue
        if info.has_audio:
            a_trim = f"atrim=start={trim / info.fps:.6f}," if trim else ""
            parts.append(f"[{i}:a]{a_trim}asetpts=PTS-STARTPTS,aresample=48000,"
                         f"aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")
        else:
            seconds = (info.frames - trim) / info.fps
            parts.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={seconds:.6f},"
                         f"aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]")
    n = len(infos)
    if any_audio:
        parts.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
        maps = ["-map", "[v]", "-map", "[a]", "-c:a", "aac"]
    else:
        parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]")
        maps = ["-map", "[v]"]
    cmd += ["-filter_complex", ";".join(parts), *maps,
            "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    return cmd


def stitch_files(paths: list[str], out: str, seam_frames: int = 1, crf: int = 18) -> ClipInfo:
    infos = [probe(p) for p in paths]
    run(build_stitch_command(paths, infos, out, seam_frames, crf, ffmpeg=find_ffmpeg()))
    return probe(out)


def extract_last_frame(path: str, out_png: str) -> None:
    """Write the final frame of `path` to `out_png`, decoding only the last half second."""
    run([find_ffmpeg(), "-y", "-v", "error", "-sseof", "-0.5", "-i", str(path),
         "-update", "1", "-q:v", "1", str(out_png)])
    if not Path(out_png).is_file():
        raise FFmpegError(f"ffmpeg wrote no frame for {path}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `./.venv/Scripts/python -m pytest tests -q`
Expected: `13 passed`.

- [ ] **Step 5: Commit**

```bash
git add ffmpeg_util.py tests/test_ffmpeg_util.py
git commit -m "feat: seam-trimming stitch command and last-frame extraction"
```

---

### Task 3: The ComfyUI nodes and registration

**Files:**
- Create: `nodes.py`, `__init__.py`, `pyproject.toml`, `LICENSE`, `tests/test_nodes_helpers.py`

**Interfaces:**
- Consumes: `ffmpeg_util.stitch_files`, `ffmpeg_util.extract_last_frame` (Task 2).
- Produces: node IDs `SeamlessContinuationLastFrame` (in `video: VIDEO`, out `IMAGE`) and `SeamlessContinuationStitch` (in `clips.clip0..clip15: VIDEO`, `seam_frames: INT`, `crf: INT`; out `VIDEO`); helper `_ordered_clips(clips: dict) -> list`.

- [ ] **Step 1: Write the failing helper test**

`tests/test_nodes_helpers.py` (pure Python; it loads only the helper by source, since `nodes.py` imports ComfyUI):
```python
import ast
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "nodes.py").read_text(encoding="utf-8")


def _load(name):
    tree = ast.parse(SRC)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    ns = {"re": __import__("re")}
    exec(compile(ast.Module([fn], []), "nodes.py", "exec"), ns)
    return ns[name]


def test_ordered_clips_sorts_numerically_and_drops_empty():
    ordered = _load("_ordered_clips")
    clips = {"clip10": "k", "clip2": "c", "clip0": "a", "clip1": "b", "clip3": None}
    assert ordered(clips) == ["a", "b", "c", "k"]


def test_ordered_clips_accepts_dotted_keys():
    ordered = _load("_ordered_clips")
    assert ordered({"clips.clip1": "b", "clips.clip0": "a"}) == ["a", "b"]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `./.venv/Scripts/python -m pytest tests/test_nodes_helpers.py -q`
Expected: FAIL with `FileNotFoundError` for `nodes.py`.

- [ ] **Step 3: Write `nodes.py`**

```python
"""Seamless Continuation nodes: last frame out, seam-trimmed stitch in."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

import numpy as np
import torch
from PIL import Image

import folder_paths
from comfy_api.latest import InputImpl, io

from . import ffmpeg_util


def _temp_path(suffix: str) -> Path:
    folder = Path(folder_paths.get_temp_directory()) / "seamless_continuation"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{uuid.uuid4().hex}{suffix}"


def _as_file(video) -> str:
    """Return a file path for `video`, writing it to ComfyUI's temp folder when it is not file-backed."""
    if isinstance(video, InputImpl.VideoFromFile):
        source = video.get_stream_source()
        if isinstance(source, str) and Path(source).is_file() and video.get_active_trim_window() == (0.0, 0.0):
            return source
    out = _temp_path(".mp4")
    video.save_to(str(out))
    return str(out)


def _ordered_clips(clips: dict) -> list:
    """Autogrow values in slot order (clip0, clip1, ..., clip10), skipping empty slots."""
    def slot(key: str) -> int:
        match = re.search(r"(\d+)$", key)
        return int(match.group(1)) if match else 0
    return [clips[k] for k in sorted(clips, key=slot) if clips[k] is not None]


class LastFrame(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeamlessContinuationLastFrame",
            display_name="Last Frame (Continuation)",
            category="video/continuation",
            description="Returns the last frame of a video, to use as the first frame of the next clip.",
            inputs=[io.Video.Input("video", tooltip="The clip to continue from.")],
            outputs=[io.Image.Output(tooltip="The final frame, ready for an image-to-video node.")],
        )

    @classmethod
    def execute(cls, video) -> io.NodeOutput:
        if isinstance(video, InputImpl.VideoFromComponents):
            # Frames are already in memory (for example from core CreateVideo): slice, no ffmpeg.
            return io.NodeOutput(video.get_components().images[-1:].clone())
        png = _temp_path(".png")
        ffmpeg_util.extract_last_frame(_as_file(video), str(png))
        pixels = np.asarray(Image.open(png).convert("RGB"), dtype=np.float32) / 255.0
        return io.NodeOutput(torch.from_numpy(pixels)[None, ...])


class Stitch(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeamlessContinuationStitch",
            display_name="Stitch Continuation Clips",
            category="video/continuation",
            description=("Joins clips in order and drops the repeated seam frame at the start of each "
                         "continuation clip, with matching audio. Runs ffmpeg, so frames are never all held in memory."),
            inputs=[
                io.Autogrow.Input(
                    "clips",
                    template=io.Autogrow.TemplatePrefix(
                        io.Video.Input("clip", tooltip="A clip to append, in order."),
                        prefix="clip", min=2, max=16),
                    tooltip="Clips in playback order. API format keys: clips.clip0, clips.clip1, ...",
                ),
                io.Int.Input("seam_frames", default=1, min=0, max=24,
                             tooltip="Frames dropped from the start of clips 2 and later. 0 joins without trimming."),
                io.Int.Input("crf", default=18, min=0, max=51, advanced=True,
                             tooltip="H.264 quality. Lower is better and larger."),
            ],
            outputs=[io.Video.Output(tooltip="The stitched video (H.264 + AAC).")],
        )

    @classmethod
    def execute(cls, clips: io.Autogrow.Type, seam_frames: int = 1, crf: int = 18) -> io.NodeOutput:
        videos = _ordered_clips(clips)
        paths = [_as_file(v) for v in videos]
        out = _temp_path(".mp4")
        ffmpeg_util.stitch_files(paths, str(out), seam_frames=seam_frames, crf=crf)
        return io.NodeOutput(InputImpl.VideoFromFile(str(out)))
```

- [ ] **Step 4: Write `__init__.py`, `pyproject.toml`, `LICENSE`**

`__init__.py`:
```python
"""ComfyUI entry point for the Seamless Continuation nodes."""
from comfy_api.latest import ComfyExtension, io

from .nodes import LastFrame, Stitch


class SeamlessContinuationExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [LastFrame, Stitch]


async def comfy_entrypoint() -> SeamlessContinuationExtension:
    return SeamlessContinuationExtension()
```

`pyproject.toml`:
```toml
[project]
name = "comfyui-seamless-continuation"
version = "0.1.0"
description = "Chain video clips in ComfyUI: take a clip's last frame for the next generation, then stitch clips with the duplicate seam frame removed (ffmpeg, low memory)."
license = { file = "LICENSE" }
requires-python = ">=3.10"
classifiers = ["Operating System :: OS Independent"]
dependencies = []

[project.urls]
Repository = "https://github.com/XXJones21/comfyui-seamless-continuation"

[tool.comfy]
PublisherId = "XXJones21"
DisplayName = "Seamless Continuation"
requires-comfyui = ">=0.39.0"
```

`LICENSE`: the standard MIT text with `Copyright (c) 2026 Joshua Jones`.

- [ ] **Step 5: Run the helper tests**

Run: `./.venv/Scripts/python -m pytest tests -q`
Expected: `15 passed`.

- [ ] **Step 6: Link into ComfyUI and verify it loads**

```bash
cmd //c mklink //J "D:\Tools\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-seamless-continuation" "D:\dev\comfyui-seamless-continuation"
```
Ask the user to restart their ComfyUI window. Then:
Run: `curl -s http://127.0.0.1:8189/object_info/SeamlessContinuationStitch` and `.../SeamlessContinuationLastFrame`
Expected: both return a schema; the ComfyUI log shows no `IMPORT FAILED` for the pack.

- [ ] **Step 7: Commit**

```bash
git add nodes.py __init__.py pyproject.toml LICENSE tests/test_nodes_helpers.py
git commit -m "feat: Last Frame and Stitch Continuation Clips nodes (V3 schema)"
```

---

### Task 4: Live API demo (stitch the Oct 6 Pillars clips)

**Files:**
- Create: `examples/stitch_api.json`, `demo_stitch.py`

**Interfaces:**
- Consumes: node `SeamlessContinuationStitch` (Task 3), `ffmpeg_util.probe` (Task 1).
- Produces: `examples/out/seamless_stitch_*.mp4`.

- [ ] **Step 1: Write the API-format graph**

`examples/stitch_api.json`:
```json
{
  "1": {"class_type": "LoadVideo", "inputs": {"file": ""}},
  "2": {"class_type": "LoadVideo", "inputs": {"file": ""}},
  "3": {"class_type": "LoadVideo", "inputs": {"file": ""}},
  "10": {"class_type": "SeamlessContinuationStitch",
         "inputs": {"clips.clip0": ["1", 0], "clips.clip1": ["2", 0], "clips.clip2": ["3", 0],
                    "seam_frames": 1, "crf": 18}},
  "20": {"class_type": "SaveVideo",
         "inputs": {"video": ["10", 0], "filename_prefix": "seamless_stitch", "format": "mp4", "codec": "auto"}}
}
```

- [ ] **Step 2: Write `demo_stitch.py`**

```python
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
```

- [ ] **Step 3: Run it against the live server**

Run (from the repo, with the proxy on 8190 and ComfyUI on 8189):
`COMFY_BASE_URL=http://127.0.0.1:8190 /d/dev/comfy-api-test/.venv/Scripts/python demo_stitch.py`
Expected: `succeeded in <30s`, `frames=361`, `audio=True` (121 + 120 + 120, matching `rebuild/seq/pillars_ltx25_15s.mp4`).

- [ ] **Step 4: Commit**

```bash
git add examples/stitch_api.json demo_stitch.py
git commit -m "feat: Comfy API demo that stitches the Oct 6 Pillars clips"
```

---

### Task 5: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`** with these sections, using the real values from Tasks 1-4:
  1. Title and one-line summary.
  2. **Why**: chained image-to-video repeats the previous last frame at each seam; core `ConcatenateVideo` joins "without decoding", so the duplicate stays; this pack does it in-graph with ffmpeg.
  3. **Nodes**: a table per node with inputs, outputs, and behavior (VideoFromComponents slice vs. ffmpeg `-sseof`).
  4. **Install**: `git clone` into `custom_nodes` (or a junction), restart ComfyUI; ffmpeg on PATH or `pip install imageio-ffmpeg`.
  5. **Example graph**: the chain diagram (I2V -> Last Frame -> I2V -> ... -> Stitch -> SaveVideo) and `examples/stitch_api.json`.
  6. **Using it through the Comfy API**: `demo_stitch.py` and the Autogrow note: API-format keys are `clips.clip0`, `clips.clip1`, ...; a bare `"clips"` link passes validation but fails at run time.
  7. **Errors**: the three error types and what each message contains.
  8. **How it works**: the `filter_complex` (trim, atrim, anullsrc, concat) with a 3-clip example.
  9. **Tests**: venv setup and `pytest` command, and what they cover.
  10. **License**: MIT.

- [ ] **Step 2: Check that every command in the README matches the files**

Run: `grep -nE "demo_stitch|stitch_api|pytest|mklink|imageio" README.md`
Expected: each path and command matches a file created in Tasks 1-4.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README for Seamless Continuation"
```

---

### Task 6: MiniMax continuation workflow for the canvas

Added 2026-10-07 at the user's request: the Oct 6 MiniMax-H3 continuation process as a ComfyUI workflow that uses the two new nodes, for viewing and walkthrough.

**Files:**
- Create: `examples/minimax_continuation_api.json` (API format), `examples/minimax_continuation_workflow.json` (UI format, drag onto the canvas), `tools/build_minimax_workflow.py` (writes both from one node list)

**Interfaces:**
- Consumes: node IDs `SeamlessContinuationLastFrame`, `SeamlessContinuationStitch` (Task 3); the H3 graph from `D:\dev\comfy-api-test\rebuild\scene_video_h3_i2v_pruned.json` (models, sampler, 124 frames, 4-step LoRA).
- Produces: one graph: LoadImage (keyframe) -> 3 x [MiniMaxH3ImageToVideo -> sampler -> VAEDecode + VAEDecodeAudio -> CreateVideo], Last Frame between clips, Stitch -> SaveVideo. Model loaders shared by all three clips. Each clip has its own prompt (the three Pillars beats).

- [ ] **Step 1:** Write `tools/build_minimax_workflow.py`: build the API graph, then the UI graph from it using `/object_info` (widget order, input and output slots), with left-to-right positions, groups "Models", "Keyframe", "Clip 1", "Clip 2", "Clip 3", "Stitch", and a note saying the graph is for Comfy Cloud or a machine with more than 32 GB of RAM.
- [ ] **Step 2:** Validate the API graph against `/object_info` (every class exists, every required input present, every model file listed). Expected: 0 problems.
- [ ] **Step 3:** Validate the UI graph's structure: every link id in `links` appears on exactly one output and one input, and every node's widget count matches `/object_info`. Expected: 0 problems.
- [ ] **Step 4:** Commit `examples/minimax_continuation_*.json` and `tools/build_minimax_workflow.py`.
