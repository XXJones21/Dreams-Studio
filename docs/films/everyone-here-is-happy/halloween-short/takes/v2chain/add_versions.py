"""Add the v2 chain takes to tracker/shots.json as version "v2" (current take, status Review), then build stills.
    python takes/v2chain/add_versions.py S01 S02 ...   (run from the halloween-short folder)"""
import json, os, subprocess, sys
from datetime import datetime

FILM = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VER = "v4" if "--v4" in sys.argv else "v3" if "--v3" in sys.argv else "v2"  # v3 refchain, v4 blockout-locked
V3 = VER != "v2"
OFF = {"v2": 0, "v3": 1, "v4": 2}[VER]
jobs = json.load(open(os.path.join(FILM, "takes", "v2chain", "jobs.json")))
job_of = {}
for j in jobs["jobs"]:
    a, _, b = j["shot"].partition("-")
    lo, hi = int(a[1:]), int((b or a)[1:])
    if (VER if VER != "v2" else "") not in j.get("pass", "") or (VER == "v2" and j.get("pass")):
        continue
    for n in range(lo, hi + 1):
        job_of[f"S{n:02d}"] = j["prompt_id"]
sids = [a for a in sys.argv[1:] if not a.startswith("--")]
sys.path.insert(0, os.path.join(FILM, "tracker"))
import server  # load() / save() keep the history copies and bump rev, same as the page's edits
d = server.load()
now = datetime.now().isoformat(timespec="minutes")
for sid in sids:
    seed = 30000 + int(sid[1:]) * 10 + 1 + OFF
    vid = VER
    path = f"takes/v2chain/{sid}_{vid}_s{seed}.mp4"
    assert os.path.exists(os.path.join(FILM, path)), path
    s = next(x for x in d["shots"] if x["id"] == sid)
    s["versions"] = [v for v in s["versions"] if v["id"] != vid]
    s["versions"].insert(0, {"id": vid, "label": {"v2": "v2 chain", "v3": "v3 refchain", "v4": "v4 blockout"}[VER], "path": path, "cn": "0.5 / 0.5 log depth" if VER == "v4" else "0.35 / 0.35", "seed": seed,
                             "job": job_of.get(sid, ""), "prompt": "chain_h3_v03" + {"v2": "", "v3": " refchain", "v4": " v4"}[VER]})
    s["current"], s["status"] = vid, "rev"
    s.setdefault("notes", []).append({"who": "Claude", "when": now, "text":
        "v4 blockout take: v3 refchain + log-depth control (whole room visible) at 0.5/0.5 + camera/layout paragraph read off the blockout (prompts/framing_from_blockout.json)." if VER == "v4" else
        "v3 refchain take: Pika H3 Flex ref2va with all 9 references, the previous shot's frame 120 pinned at frame 0 (AddGuide), Fun ControlNet 0.35/0.35 on the blockout depth."
        if V3 else "v2 chain take: H3 FL2VA from the previous shot's frame 120 + Fun ControlNet 0.35/0.35 on the new blockout depth."
        if sid != "S01" else "v2 chain take: Pika H3 Flex ref2va (party + sarah) + Fun ControlNet 0.35/0.35 on the new blockout depth; frame 120 starts S02."})
    s["rev"] = s.get("rev", 0) + 1
    print(sid, vid, "added")
server.save(d)
subprocess.run([sys.executable, os.path.join(FILM, "tracker", "media.py")], check=True)
