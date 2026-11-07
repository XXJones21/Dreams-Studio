"""Join the v2 chain takes (frames 0-119 of each, with audio) into one clip, plus a side-by-side with the blockout.
    python takes/v2chain/assemble.py S01 S12"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = "D:/Comfy/blockout-previs-demo/halloween-playways/animatic/ehih_halloween_animatic.mp4"
a, b = int(sys.argv[1][1:]), int(sys.argv[2][1:])
ids = [f"S{n:02d}" for n in range(a, b + 1)]
def take(s):  # newest pass first: v4 (seed + 2), v3 (seed + 1), else the v2 chain take
    seed = 30000 + int(s[1:]) * 10 + 1
    for tag, off in (("v4", 2), ("v3", 1)):
        f = os.path.join(HERE, f"{s}_{tag}_s{seed + off}.mp4")
        if os.path.exists(f):
            return f
    return os.path.join(HERE, f"{s}_v2_s{seed}.mp4")
files = [take(s) for s in ids]
print(*[os.path.basename(f) for f in files])
ins, parts = [], []
for k, f in enumerate(files):
    ins += ["-i", f]
    parts.append(f"[{k}:v]trim=end_frame=120,setpts=PTS-STARTPTS[v{k}];[{k}:a]atrim=end=5,asetpts=PTS-STARTPTS[a{k}]")
cat = "".join(f"[v{k}][a{k}]" for k in range(len(files))) + f"concat=n={len(files)}:v=1:a=1[v][a]"
out = os.path.join(HERE, f"cut_{ids[0]}_{ids[-1]}.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(parts) + ";" + cat, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-movflags", "+faststart", out], check=True)
# side by side: blockout (left) | v2 chain (right), 540 px tall each half
f0, f1 = (a - 1) * 120, b * 120
sbs = os.path.join(HERE, f"cut_{ids[0]}_{ids[-1]}_vs_blockout.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", BLOCK, "-i", out, "-filter_complex",
                f"[0:v]trim=start_frame={f0}:end_frame={f1},setpts=PTS-STARTPTS,scale=-2:960[l];[1:v]scale=-2:960[r];[l][r]hstack[v]",
                "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "22", "-preset", "fast", "-c:a", "aac", "-movflags", "+faststart", sbs], check=True)
print(out); print(sbs)
