"""Boundary keyframes for the FLF chain. K_n = frame at the cut between shot n and n+1.
K0 = S01 frame 0; K_n (n=1..22) = S(n+1) frame 0; K23 = S24_26 bridged frame 0; K26 = bridged last frame;
K27..K35 = S(n+1) frame 0; K36 = S36 last frame."""
import glob, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(HERE)
B1 = os.path.join(T, "batch1"); CONT = os.path.join(T, "S24_26", "h3_cont_s24272_bridged.mp4")
OUT = os.path.join(HERE, "keys")
def take(n): return sorted(glob.glob(os.path.join(B1, f"S{n:02d}_h3_*.mp4")))[-1]
def grab(src, frame, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "select=eq(n\\,%d)" % frame, "-frames:v", "1", "-fps_mode", "vfr", dst], check=True)
def last(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", src], capture_output=True, text=True)
    return int(r.stdout.strip()) - 1
keys = {0: (take(1), 0)}
for n in range(1, 23): keys[n] = (take(n + 1), 0)
keys[23] = (CONT, 0); keys[26] = (CONT, last(CONT))
for n in range(27, 36): keys[n] = (take(n + 1), 0)
keys[36] = (take(36), last(take(36)))
for n, (src, f) in keys.items():
    grab(src, f, os.path.join(OUT, f"K{n:02d}.png")); print(f"K{n:02d} <- {os.path.basename(src)} f{f}")
