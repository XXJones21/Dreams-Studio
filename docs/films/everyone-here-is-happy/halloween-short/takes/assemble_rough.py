"""Rough assembly: batch1 takes in shot order, S24-26 continuous bridged take, clay animatic where a take is missing.
    python assemble_rough.py [out.mp4]
Each 124-frame take is trimmed to its first 120 frames (the depth slice was padded at the tail).
"""
import os, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.join(HERE, "batch1")
CONT = os.path.join(HERE, "S24_26", "h3_cont_s24272_bridged.mp4")
CLAY = "D:/Comfy/blockout-previs-demo/halloween-playways/animatic/ehih_halloween_animatic.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ehih_rough_assembly_v01.mp4")
WORK = os.path.join(HERE, "_rough_work")
os.makedirs(WORK, exist_ok=True)
FONT = "C\\:/Windows/Fonts/arial.ttf"
VF = "scale=768:1344,fps=24,format=yuv420p"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


def seg(src, out, start_frame, nframes, label=None):
    vf = VF + f",trim=start_frame={start_frame}:end_frame={start_frame + nframes},setpts=PTS-STARTPTS"
    if label:
        vf += f",drawtext=fontfile='{FONT}':text='{label}':x=24:y=24:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8"
    dur = nframes / 24
    cmd = ["ffmpeg", "-y", "-i", src]
    if has_audio(src):
        af = f"atrim=start={start_frame / 24}:duration={dur},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo"
        cmd += ["-vf", vf, "-af", af, "-map", "0:v:0", "-map", "0:a:0"]
    else:
        cmd += ["-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-frames:v", str(nframes), "-t", str(dur), "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", out]
    run(cmd)


parts, report = [], []
n = 1
while n <= 36:
    sid = f"S{n:02d}"
    out = os.path.join(WORK, f"{sid}.mp4")
    if n == 24:
        if os.path.exists(CONT):
            seg(CONT, out, 0, 360); report.append("S24-26 continuous bridged take")
        else:
            seg(CLAY, out, 23 * 120, 360, "S24-26 CLAY"); report.append("S24-26 CLAY")
        parts.append(out); n = 27; continue
    takes = sorted(glob.glob(os.path.join(B1, f"{sid}_h3_*.mp4")))
    if takes:
        seg(takes[-1], out, 0, 120); report.append(f"{sid} {os.path.basename(takes[-1])}")
    else:
        seg(CLAY, out, (n - 1) * 120, 120, f"{sid} CLAY"); report.append(f"{sid} CLAY")
    parts.append(out); n += 1

lst = os.path.join(WORK, "list.txt")
with open(lst, "w") as f:
    for p in parts:
        f.write(f"file '{p.replace(os.sep, '/')}'\n")
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT])
web = OUT.replace(".mp4", "_web.mp4")
run(["ffmpeg", "-y", "-i", OUT, "-vf", "scale=540:-2", "-c:v", "libx264", "-crf", "26", "-preset", "fast", "-c:a", "aac", "-b:a", "128k",
     "-movflags", "+faststart", web])
print("\n".join(report))
print("wrote", OUT, "and", web)
