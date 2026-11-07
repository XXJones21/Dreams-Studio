# Ethan character sheet

Ethan is Sarah's father in the birthday-party opening of *Everyone Here Is Happy*. Josh accepted this appearance direction for testing on October 16, 2026. It remains editable as the film develops.

Sheet revision: 01. Reference family: `CHAR_ETHAN_V01`. Selected visual anchor: pending rendering and selection. Acceptance of the test description does not select an unseen face.

## Appearance and performance

| Detail | Current test direction |
|---|---|
| Apparent age | Mid-30s |
| Hair | Short, slightly untidy dark brown |
| Facial hair | Light stubble |
| Eyes | Brown |
| Skin | Light-to-medium warm tone; development default |
| Build | Average, ordinary adult proportions |
| Expression | Slightly tired eyes, approachable features, warmth underneath fatigue |
| Performance | Distracted and mildly hungover at the party; affectionate with Sarah; concern becomes focused searching |
| Reference lighting | Soft, even light against pale gray; readable skin and clothing |

The rendered anchor will establish the exact face, hairline, ears and body proportions. Do not invent those details independently in each later shot.

## Wardrobe and continuity

| Item or state | Direction |
|---|---|
| Overshirt | Charcoal cotton, worn open, sleeves intact |
| T-shirt | Plain warm-gray crewneck |
| Trousers | Dark navy |
| Shoes | Worn gray trainers |
| Base accessories | None; no hat, jewelry, wrist token or handheld props |
| Paper crown | Add only for the relevant party shots; left at the table after the crown beat |
| Pit entry | Same clothes; any later dust is a separately recorded shot state |
| Excluded from this opening | Torn sleeve, visible aging and later-story costume changes |

## Reference panels

Render these separately from the same selected anchor. Attach or embed the actual PNG in each row when available, retaining the full file path and hash in the asset register. A compiled visual sheet is a review aid; individual source images remain the conditioning references.

| Panel | Workflow task | Image and run record | Review focus |
|---|---|---|---|
| Full-body anchor | `ethan anchor` | Pending | Face, proportions, complete wardrobe, hands and shoes |
| Front portrait | `ethan portrait` | Pending | Eyes, ears, hairline, stubble and facial structure |
| Left profile | `ethan profile` | Pending | Nose, forehead, jaw and ear shape |
| Rear view | `ethan rear` | Pending | Hair silhouette and back of clothing |
| Concern study | `ethan concern` | Pending | Same identity under a restrained expression change |

## Edit and version procedure

1. Edit the description here and the matching `subjects.ethan` fields in [presets.json](../../../../../workflows/ehih-opening/references/presets.json). Presets supply generation prompts; this sheet explains the choices.
2. Increment this sheet revision and note the change below. For a replacement actor or a change to a selected base costume, preserve the old preset and references, and create a new family version such as `CHAR_ETHAN_V02`.
3. Rebuild the canvases/API graphs with `node scripts/build-opening-references.mjs`. Generate the revised anchor before deriving new views.
4. Keep old reference images and their run IDs. Mark which version each downstream shot uses; do not silently replace an image behind an existing approved asset ID.

For a new angle or expression of the same identity, keep the family version and add a named view. Crown and dust changes are shot states, not new actors.

## Revision history

| Revision | Date | Change | Decision |
|---|---|---|---|
| 01 | 2026-10-16 | Established editable test appearance, wardrobe and reference panels | Josh accepted the proposed appearance for tests; rendered identity still pending |

## Production links

- [Anchor and matching-view walkthroughs](ethan.md)
- [Asset register](../../../../../assets/ehih-opening/references/asset-register.json)
- [Shared workflow setup and current Cloud status](README.md)

Cloud rendering currently awaits valid authentication. No image slots have been populated.
