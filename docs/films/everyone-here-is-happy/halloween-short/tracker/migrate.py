"""One-time seed of tracker/shots.json from the shot table, the v02 prompt builder, the takes on disk,
the seam notes and the v02 test. After this, shots.json is the source of truth: the tracker page and
prompts/batch_h3_v02.py both read it.

    python tracker/migrate.py            # refuses to overwrite an existing shots.json
    python tracker/migrate.py --force
"""
import glob, json, os, re, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
OUT = os.path.join(HERE, "shots.json")
sys.path.insert(0, "D:/Comfy/blockout-previs-demo/halloween-playways/scripts")
sys.path.insert(0, os.path.join(FILM, "prompts"))
from shots import SHOTS  # noqa: E402

os.environ["EHIH_NO_TRACKER"] = "1"  # read the builder's built-in table, not a tracker that doesn't exist yet
import batch_h3_v02 as B  # noqa: E402

NOW = datetime(2026, 11, 1, 2, 0).isoformat(timespec="minutes")
TABLE = {s[0]: dict(set=s[1], beat=s[2], camera=s[3], caption=s[4]) for s in SHOTS}
J1 = json.load(open(os.path.join(FILM, "gate1", "batch1_jobs.json")))["jobs"]
J2 = json.load(open(os.path.join(FILM, "gate1", "batch2_test_jobs.json")))["jobs"]

NOTES = {  # from takes/flf/seam_notes.md and the v02 test (Claude's review)
    "S02": ["v1: the crown ended up on Sarah. It has to drop over Dad's lens, and S04 needs it in his hand.",
            "v02 test: v2b lands the beat (Dad lifts the crown, Sarah kneels up to fix it on him, ends bare-headed). v2a still puts it on Sarah."],
    "S04": ["v1 opens in a dark, empty room with the crown on a plate. Wrong room and light."],
    "S05": ["v1 mascot is in a white-walled room that doesn't match the party room."],
    "S08": ["v1 opens on a stranger in a pink shirt at a gingham table instead of Sarah waving at the pit rail. Caused by 'a man's voice nearby' in the v1 prompt."],
    "S10": ["v1: the shove never happens.",
            "v02 test: v2b has the grey-shirt boy at the foam step and she topples into the balls. Ends with her sitting on the step, not visibly crying. v2a is muddy, with a floating stray hand."],
    "S14": ["v1 misses the crouch at the tube mouth and the sneakers vanishing; it's already deep in the orange tube."],
    "S15": ["v1 S15-S22 collapse to one orange concentric-ring tube image (ControlNet 1.0 painting the tube depth)."],
    "S16": ["v1 turned the net tunnel into a radial cage.",
            "v02 test: v2b is a real black rope net tunnel. Sarah stays visible crawling ahead most of the shot instead of one flash of blue; tighten the wording."],
    "S18": ["v1 is missing the star pickup. S35 pays it off."],
    "S27": ["v1 is already above the balls. It should stay under, dark, so S28 is the surfacing."],
    "S30": ["v1 has a stranger man behind the ledge (from 'a man... charcoal overshirt' in the hands line).",
            "v02 test: man gone in both, but Sarah climbs onto the ledge in v2a and v2b. Cause: the cast sheet described Sarah in every shot. Builder fixed: Sarah's description only goes into shots she's in."],
    "S32": ["v1 shows one Sarah, not 'another... and another'."],
    "S33": ["v1 shows one Sarah close, not dozens of blue tops on every bridge."],
    "S34": ["v1: the grinning idol never appears."],
    "S24-26": ["Continuous 15 s take with an FL2VA bridge spliced over the jump (h3_cont_s24272_bridged)."],
}
SEAM_OK = {"S10", "S12", "S13", "S14", "S24-26", "S29", "S36"}  # incoming cut already flows (seam sheet)


def ver(vid, label, path, **kw):
    return dict(id=vid, label=label, path=path.replace("\\", "/"), **kw)


