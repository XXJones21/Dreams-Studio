"""H3 batch v02: regular Pika H3 Flex ref2va (template settings) + a softer depth ControlNet, Gohma-style prompts.

    python batch_h3_v02.py <depth_all.mp4 Cloud name> <out.json> [shots=S10,S16,...] [cn=0.6:0.5] [tag=a]

Changes from v01 (see takes/flf/seam_notes.md):
- ControlNet strength/end_percent default 0.6/0.5 instead of 1.0/1.0. At full strength the tube depth (concentric
  rings) was painted literally, and actions not in the clay (shove, crown, waving) were overridden.
- Prompts follow docs/On-site/dream-prompts.md (Gohma's lair): a cast sheet in every shot, numbered timed beats,
  "exactly N ... no others", a stated end state that the next shot opens on, an Avoid line.
- No clothing words on the viewer and no "a man's voice": both spawned strangers (S08 pink shirt, S30 man).
- Animation principles from the chase previs: anticipation, ease in / ease out, arcs, follow-through, end hold.
Template settings kept: lcm, ManualSigmas 1.0..0 (6 steps), 0.98 MP, 124 frames, nvfp4 text encoder, ref size match.
"""
import json, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_h3_v01 import K, DESC as DESC1

DESC = dict(DESC1)
DESC["tube"] = ("the play-structure tube in <Picture {n}>: a short, gently curving crawl tube of dull faded rotomolded "
                "plastic, scuffed vinyl-padded floor, round bolt caps at the joints, thin warm light through the plastic. "
                "Cramped for an adult, still ordinary.")
# S16 on (Josh 2026-11-01): the oner leaves the party room through its back wall; the tubes are no longer "ordinary"
DESC_TUBE_DEEP = ("the play-structure tube in <Picture {n}>: crawl tubes of the same dull faded rotomolded plastic, scuffed "
                  "vinyl-padded floor, round bolt caps at the joints, the light through the plastic thinner and warmer the "
                  "further I go. Cramped for an adult.")
DESC["party"] = DESC1["party"].replace("Ordinary, loud, a little grubby.", "Ordinary, loud, a little grubby. Only children and the one mascot are in the room; no adult is ever close to the camera.")

STYLE = ("First-person POV, one single continuous handheld take with no cuts; the camera is my own eyes, a tired father, "
         "and no other adult is ever near the camera. The only part of me ever visible is my own two bare hands and "
         "forearms in the lower frame; exactly two hands, never more. Sarah always looks the same: a girl of about five, "
         "shoulder-length brown hair, a blue long-sleeve top, dark grey leggings, cream velcro sneakers, a yellow plastic "
         "star bracelet on her left wrist. Photorealistic early-1990s live-action film still, shot on 35mm film with a real "
         "lens, practical sets and real physical materials: scuffed rotomolded plastic, vinyl padding, cheap carpet, nylon "
         "rope net. Natural textures and real-world scale. {look}. Visible film grain, slight halation around lights.")
MOTION = ("Motion: the camera moves like a real person's head and body. Every move starts with a small anticipation, eases "
          "in and eases out, travels on a gentle arc and settles with a little follow-through; nothing snaps or jitters. "
          "People move with weight. The last half second holds almost still on the end state.")
LOOK = {
    "party": "Flat cool fluorescent light from a drop ceiling, a loud ordinary room",
    "structure": "Dim warm light leaking through faded plastic walls, getting dimmer the deeper I go",
    "slide": "Dim orange glow through translucent plastic",
    "playways": "Gloomy and underlit: cold desaturated blue-grey haze against weak amber window lights, lifted milky blacks",
}
AVOID = ("Avoid: a cut, third-person view, cartoon, anime, illustration, 3D render, CGI look, video game graphics, glossy "
         "surfaces, oversaturated colors, readable text, logos, a second adult, a stranger looking at the camera, a face "
         "close to the camera, extra hands, extra mascots, monsters, concentric rings, a tunnel of repeating circles")

