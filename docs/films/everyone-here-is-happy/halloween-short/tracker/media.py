"""Build tracker media from shots.json: a blockout clip per shot (cut from the clay animatic) and
first / mid / last stills for every version, blockout first / last frames per shot (the FLF keyframe
targets), and thumbnails of the reference pictures. Skips files that already exist; run after adding a version.

    python tracker/media.py [--force]
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, "shots.json"), encoding="utf-8"))
FORCE = "--force" in sys.argv
os.makedirs(os.path.join(HERE, "media", "blockout"), exist_ok=True)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def nframes(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", p], capture_output=True, text=True)
    return int(r.stdout.strip())


made = 0
for s in D["shots"]:
    a, b = s["frames"]
    clip = os.path.join(HERE, "media", "blockout", f"{s['id']}.mp4")
    if FORCE or not os.path.exists(clip):
        n = b - a + 1
        run(["ffmpeg", "-y", "-i", D["blockout"], "-vf",
             f"trim=start_frame={a - 1}:end_frame={b},setpts=PTS-STARTPTS,scale=432:-2", "-an",
             "-frames:v", str(n), "-c:v", "libx264", "-crf", "26", "-preset", "fast", "-movflags", "+faststart", clip])
        made += 1
    sdir = os.path.join(HERE, "media", "stills", s["id"])
    os.makedirs(sdir, exist_ok=True)
    for v in s["versions"]:
        src = os.path.join(FILM, v["path"])
        if not os.path.exists(src):
            print("missing", v["path"]); continue
        # the cut uses the first 120 frames of a 124-frame take
        last = b - a
        if not os.path.exists(os.path.join(sdir, f"{v['id']}_last.jpg")):
            last = min(last, nframes(src) - 1)
        for tag, f in (("first", 0), ("mid", last // 2), ("last", last)):
            out = os.path.join(sdir, f"{v['id']}_{tag}.jpg")
            if FORCE or not os.path.exists(out):
                run(["ffmpeg", "-y", "-i", src, "-vf", f"select=eq(n\\,{f}),scale=384:-2", "-frames:v", "1",
                     "-fps_mode", "vfr", "-q:v", "3", out])
                made += 1
    # blockout first / last frame of this shot (what the FLF keyframes have to match)
    bdir = os.path.join(HERE, "media", "blockout_stills")
    os.makedirs(bdir, exist_ok=True)
    for tag, f in (("first", a - 1), ("last", b - 1)):
        out = os.path.join(bdir, f"{s['id']}_{tag}.jpg")
        if FORCE or not os.path.exists(out):
            run(["ffmpeg", "-y", "-i", D["blockout"], "-vf", f"select=eq(n\\,{f}),scale=540:-2", "-frames:v", "1",
                 "-fps_mode", "vfr", "-q:v", "3", out])
            made += 1

# reference pictures: <name>.jpg thumbnail and <name>_full.jpg for the click-through
REFS = {
    "party": "gate1/partykey_s101.png",
    "mascot": "gate1/mascot_party_s102.png",
    "pit": "gate1/pitkey_s103.png",
    "tube": "gate1/structkey_tube_s104.png",
    "junction": "gate1/structkey_junction_s105.png",
    "sarah": "gate1/sarah_turnaround_s10403.png",
    "slide": "refs/slide-key-LOCKED.png",
    "playways": "refs/playways-setkey-v3-LOCKED.png",
    "idol": r"D:/Tools/Valinor/Engram/Projects/everyone-here-is-happy/renders/23_manager_mascot_idol.png",
}
rdir = os.path.join(HERE, "media", "refs")
os.makedirs(rdir, exist_ok=True)
for name, src in REFS.items():
    src = src if os.path.isabs(src) else os.path.join(FILM, src)
    if not os.path.exists(src):
        print("missing ref", name, src); continue
    for suffix, w in (("", 320), ("_full", 1600)):
        out = os.path.join(rdir, f"{name}{suffix}.jpg")
        if FORCE or not os.path.exists(out):
            run(["ffmpeg", "-y", "-i", src, "-vf", f"scale='min({w},iw)':-2", "-frames:v", "1", "-q:v", "3", out])
            made += 1
print("made", made, "files")
