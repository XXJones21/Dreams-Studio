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
            # Clamp audio to this clip's video span, then pad to exactly that length. concat starts
            # the next segment where the longer stream ended, so an audio tail past the last video
            # frame would make the constant-frame-rate output repeat frames at the seam.
            start, end = trim / info.fps, info.frames / info.fps
            parts.append(f"[{i}:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS,aresample=48000,"
                         f"aformat=sample_fmts=fltp:channel_layouts=stereo,"
                         f"apad=whole_dur={end - start:.6f}[a{i}]")
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
