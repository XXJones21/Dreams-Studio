"""Seam sheets: per cut, last 5 frames of the outgoing shot | first 5 of the incoming, from the rough assembly."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
SRC = sys.argv[1] if len(sys.argv) > 1 else "../ehih_rough_assembly_v01.mp4"
slots = [(f"S{n:02d}", 120) for n in range(1, 24)] + [("S24-26", 360)] + [(f"S{n:02d}", 120) for n in range(27, 37)]
cuts, t = [], 0
for i in range(len(slots) - 1):
    t += slots[i][1]; cuts.append((slots[i][0], slots[i + 1][0], t))
W, H = 768, 1344; TW, TH = 96, 168
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={TW}:{TH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, TH, TW, 3)
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15); LAB = 70; GAP = 6
os.makedirs("seams", exist_ok=True)
per = 12
for s in range(0, len(cuts), per):
    grp = cuts[s:s + per]
    sheet = Image.new("RGB", (LAB + 10 * TW + GAP, len(grp) * TH), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for r, (a, b, c) in enumerate(grp):
        for j, f in enumerate(range(c - 5, c + 5)):
            x = LAB + j * TW + (GAP if j >= 5 else 0)
            sheet.paste(Image.fromarray(fr[f]), (x, r * TH))
        d.text((4, r * TH + 60), f"{a}\n  >\n{b}", fill="yellow", font=font)
    name = f"seams/seams_{grp[0][0]}_{grp[-1][1]}.jpg"; sheet.save(name, quality=90); print(name, sheet.size)
