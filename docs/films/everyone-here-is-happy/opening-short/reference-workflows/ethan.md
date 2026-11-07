# Ethan reference walkthroughs

Read the [shared setup and run instructions](README.md) first. Asset family: `CHAR_ETHAN_V01`. Both workflows are authored but have not rendered successfully on Cloud; the pilot hit an authentication rejection. No image is approved.

## What stays fixed

Use the [editable Ethan character sheet](ethan-character-sheet.md) to track revisions and reference images. Josh accepted the appearance direction below for testing; it remains a development design until an actual anchor is selected.

Ethan is Sarah's loving but distracted father. He is slightly hungover at the party; his reference should read as a recognizable ordinary person with warmth, not a horror villain. The proposed casting is mid-30s, short dark-brown hair, brown eyes, light stubble and average build. Skin tone and facial details are provisional and editable before selecting an anchor.

Wardrobe: open charcoal overshirt, plain warm-gray T-shirt, dark navy trousers, worn gray trainers. Clothes and sleeves remain intact in this opening. No time-aging, torn sleeve or later-story costume. The crooked paper crown is a shot-specific prop: it is absent from these base references and stays at the party table after the screenplay's crown beat.

## Walkthrough A — discover the anchor

File: `workflows/ehih-opening/references/ethan-anchor.json` (canvas), with matching API and role-map files.

Graph: `Nano Banana 2.1 (10) → SaveImage (20)`. Input: prompt only; no reference image. Default: 2:3, 1K, Medium, seed 10401. Output: one full-length neutral-background reference with a readable face, visible hands, complete wardrobe and shoes.

1. Import the canvas and review the full prompt in node 10. Adjust unapproved casting details deliberately, preserving the wardrobe and story role.
2. Generate one candidate and download it. Use a new run ID for another deliberate candidate; keep the preceding result for comparison.
3. Check face detail at full resolution, limb/hand anatomy, head-to-body proportions, apparent age, shirt layers and shoe consistency. An attractive face with blurred full-body details is insufficient.
4. Select a candidate for further development and record its original PNG and hash. If a different actor is wanted, return to this stage; don't try to morph a selected identity across downstream shots.

SDK equivalent:

```powershell
node --env-file=.env.local scripts/run-opening-reference.mjs submit ethan anchor ethan-anchor-02
node --env-file=.env.local scripts/run-opening-reference.mjs collect ethan-anchor-02
```

## Walkthrough B — derive the matching views

File: `workflows/ehih-opening/references/ethan-views.json`. Graph: `LoadImage (1) → Nano Banana 2.1 (10) → SaveImage (20)`. Upload the selected anchor at node 1. There is no included image behind its placeholder filename.

Generate individual views in this order: `portrait`, `profile`, `rear`, then `concern` only when preparing the disappearance shots. In the editor, replace only the last task paragraph with the corresponding `presets.json` view text; retain the preservation instructions. With the SDK helper, pass the view name and it composes the complete prompt automatically.

```powershell
node --env-file=.env.local scripts/run-opening-reference.mjs submit ethan portrait ethan-portrait-02 assets/ehih-opening/references/runs/ethan-anchor-02/candidate-1.png
```

Compare every result against the original anchor, including changes that seem flattering. Reject altered jaw/nose/ears, hairline, stubble density, age, shoulders, fabric cut, shirt layering or added accessories. The concerned expression must still be the same actor. A rear view supplements identity; it cannot replace the face anchor.

## Handoff to shots

Minimum useful set: anchor, clean portrait and profile. Add rear view for pit-entry/body-away angles. Use the selected PNGs as reference inputs to future composition workflows, then review the composed shot for the same identity. Add paper crown or later dust only in explicit shot variants with separate asset IDs. Keep `CHAR_ETHAN_V01` as the unchanged base family.

Agent review record: run ID, source anchor hash, prompt/view, face pass/fail, anatomy pass/fail, wardrobe pass/fail, approval status and reason for any rejection. Do not mark a reference approved solely because Cloud returned `succeeded`.
