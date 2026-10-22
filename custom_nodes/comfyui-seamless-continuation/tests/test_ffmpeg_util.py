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


def test_audio_tail_longer_than_video_adds_no_frames(tmp_path):
    # concat starts each segment where the longer stream ended; a late audio tail made the
    # constant-frame-rate output repeat video frames at the seam (review Important #1).
    paths = [str(make_clip(tmp_path / f"t{i}.mp4", audio_seconds=1.5)) for i in range(2)]
    out = ffmpeg_util.stitch_files(paths, str(tmp_path / "out.mp4"))
    assert out.frames == 24 + 24 - 1


def test_ntsc_clips_with_audio_keep_exact_frame_count(tmp_path):
    paths = [str(make_clip(tmp_path / f"n{i}.mp4", fps="24000/1001")) for i in range(3)]
    frames = [ffmpeg_util.probe(p).frames for p in paths]
    out = ffmpeg_util.stitch_files(paths, str(tmp_path / "out.mp4"))
    assert out.frames == sum(frames) - 2