# id: (zone, refs, cast, beats, end, sound, extra_avoid)
S = {
 "S01": ("party", ["party"], "Children at the far tables, small in frame. No adult near me.",
   ["0-1 s: I hold a paper coffee cup in both hands at the party table, steam rising, still.",
    "1-4 s: my head pans slowly left to right across the party, easing in and out: kids eating pizza, balloons, paper plates, the yellow-poled play structure at the back.",
    "4-5 s: the pan settles and holds."],
   "the coffee cup in both hands at the bottom of frame, the party table and play structure behind.",
   "Party din, kids shrieking, arcade bleeps, a distant birthday song, fluorescent hum.", ""),
 "S02": ("party", ["party", "sarah"], "Exactly one child close to me: Sarah. The paper crown is on my head, never on Sarah's.",
   ["0-1 s: a paper birthday crown drops over the top of the view, its yellow zigzag edge covering the upper frame.",
    "1-2.5 s: my right hand rises and pushes the crown up onto my own head, out of frame.",
    "2.5-4 s: my head turns right on a smooth arc to Sarah kneeling on the bench beside me, grinning, both her hands reaching up toward my forehead to straighten the crown.",
    "4-5 s: she pats it, sits back on the bench, pleased, and holds."],
   "Sarah seated on the bench to my right, facing me, smiling, bare-headed.",
   "Paper rustle, Sarah giggles, party din.", "Sarah wearing a crown"),
 "S03": ("party", ["party", "sarah"], "Exactly one child close to me: Sarah.",
   ["0-1.5 s: Sarah slides down off the bench and lands with a little bounce.",
    "1.5-3.5 s: my view follows her down and along to the corner of the table; she walks with small heavy steps.",
    "3.5-5 s: she turns back to me with a serious little face and says her line, then holds."],
   "Sarah standing at the table corner, facing me.",
   "Sarah, small and clear: \"You say ready.\" Party din behind.", ""),
 "S04": ("party", ["party", "sarah"], "Exactly one child close to me: Sarah.",
   ["0-1.5 s: my right hand lowers the paper crown onto the laminate table in front of me.",
    "1.5-2.5 s: my view lifts to Sarah standing at a line in the carpet pattern; she crouches, winding up.",
    "2.5-3.5 s: she hops over the line and lands with a bounce, arms out for balance.",
    "3.5-5 s: she looks back over her shoulder to check I saw, and holds."],
   "Sarah a few steps away across the carpet, looking back at me, the party room behind her.",
   "My own tired voice, close to the camera: \"Ready.\" A thump of small sneakers on carpet. Party din.", "an empty room, a dark room"),
 "S05": ("party", ["mascot", "party"], "Exactly one mascot. It is a person in a costume and moves like one.",
   ["0-1.5 s: across the same fluorescent party room, the mascot waves at a table of kids.",
    "1.5-3 s: it turns slowly toward me, the big foam head lagging a beat behind its body.",
    "3-4.5 s: it waves directly at me, the glove overshooting and bouncing back.",
    "4.5-5 s: it stops with its arm still raised and holds. The grin never changes."],
   "the mascot facing me in the middle of the party room, tables and the play structure behind it.",
   "Party din, a kid laughing, the muffled squeak of the costume.", "a white empty room"),
 "S06": ("party", ["party"], "No one near me.",
   ["0-1 s: my view eases down from the room toward the table.",
    "1-3 s: on the sticky laminate table a phone lies face up, buzzing, its screen lighting up with a notification.",
    "3-5 s: my right hand comes in, picks it up and holds it close."],
   "the phone in my right hand above the table, screen lit and unreadable.",
   "Phone vibration rattling on laminate, party din.", ""),
 "S07": ("party", ["party"], "No one near me.",
   ["0-1.5 s: the phone is held close in both hands, the screen unreadable.",
    "1.5-3.5 s: my thumb types, slows, and hovers.",
    "3.5-5 s: the thumb stops; everything holds still."],
   "the phone in both hands, the party softly out of focus behind.",
   "Soft thumb taps, then nothing, party din.", ""),
 "S08": ("party", ["pit", "sarah"], "Exactly one child in focus: Sarah. No adult anywhere near me.",
   ["0-1 s: from the phone in my hands, my view lifts up with a small dip of anticipation.",
    "1-3 s: across the room at the ball pit, Sarah stands at the padded rail.",
    "3-5 s: she waves both arms at me, bouncing on her toes, and holds."],
   "Sarah at the ball-pit rail, waving, the phone low at the bottom of frame.",
   "Sarah calls across the room: \"Dad. Watch this one.\" My own voice, close to the camera: \"One second.\"",
   "a tablecloth close to the camera"),
 "S09": ("party", ["pit", "sarah"], "Exactly one child in focus: Sarah.",
   ["0-1.5 s: my view dips down to the phone in my hand.",
    "1.5-2.5 s: it lifts back up to the ball pit.",
    "2.5-5 s: Sarah climbs over the padded wall into the ball pit, one leg then the other, balls shifting, and holds."],
   "Sarah in the ball pit near the foam step.", "Ball pit rattle, party din.", ""),
 "S10": ("party", ["pit", "sarah"], "Exactly two children in focus: Sarah, and one bigger boy with short dark hair in a plain grey t-shirt.",
   ["0-1 s: my view pushes in slowly on the ball pit.",
    "1-2 s: Sarah stands on the foam step; the bigger boy climbs up right behind her.",
    "2-3 s: he shoves her in the back with both hands; she tips forward, arms flying up.",
    "3-4.5 s: she falls into the balls and balls splash out around her.",
    "4.5-5 s: she sits up crying; the boy turns away. Hold."],
   "Sarah sitting in the balls beside the foam step, crying.", "A shove, balls clattering, Sarah's startled cry.", ""),
 "S11": ("party", ["party"], "No one near me.",
   ["0-1 s: my right hand slaps the phone face down on the table.",
    "1-2 s: my view dips slightly as I get ready to stand.",
    "2-4 s: I stand up fast; the view rises over the table.",
    "4-5 s: it settles at standing height, looking across the party room toward the ball pit, and holds."],
   "a standing view across the party tables toward the ball pit.",
   "Sarah's crying cuts through the party. The bench scrapes.", ""),
 "S12": ("party", ["party", "pit"], "Children around the room, small. No adult near me.",
   ["0-4 s: walking fast between the party tables toward the ball pit, the view bobbing with each step, tables and balloons sliding past, my hands swinging into frame.",
    "4-5 s: I slow to a stop at the padded wall and hold."],
   "the ball pit close, its padded wall across the bottom of frame.",
   "My own voice, close: \"Hey. Hey, I'm here.\" Footsteps, party din.", ""),
 "S13": ("party", ["pit", "sarah"], "Exactly one child in focus: Sarah.",
   ["0-1.5 s: Sarah scrambles out of the ball pit, crying.",
    "1.5-3.5 s: she runs to the entrance of the play structure, a round tube mouth at floor level.",
    "3.5-5 s: she ducks in and disappears; my view follows and settles on the empty tube mouth."],
   "the empty round tube mouth at the base of the play structure.", "Sarah sobbing, sneakers on padding.", ""),
 "S14": ("party", ["pit", "tube"], "No one visible except a pair of small sneakers deep inside.",
   ["0-1.5 s: I crouch down at the round tube mouth; the view drops to child height.",
    "1.5-2.5 s: my two hands grip its rim.",
    "2.5-4.5 s: deep inside, a pair of small cream sneakers slips away around the bend.",
    "4.5-5 s: hold on the empty bend."],
   "looking into a short padded tube that bends out of sight, my hands on the rim.",
   "Hollow plastic echo, a sniffle fading away inside the tube.", ""),
 "S15": ("structure", ["tube"], "No one visible.",
   ["0-4 s: I crawl forward through a short, gently curving padded tube, the view rocking side to side with each move, my hands planting on the scuffed padded floor one after the other, joints and bolt caps passing on both sides.",
    "4-5 s: ahead, the tube opens into a rope net tunnel. Hold."],
   "the tube mouth opening into a rope net tunnel ahead.",
   "Knees and palms on vinyl, breathing, my own voice: \"Sarah?\" The party muffled outside.", ""),
 "S16": ("structure", ["tube", "sarah"], "Exactly one small figure, far away: Sarah, seen only for a moment.",
   ["0-1.5 s: I crawl into a tunnel made of thick black nylon rope net stretched over a frame, square holes, the party room blurred through the net; the net sags under my hands.",
    "1.5-3 s: far ahead at the corner, a flash of a blue long-sleeve top whips out of sight.",
    "3-5 s: I crawl faster toward the corner and hold on it, empty."],
   "the empty corner of the rope net tunnel ahead.", "Net creaking, distant small footsteps, the party fainter.",
   "metal bars, a cage, a radial pattern"),
 "S17": ("structure", ["junction"], "No one visible.",
   ["0-1 s: I crawl into the teal junction chamber.",
    "1-2.5 s: my head turns left on an arc into a red tube mouth and pauses.",
    "2.5-4 s: it turns right into a yellow tube mouth and pauses.",
    "4-5 s: back to the middle; I move toward the middle tube and hold."],
   "facing the middle tube mouth of the teal junction.", "Breathing, plastic creaks, the party barely audible.", ""),
 "S18": ("structure", ["tube"], "No one visible.",
   ["0-1.5 s: crawling through the tube, the view slows and stops.",
    "1.5-2.5 s: on the padded floor lies one small yellow plastic star charm.",
    "2.5-4 s: my right hand picks it up and lifts it close to the camera.",
    "4-5 s: I hold it, then close my fist around it."],
   "my closed right fist close to the camera, the yellow star showing between the fingers.", "A tiny plastic click, breathing.", ""),
 "S19": ("structure", ["tube"], "No one visible.",
   ["0-5 s: a long straight padded tube runs ahead, the same joints repeating far past where the building should end; a slow steady push forward, easing in. The far end is lost in gloom."],
   "the tube continuing into darkness.", "Breathing, plastic, the party gone faint and far.", ""),
 "S20": ("structure", ["junction"], "No one visible.",
   ["0-1 s: I come out into the teal junction chamber again, from another side.",
    "1-4 s: the view pushes in slowly on one faded smiling-sun sticker on the teal wall.",
    "4-5 s: my right hand rises and presses flat on the wall beside it. Hold."],
   "my hand flat on the teal wall beside the faded sticker.", "Near silence, a low hum starting.", ""),
 "S21": ("structure", ["tube"], "No one visible.",
   ["0-5 s: padded steps lead down into a warmer, dimmer section; my hands on the padded edges, the view stepping down one step at a time with a small bob on each step."],
   "the bottom of the steps, a short dim tube ahead.", "Muffled thumps on padding, the hum growing.", ""),
 "S22": ("structure", ["tube", "slide"], "No one visible.",
   ["0-1.5 s: in the tube wall ahead is a dark round slide mouth that was not there before.",
    "1.5-3 s: my hands grip its rim.",
    "3-5 s: I lean in and peer into the black, and hold."],
   "looking into the black slide mouth, my hands on its rim.",
   "My own voice into the dark: \"Sarah?\" It echoes far too long.", ""),
 "S23": ("slide", ["slide", "tube"], "No one visible.",
   ["0-1.5 s: I climb into the slide mouth, hands on the walls.",
    "1.5-2.5 s: the floor tips forward; a moment of stillness.",
    "2.5-5 s: I start to slide, slowly then faster, hands skidding along the walls as the tube curves down."],
   "sliding fast down the dull orange tube.", "Plastic squeal, a sharp breath, the slide roar starting.", ""),
 "S27": ("playways", ["playways"], "No people.",
   ["0-5 s: darkness under the balls: dim colored balls pressed against the view, my hands clawing at them, thin cold blue light leaking from above and slowly growing as I rise."],
   "the balls thinning, the light brightening just above.", "Muffled clatter, heartbeat, pressure.", "towers, open air"),
 "S28": ("playways", ["playways"], "No people.",
   ["0-1.5 s: my hands push up through the balls.",
    "1.5-3 s: the view breaks the surface, balls spilling off.",
    "3-5 s: I look around at the hazy Playways and hold."],
   "a level view across the ball sea toward the towers.",
   "Balls rolling off, a gasp, then silence and a low hum where the party was.", ""),
 "S29": ("playways", ["playways"], "No people.",
   ["0-5 s: from the ball sea, my view tilts slowly up the towers, easing in and easing out, up and up into haze, no top in sight."],
   "looking almost straight up into haze.", "A low enormous hum, distant creaks.", ""),
 "S30": ("playways", ["playways"], "No people at all.",
   ["0-1 s: my view tilts back down to the ball sea.",
    "1-3 s: I wade through the balls to a padded ledge.",
    "3-4.5 s: my hands grab its edge and I haul myself up, the view rising over the top.",
    "4.5-5 s: kneeling on the empty ledge. Hold."],
   "the empty ledge, seen from on top of it, looking out over the ball sea at the towers.",
   "Balls shifting, heavy breathing, vinyl creak.", "a person on or behind the ledge"),
 "S31": ("playways", ["playways", "sarah"], "Exactly one small figure, far away.",
   ["0-1.5 s: I stand on the ledge looking out.",
    "1.5-3.5 s: far off on a net bridge high up, one small figure in a blue long-sleeve top stands with her back turned, perfectly still.",
    "3.5-5 s: my view pushes in a little and holds."],
   "the far net bridge with the single small figure.",
   "My own voice, shouting: \"Sarah!\" It rolls away into the space with no answer.", ""),
 "S32": ("playways", ["playways", "sarah"], "Exactly three small figures in blue tops, all identical to Sarah, all far away, backs turned.",
   ["0-1.5 s: hold on the figure on the bridge.",
    "1.5-3 s: my view pans right: another small figure in a blue top stands in a lit window, back turned.",
    "3-5 s: and another, at the top of a slide, back turned. Hold."],
   "the third small figure at the top of a slide.", "The hum, distant creaks.", ""),
 "S33": ("playways", ["playways", "sarah"], "Dozens of identical small figures in blue tops, all far away, backs turned, all still.",
   ["0-1 s: the view holds, gathering.",
    "1-4 s: a fast whip pan across the bridges, with motion blur: a small figure in a blue top on every bridge and catwalk.",
    "4-5 s: the pan stops, overshoots a little, settles and holds."],
   "a bridge lined with small blue-top figures, backs turned.", "The whoosh of the pan, then the hum.", ""),
 "S34": ("playways", ["playways", "idol"], "Many tiny still figures in blue tops, backs turned; exactly one giant mascot idol.",
   ["0-4 s: my view tilts slowly up the tiers, every tier dotted with tiny still blue-top figures turned away.",
    "4-5 s: at the top, the giant grinning mascot idol looks down. Hold."],
   "the giant grinning mascot face filling the upper frame.", "A deep swelling drone.", ""),
 "S35": ("playways", ["playways"], "No people.",
   ["0-1.5 s: my view tilts down from above to my hands.",
    "1.5-4 s: my right hand opens slowly; on the palm lies the small yellow plastic star charm.",
    "4-5 s: hold."],
   "my open palm with the yellow star, the ball sea below.", "The hum, a single breath.", ""),
 "S36": ("playways", ["playways"], "No people.",
   ["0-4.5 s: a slow tilt up into a tower that never ends, easing in, rising into haze and dark.",
    "4.5-5 s: the frame goes to black."],
   "black.", "The hum swelling, then cut to silence.", ""),
}
# The table above is the 2026-11-01 seed. tracker/shots.json is the source of truth from then on (edited in the
# tracker page); set EHIH_NO_TRACKER=1 to use the seed table instead.
TRACKER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tracker", "shots.json")


