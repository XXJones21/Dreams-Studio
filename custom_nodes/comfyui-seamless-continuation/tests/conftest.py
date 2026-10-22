import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ffmpeg_util  # noqa: E402


def make_clip(path, seconds=1, fps=24, size="64x48", audio=True, audio_seconds=None):
    """Write a tiny H.264 test clip (testsrc pattern, optional 440 Hz tone).

    `audio_seconds` longer than `seconds` keeps an audio tail past the last video frame.
    """
    cmd = [ffmpeg_util.find_ffmpeg(), "-y", "-v", "error",
           "-f", "lavfi", "-i", f"testsrc=size={size}:rate={fps}:duration={seconds}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={audio_seconds or seconds}"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", "aac"] + ([] if audio_seconds else ["-shortest"])
    cmd.append(str(path))
    subprocess.run(cmd, check=True)
    return Path(path)
