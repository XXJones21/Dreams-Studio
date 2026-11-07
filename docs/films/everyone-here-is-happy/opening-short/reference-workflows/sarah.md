# Sarah reference walkthroughs

Read the [shared setup and run instructions](README.md) first. Asset family: `CHAR_SARAH_V01`. Both graphs await live Cloud validation and image review. Sarah is **four years old** throughout the opening. The later traveler version of Sarah is outside this package.

## What stays fixed

Use the [editable Sarah character sheet](sarah-character-sheet.md) to track revisions and reference images. Josh accepted the appearance direction below for testing; it remains a development design until an actual anchor is selected.

Blue top and the yellow plastic star wrist token follow the opening plan. The proposed detailed costume is a cornflower-blue long-sleeve top, charcoal leggings and off-white sneakers. Proposed appearance: shoulder-length brown hair with a side part, brown eyes and light-to-medium warm skin. These casting details are provisional.

The token is on her **anatomical left wrist** as an explicit proposed continuity choice. Front-facing, her left wrist usually appears on the viewer's right; a mirrored output is not an acceptable shortcut. Only one token exists. These references represent the period before she disappears, while she is still wearing it. After Ethan finds it, use the story's loose-token prop state, not a duplicated wrist token.

## Walkthrough A — discover the anchor

File: `workflows/ehih-opening/references/sarah-anchor.json` with matching API and role map. Graph: `Nano Banana 2.1 (10) → SaveImage (20)`. Default: 2:3, 1K, Medium, seed 10402.

1. Import the canvas, read the casting and wardrobe prompt, and adjust only unapproved choices before generating.
2. Generate one full-length neutral-background candidate, using a child-height camera and an ordinary unposed expression.
3. Check that she reads as four, not a school-age child or a scaled-down adult. Inspect facial anatomy, hair part and length, hand scale, body proportions, blue sleeve cuffs and shoes.
4. Inspect both wrists at full size. There must be exactly one yellow five-point star on the left wrist, attached to a band. If it is too small or unclear to establish shape, keep the anchor provisional and use the wrist-detail view for review; do not claim a prop design is locked from an unreadable shape.
5. Select and hash the actual PNG. If age or identity is wrong, reject before generating more views.

```powershell
node --env-file=.env.local scripts/run-opening-reference.mjs submit sarah anchor sarah-anchor-01
node --env-file=.env.local scripts/run-opening-reference.mjs collect sarah-anchor-01
```

## Walkthrough B — derive the matching views

File: `workflows/ehih-opening/references/sarah-views.json`. Upload the selected anchor in LoadImage node 1; its IMAGE output conditions node 10. Do not type an anchor filename into the prompt as a substitute.

Generate `portrait`, `profile`, `rear`, and `wrist_detail` as separate images. `upset` is an optional expression study for the foam-block incident. Use the view text from presets as the final task paragraph in the editor, or pass its key to the SDK helper.

```powershell
node --env-file=.env.local scripts/run-opening-reference.mjs submit sarah portrait sarah-portrait-01 assets/ehih-opening/references/runs/sarah-anchor-01/candidate-1.png
```

Compare each view with the anchor. Reject age drift, adult facial proportions, makeup, changed hair, new accessories, different sleeve color or an extra token. In a chest-up crop the wrists may be absent; that must not relocate the star onto a necklace or blouse. The upset view is ordinary childhood disappointment, with no injury or threat.

## Handoff to shots

Minimum useful set: anchor, portrait, profile and readable wrist detail. The separate wrist image may become a prop-detail reference after approval; it is not evidence that a newly generated token matches unless shape and attachment were compared. For the party two-shot, also inspect Sarah's height relative to Ethan; separate portraits do not establish shared physical scale.

Track identity, apparent age, wardrobe and token state separately. If wrist side or costume is changed later, update the presets, this guide and affected shot continuity together. Mark obsolete references superseded, keeping their hashes and lineage for review.