def versions(sid):
    out = []
    for p in sorted(glob.glob(os.path.join(FILM, "takes", "batch1", f"{sid}_h3_s*.mp4"))):
        seed = int(re.search(r"_s(\d+)\.mp4$", p).group(1))
        out.append(ver("v1", "v1 batch 1", os.path.relpath(p, FILM), cn="1.0 / 1.0", seed=seed, job=J1.get(sid), prompt="batch_h3_v01"))
    for t in "ab":
        for p in sorted(glob.glob(os.path.join(FILM, "takes", "batch2_test", f"{sid}_h3v2{t}_s*.mp4"))):
            seed = int(re.search(r"_s(\d+)\.mp4$", p).group(1))
            out.append(ver(f"v2{t}", f"v2{t} test", os.path.relpath(p, FILM), cn="0.6 / 0.5" if t == "a" else "0.35 / 0.35",
                           seed=seed, job=J2.get(os.path.basename(p)[:-4]), prompt="batch_h3_v02"))
    return out


shots = []
for n in range(1, 37):
    sid = f"S{n:02d}"
    if n in (25, 26):
        continue
    if n == 24:
        t = TABLE["S24"]
        shots.append(dict(
            id="S24-26", index=24, frames=[2761, 3120], set="slide", beat="Slide",
            camera="One continuous take: fast spiral, long straight drop, shoot out over the ball sea",
            caption="Faster. Spiraling. / It keeps going. / Out into open air. A sea of balls below.",
            zone="slide", refs=["slide"], cast="", beats=[], end="", sound="", extra_avoid="",
            raw_prompt=open(os.path.join(FILM, "prompts", "s24_26_h3_continuous_v02.txt"), encoding="utf-8").read(),
            status="rev", current="v1",
            versions=[ver("v1", "v1 bridged", "takes/S24_26/h3_cont_s24272_bridged.mp4", cn="1.0 / 1.0", seed=24272, prompt="s24_26_h3_continuous_v02"),
                      ver("v0", "v0 raw 272", "takes/S24_26/h3_cont_s24272.mp4", cn="1.0 / 1.0", seed=24272, prompt="s24_26_h3_continuous_v02"),
                      ver("v0b", "v0 raw 271", "takes/S24_26/h3_cont_s24271.mp4", cn="1.0 / 1.0", seed=24271, prompt="s24_26_h3_continuous_v02")],
            notes=[dict(who="Claude", when=NOW, text=x) for x in NOTES["S24-26"]], seam_ok=True, rev=1))
        continue
    zone, refs, cast, beats, end, sound, extra = B.S[sid]
    vs = versions(sid)
    cur = "v2b" if any(v["id"] == "v2b" for v in vs) else "v1"
    status = {"S02": "rev", "S10": "rev", "S16": "rev", "S30": "fix"}.get(sid, "fix" if sid in NOTES else "rdy")
    shots.append(dict(
        id=sid, index=n, frames=[(n - 1) * 120 + 1, n * 120], **TABLE[sid],
        zone=zone, refs=list(refs), cast=cast, beats=list(beats), end=end, sound=sound, extra_avoid=extra,
        raw_prompt="", status=status, current=cur, versions=vs,
        notes=[dict(who="Claude", when=NOW, text=x) for x in NOTES.get(sid, [])],
        seam_ok=sid in SEAM_OK, rev=1))

data = dict(
    film="Everyone Here Is Happy",
    statuses=[dict(id="wtg", label="Waiting"), dict(id="rdy", label="Ready to generate"), dict(id="ip", label="Generating"),
              dict(id="rev", label="Review"), dict(id="fix", label="Needs fix"), dict(id="apr", label="Approved")],
    refs=sorted(B.K), defaults=dict(cn="0.35 / 0.35", builder="prompts/batch_h3_v02.py"),
    blockout="D:/Comfy/blockout-previs-demo/halloween-playways/animatic/ehih_halloween_animatic.mp4",
    shots=shots, rev=1)

if os.path.exists(OUT) and "--force" not in sys.argv:
    sys.exit(f"{OUT} exists; pass --force to overwrite")
tmp = OUT + ".tmp"
json.dump(data, open(tmp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
os.replace(tmp, OUT)
print(len(shots), "shots ->", OUT)
