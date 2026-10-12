// Starting points for the form. Every field stays editable.

export type Preset = { style: string; scene: string; avoid: string; clips: [string, string, string] };

const CAVERN: Preset = {
  style: "First-person POV, one single continuous handheld take with no cuts; the camera is my own eyes and I am alone. " +
    "In the lower frame I always see exactly two hands: my left hand, in a brown leather gauntlet, holds one short steel sword; " +
    "my right forearm carries a round wooden shield with a red spiral emblem. There is only one sword, and the shield never " +
    "leaves my right arm. The skeletons always look the same: adult-sized human skeletons with normal anatomical proportions, " +
    "weathered brown-stained bone, cracked skulls with faint red embers deep in the eye sockets, scraps of rotted cloth and dirt " +
    "clinging to them. A still from a 1980s live-action fantasy film in the style of Legend, Willow and Dragonslayer, shot on Kodak 35mm film stock with practical sets and real " +
    "physical materials: wet root, packed earth, old bone, rusted iron. Color grade: muted, slightly faded colors; cool " +
    "steel-blue haze and smoke filling the air; soft warm amber torchlight that glows rather than burns; lifted milky blacks, " +
    "low contrast; diffusion filter bloom and halation around every light; soft focus falloff; visible film grain. Grim and ominous.",
  scene: "A deep underground cavern beneath an ancient giant tree. Thick twisted roots form the walls and ceiling, hung with " +
    "cobwebs and patches of faintly glowing green moss. Torches burn in iron brackets on the roots. The dirt floor in front of me " +
    "is cracked open, and a bony skeletal hand is clawing up out of the earth. My sword is held forward in my left hand, my " +
    "shield raised on my right arm.",
  avoid: "Avoid: cartoon, anime, illustration, painting, 3D render, CGI look, video game graphics, toy, plastic, claymation, " +
    "chibi or bobblehead proportions, oversized heads, cute faces, glossy surfaces, HDR, crisp digital sharpness, high contrast, " +
    "crushed pure-black shadows, modern teal-and-orange grade, saturated orange fire, extra hands, two swords.",
  clips: [
    "There are exactly three skeletons, and the cavern behind them stays empty; no other skeletons ever appear. Each has its own " +
      "silhouette: Left is short and hunched with a dangling lower jaw; Center is the tallest, with a cracked skull; Right drags " +
      "a rusted iron shackle and chain from one wrist. The motion is slow and heavy, one action at a time. 0–3 s: The dirt in " +
      "front of me bulges and trembles before it breaks; Left's bony hand bursts up, fingers curling, then the arm drags its " +
      "skull and shoulders free as soil slides off in clumps. 3–6 s: The floor bulges again; Center pushes up in one long rising " +
      "arc, its head coming up last, then pauses and sways while Left keeps shaking dirt from its ribs. 6–9 s: Right claws its " +
      "way out, its chain uncoiling from the dirt a beat after its arm and clattering behind it. 9–13 s: All three straighten, " +
      "their heads snapping toward me a beat after their bodies turn; they lurch forward in slow staggering steps, arms swinging " +
      "loosely behind each step, while I ease backward with my sword and shield rising. 13–15 s: They stop close in front of me " +
      "and hold, swaying, Left's jaw rattling, Right's chain still swinging to a stop. Only these three skeletons, with the empty " +
      "cavern behind them. Sound: earth cracking, bones scraping, a chain dragging, low hollow moaning, my breathing, torches crackling.",
    "Exactly three skeletons stand in front of me: Left, short and hunched with a dangling jaw; Center, the tallest, with a " +
      "cracked skull; Right, with a rusted shackle and chain on one wrist. No other skeletons. Only one attacks at a time while " +
      "the other two hold back, swaying. 0–4 s: Center rears back with its arms raised high over its head, hangs there for a " +
      "beat, then slams its claws down onto my shield, jolting it. I draw my sword far back, pause, then swing it forward in a " +
      "wide flat arc through its ribs: its skull flies off in a high arc and bounces away, its ribcage bursts apart, and its arm " +
      "and leg bones fall a split second later, scattering across the dirt. 4–8 s: Left crouches low, coils, then springs at my " +
      "head; I drop behind my shield, then chop down in a steep arc, and it breaks apart at every joint, its jaw flying loose " +
      "last, the bones bouncing and settling into a pile at my feet. 8–12 s: Right whips its chain around the rim of my shield " +
      "and yanks, pulling the shield toward it; I lean back, shove hard, and as it staggers I slash up through its spine in a " +
      "rising arc: skull, ribs and limbs scatter, and the chain slides off last and coils on the dirt. 12–15 s: I slow down, " +
      "lower my sword and look down: no whole skeletons remain, only separate scattered bones, three skulls and a loose chain. " +
      "Dust drifts down and settles; nothing moves; my breathing slows. Sound: claws scraping wood, a chain rattling, steel " +
      "cracking bone, bones clattering onto dirt, my heavy breathing.",
    "Separate scattered bones, three skulls and a loose rusted chain lie on the dirt in front of me. 0–3 s: The bones twitch, " +
      "slowly at first and then faster, sliding toward each other; the skulls wobble, roll and click back into place, and three " +
      "half-built ribcages lift unsteadily off the ground. 3–6 s: A trickle of dirt falls from above. I look up slowly: a giant " +
      "spider-like creature clings upside down to the ceiling roots, drawing its legs in tight and lowering its body, gathering " +
      "itself. 6–8 s: It lets go. I look down as it falls in a heavy arc and lands on the half-built skeletons; its body sinks " +
      "low as its legs buckle under its weight, then pushes back up; bone fragments spray outward and keep bouncing after it " +
      "lands, and dust rolls out in a wave. 8–13 s: It crawls toward me, slowly at first and then faster, its legs stepping one " +
      "after another in a rippling wave, its body swaying side to side and its head arriving last, until its head fills the " +
      "frame. 13–15 s: It pulls its head back and rears up high, holds for a beat, then shrieks with its mandibles spread wide; " +
      "I raise my shield and point my sword at its eye. The creature looks like a real giant arachnid, taller than a horse: dull " +
      "olive-brown chitin caked with dust and cobwebs, six long hairy jointed legs, two front legs ending in hooked claws, wet " +
      "mandibles, and one single enormous eye in the center of its head that glows a dull ember red through the haze. No metal, " +
      "no armor plates, no shine. Sound: bones rattling, dirt trickling, roots tearing, a heavy crunching impact, clacking legs, " +
      "an ear-splitting insect shriek, a deep drone.",
  ],
};

const BLANK: Preset = {
  style: "First-person POV, one single continuous handheld take with no cuts; the camera is my own eyes and I am alone. ",
  scene: "",
  avoid: CAVERN.avoid,
  clips: ["", "", ""],
};

export const PRESETS = { "Skeleton cavern": CAVERN, Blank: BLANK } as const;
export type PresetName = keyof typeof PRESETS;
