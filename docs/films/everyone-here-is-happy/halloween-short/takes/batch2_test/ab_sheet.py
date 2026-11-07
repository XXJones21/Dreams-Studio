"""A/B sheet: for each shot, rows = batch1 take, v2a, v2b; 6 frames each (0, 24, 48, 72, 96, 119)."""
import glob, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); B1 = os.path.join(os.path.dirname(HERE), "batch1")
FR = [0, 24, 48, 72, 96, 119]; TW, TH = 120, 210
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
def frames(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", f"scale={TW}:{TH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, TH, TW, 3); return [a[min(f, len(a) - 1)] for f in FR]
for sid in ["S02", "S10", "S16", "S30"]:
    rows = [("v1 (CN 1.0)", sorted(glob.glob(f"{B1}/{sid}_h3_*.mp4")))] + [(f"v2{t}", sorted(glob.glob(f"{HERE}/{sid}_h3v2{t}_*.mp4"))) for t in "ab"]
    rows = [(l, p[-1]) for l, p in rows if p]
    sheet = Image.new("RGB", (90 + TW * 6, TH * len(rows)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for r, (lab, p) in enumerate(rows):
        for j, im in enumerate(frames(p)): sheet.paste(Image.fromarray(im), (90 + j * TW, r * TH))
        d.text((4, r * TH + 90), f"{sid}\n{lab}", fill="yellow", font=font)
    sheet.save(f"{HERE}/_ab_{sid}.jpg", quality=88); print("wrote", sid, len(rows), "rows")
