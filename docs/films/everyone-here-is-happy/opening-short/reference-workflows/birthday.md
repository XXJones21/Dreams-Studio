# Birthday venue reference walkthroughs

Read the [shared setup and run instructions](README.md) first. These workflows establish the ordinary birthday room and ball pit before the impossible transition. They do not build the Playways, passage, Archives or later-world locations. The set design is provisional and no image is approved.

## Spatial contract

North/east/south/west are design directions for continuity, not compass claims about a real venue. Use this proposed plan when reviewing generated views:

```text
                          NORTH
              +--------------------------------+
              |         mesh climbing frame    |
              |                +------------S--|
 WEST windows |                | BALL PIT      | EAST
              |                |              |
              |                G--------------|
              |       clear    ^ blue step    |
              |     sightline                 |
              |  PARTY TABLE                  |
              | C                             |
              +--------------------------------+
                          SOUTH

C = master camera in southwest, looking northeast
G = only gate, in the south rail near the pit's southwest corner
S = ordinary closed padded seam in the pit's northeast back corner
```

The party table sits southwest of the pit, with a clear view to the gate. The blue foam step is immediately inside that gate. Mesh climbing equipment is above the north side. This geometry is a review constraint supplied through text, not a depth map or a measured 3D set. Generated angles can still contradict it.

Visual proposal: cream walls, pale wood-look floor, teal padding, blue/yellow paper decorations, red/yellow/blue/green balls, daylight from the west. Everything looks maintained and ordinary. No sinister mascot, portal, tunnel, dates, clocks, recognizable brand or premature supernatural lighting. We deliberately generate empty clean plates first so unrelated faces do not become accidental recurring cast.

## Walkthrough A — establish the room master

File: `workflows/ehih-opening/references/birthday-anchor.json` with API and input map. Graph: `Nano Banana 2.1 (10) → SaveImage (20)`. Default: 16:9, 1K, Medium, seed 10403. Output family: `LOC_PARTY_V01`.

1. Import the canvas and check the prompt against the spatial contract. Treat room dimensions and decor as a design proposal.
2. Run one master, with the southwest camera looking northeast. The party table should be left foreground and pit right midground; the gate and step must be legible.
3. Check plausible scale and usable camera positions. Ethan must be able to see the pit, walk to the gate and enter it. Reject obstructed sightlines, duplicate gates, impossible climbing equipment, floating furniture or exaggerated endless architecture.
4. Check light direction, padding colors, ball palette, and that the back seam looks ordinary. Reject ominous details rather than carrying them into every derivative.
5. Select and hash a master. Record any necessary plan revision before deriving angles. Do not call an incoherent master a set bible.

```powershell
node --env-file=.env.local scripts/run-opening-reference.mjs submit birthday anchor birthday-anchor-01
node --env-file=.env.local scripts/run-opening-reference.mjs collect birthday-anchor-01
```

## Walkthrough B — derive coverage plates

File: `workflows/ehih-opening/references/birthday-views.json`. Upload the selected master at node 1. All derivatives should branch from that master, not from successive generated views.

| View preset | Intended asset ID | Review purpose |
|---|---|---|
| `pit_axis` (default) | `LOC_PARTY_PIT_AXIS_V01` | Ethan's seated view from table to gate; establishes eyeline |
| `pit_child_height` | `LOC_PIT_V01` | Same gate and step at Sarah's camera height |
| `seam_detail` | `LOC_SEAM_V01` | Closed padded seam before the threshold opens |
| `reverse_axis` | `LOC_PARTY_REVERSE_V01` | Diagnostic for table/window/gate relationships from the pit |

These are intended IDs, not claims that those images exist. Keep actual selected files null until rendered and reviewed.

```powershell
node --env-file=.env.local scripts/run-opening-reference.mjs submit birthday pit_axis birthday-pit-axis-01 assets/ehih-opening/references/runs/birthday-anchor-01/candidate-1.png
```

In the Cloud editor, retain the room description and preservation paragraphs, replacing only the final camera-task paragraph with the chosen view preset. Change the SaveImage prefix for every view. Compare the result with the plan and master side by side.

A reverse view reveals geometry not present in the source image. Treat it as a proposed extension, never automatic proof of spatial consistency. If the master and reverse cannot be reconciled, reject the angle, reduce the camera move, or establish a simple 3D blockout in a later package. Do not keep rewording contradictory geometry until one attractive frame passes casually.

## Handoff to shots

Minimum useful set: master, pit axis, child-height pit and closed seam detail. Background party attendees, cups and cake actions belong in composed shot keyframes after the clean geography is selected. A neutral empty plate is not a completed birthday-party scene.

For each plate record camera position, direction, approximate height, lens feel, gate/step/seam visibility and light direction. Hand these alongside the PNG/hash to the shot-composition agent. Generated lens language is an aesthetic cue, not calibrated lens metadata. The threshold-open state and Playways arrival require new workflows and must not overwrite the normal seam reference.
