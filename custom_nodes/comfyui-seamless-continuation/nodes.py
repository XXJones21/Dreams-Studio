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
            # A cropped VideoFromFile (core Crop Video) still points at the uncropped file. Pass the
            # file through only when its real size matches the size the video reports.
            info = ffmpeg_util.probe(source)
            if (info.width, info.height) == tuple(video.get_dimensions()):
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