def load_tracker(path=TRACKER):
    d = json.load(open(path, encoding="utf-8"))
    return {s["id"]: (s["zone"], s["refs"], s["cast"], s["beats"], s["end"], s["sound"], s.get("extra_avoid", ""))
            for s in d["shots"] if s.get("beats")}


if os.path.exists(TRACKER) and not os.environ.get("EHIH_NO_TRACKER"):
    S = load_tracker()
ORDER = list(S)


def prompt(sid):
    zone, refs, cast, beats, end, sound, extra = S[sid]
    i = ORDER.index(sid)
    prev_end = S[ORDER[i - 1]][4] if i > 0 else None  # every shot is continuous (Josh 2026-11-01)
    deep = int(sid[1:3]) >= 16
    subs = [f"<Subject {k + 1}> is " + (DESC_TUBE_DEEP if (r == "tube" and deep) else DESC[r]).format(n=k + 1)
            for k, r in enumerate(refs)]
    opening = f"The shot opens where the last one ended: {prev_end}" if prev_end else ""
    first = beats[0].split(": ", 1)[-1]
    style = STYLE.format(look=LOOK[zone])
    if int(sid[1:3]) >= 18:  # Dad picks up her star in S18: from then on Sarah has no bracelet
        style = style.replace(", a yellow plastic star bracelet on her left wrist", "")
        subs = [x.replace(", a yellow star bracelet on her left wrist", "") for x in subs]
    if "sarah" not in refs:
        # Test 2026-11-01: describing Sarah in a shot she is not in made her appear (S30 v2a/v2b climbed the ledge).
        style = re.sub(r"Sarah always looks the same:.*?left wrist\. ", "", style)
        if zone != "party" and "blue top" not in cast:
            extra = ", ".join(x for x in (extra, "a child, a girl in a blue top") if x)
    return "\n".join([
        "subject_definitions:", *subs, "",
        "summary:",
        f"[reference generation] A five-second single continuous first-person shot. {first[:1].upper() + first[1:]} It ends on {end}", "",
        "retention_analysis:",
        *[f"<Subject {k + 1}>: fully_preserved." for k in range(len(refs))],
        "No audio reference is used in this generation.", "",
        "detailed_description:",
        style, MOTION, cast, "",
        f"[Shot 1] {opening}".rstrip() + " In order: " + " ".join(f"{n + 1}. {b}" for n, b in enumerate(beats)),
        f"The shot ends on: {end}", "",
        "overall_soundscape:", sound, "",
        "non_diegetic_music:", "None.", "",
        AVOID + (", " + extra if extra else "") + ".",
    ])


