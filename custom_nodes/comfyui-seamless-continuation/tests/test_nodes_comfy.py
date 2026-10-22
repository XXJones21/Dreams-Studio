"""Node tests that need ComfyUI itself. Skipped in the plain test venv.

Run with ComfyUI's Python:
  COMFYUI_DIR=<path to ComfyUI> <ComfyUI venv python> -m pytest tests/test_nodes_comfy.py -q
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

if os.environ.get("COMFYUI_DIR"):
    sys.path.insert(0, os.environ["COMFYUI_DIR"])
pytest.importorskip("comfy_api.latest")

import ffmpeg_util  # noqa: E402
from conftest import make_clip  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def nodes(tmp_path, monkeypatch):
    import folder_paths

    monkeypatch.setattr(folder_paths, "temp_directory", str(tmp_path / "temp"))
    if "seamless_continuation.nodes" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "seamless_continuation", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["seamless_continuation"] = package
        spec.loader.exec_module(package)
    return sys.modules["seamless_continuation.nodes"]


def _cropped_clip(tmp_path):
    from comfy_api.latest import InputImpl

    clip = make_clip(tmp_path / "a.mp4", audio=False)
    return InputImpl.VideoFromFile(str(clip)).as_cropped(0, 0, 32, 24)


def test_as_file_applies_crop(nodes, tmp_path):
    # Core Crop Video returns VideoFromFile(path, crop=...) with no trim; the source path is the
    # uncropped file, so it must not be passed through as-is (review Important #2).
    info = ffmpeg_util.probe(nodes._as_file(_cropped_clip(tmp_path)))
    assert (info.width, info.height) == (32, 24)


def test_last_frame_of_cropped_video_is_cropped(nodes, tmp_path):
    image = nodes.LastFrame.execute(_cropped_clip(tmp_path)).args[0]
    assert tuple(image.shape) == (1, 24, 32, 3)


def test_last_frame_of_in_memory_video_slices_without_ffmpeg(nodes, tmp_path, monkeypatch):
    import torch
    from comfy_api.latest import InputImpl, VideoComponents
    from fractions import Fraction

    frames = torch.rand(5, 24, 32, 3)
    video = InputImpl.VideoFromComponents(VideoComponents(images=frames, frame_rate=Fraction(24)))
    monkeypatch.setattr(ffmpeg_util, "find_ffmpeg", lambda: pytest.fail("ffmpeg must not run"))
    image = nodes.LastFrame.execute(video).args[0]
    assert torch.equal(image, frames[-1:])