def graph(sid, P, depth, seed, cn, tag):
    idx = int(sid[1:]) - 1
    start = idx * 124 / 24 + 0.01
    refs = S[sid][1]
    if len(refs) == 1:
        refs = refs * 2
    strength, end_pct = cn
    g = {
        "127": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "145": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["127", 0], "lora_name": "pika_h3_flex_ref2va_v1_bf16.safetensors", "strength_model": 1}},
        "173": {"class_type": "ModelPatchLoader", "inputs": {"name": "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors"}},
        "174": {"class_type": "LoadVideo", "inputs": {"file": depth}},
        "705": {"class_type": "Video Slice", "inputs": {"video": ["174", 0], "start_time": round(start, 4), "duration": round(124 / 24, 4), "strict_duration": False}},
        "709": {"class_type": "GetVideoComponents", "inputs": {"video": ["705", 0]}},
        "172": {"class_type": "MiniMaxH3FunControlNetApply", "inputs": {"model": ["145", 0], "model_patch": ["173", 0], "vae": ["119", 0], "strength": strength, "start_percent": 0.0, "end_percent": end_pct, "control_video": ["709", 0]}},
        "128": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "119": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "120": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "115": {"class_type": "ResolutionSelector", "inputs": {"aspect_ratio": "9:16 (Portrait Widescreen)", "megapixels": 0.98, "multiple": 32}},
        "136": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"clip": ["128", 0], "vae": ["119", 0], "audio_vae": ["120", 0],
                "prompt": P, "width": ["115", 0], "height": ["115", 1], "length": 124, "ref_image_size": "match"}},
        "126": {"class_type": "BasicGuider", "inputs": {"model": ["172", 0], "conditioning": ["136", 0]}},
        "129": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "123": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "lcm"}},
        "147": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0"}},
        "125": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["129", 0], "guider": ["126", 0], "sampler": ["123", 0], "sigmas": ["147", 0], "latent_image": ["136", 1]}},
        "122": {"class_type": "VAEDecode", "inputs": {"samples": ["125", 0], "vae": ["119", 0]}},
        "121": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["125", 0], "vae": ["120", 0]}},
        "130": {"class_type": "CreateVideo", "inputs": {"images": ["122", 0], "audio": ["121", 0], "fps": 24}},
        "92": {"class_type": "SaveVideo", "inputs": {"video": ["130", 0], "filename_prefix": f"ehih/halloween/batch2/{sid}_h3v2{tag}_s{seed}", "format": "auto", "codec": "auto"}},
    }
    for k, r in enumerate(refs):
        g[str(150 + k)] = {"class_type": "LoadImage", "inputs": {"image": K[r]}}
        g["136"]["inputs"][f"ref_images.ref_image_{k}"] = [str(150 + k), 0]
    return g


if __name__ == "__main__":
    depth, out = sys.argv[1], sys.argv[2]
    opts = dict(a.split("=", 1) for a in sys.argv[3:])
    shots = opts.get("shots", ",".join(ORDER)).split(",")
    cn = tuple(float(x) for x in opts.get("cn", "0.35:0.35").split(":"))
    tag = opts.get("tag", "a")
    items = []
    for sid in shots:
        seed = 20000 + int(sid[1:]) * 10 + (ord(tag) - 96)
        items.append({"tool": "submit_workflow", "description": f"{sid}_h3v2{tag}_s{seed}", "workflow": graph(sid, prompt(sid), depth, seed, cn, tag)})
    json.dump(items, open(out, "w"))
    print(len(items), "items", "cn", cn)
