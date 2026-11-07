# Sarah character sheet

Sarah is Ethan's four-year-old daughter in the birthday-party opening of *Everyone Here Is Happy*. Josh accepted this appearance direction for testing on October 16, 2026. It remains editable as the film develops.

Sheet revision: 01. Reference family: `CHAR_SARAH_V01`. Selected visual anchor: pending rendering and selection. This sheet covers young Sarah only; her later travels and older appearances belong to the larger story.

## Appearance and performance

| Detail | Current test direction |
|---|---|
| Age | Four |
| Hair | Shoulder-length medium brown, simple side part, no accessories |
| Eyes | Brown |
| Skin | Light-to-medium warm tone; development default |
| Proportions | Natural preschool face, hands and body; never an older child scaled down |
| Expression | Cheerful and unposed; ordinary hurt expression after the foam-block incident |
| Performance | Comfortable with Dad, playful, then upset before disappearing |
| Reference camera | Child height, soft even light, pale-gray background |

The rendered anchor will establish her exact facial structure and hair shape. Every later view should preserve that child and her apparent age.

## Wardrobe and prop continuity

| Item or state | Direction |
|---|---|
| Top | Plain cornflower-blue long-sleeve cotton |
| Leggings | Charcoal |
| Shoes | Small off-white sneakers |
| Token | One small yellow plastic five-point star on a plain yellow wrist band |
| Wrist side | Anatomical left; working continuity choice for these tests |
| Before disappearance | Sarah wears the single token |
| Later search | Ethan finds that same token loose; do not duplicate it onto Sarah or Ethan |
| Other accessories | None; no jewelry, makeup, hair ornaments or crown in the base reference |

In a front view, Sarah's left wrist usually appears on the viewer's right. Inspect anatomy rather than treating screen-left as her left. A portrait that crops out the wrists must not move the token to a necklace or her shirt.

## Reference panels

Render each view separately using the same selected anchor. Populate the image/run column with actual files after review and retain hashes in the asset register. A visual overview can later arrange those images together without asking the model to reinvent several faces in one generated sheet.

| Panel | Workflow task | Image and run record | Review focus |
|---|---|---|---|
| Full-body anchor | `sarah anchor` | Pending | Age four, proportions, wardrobe, shoes, single left-wrist token |
| Front portrait | `sarah portrait` | Pending | Face, hair part, apparent age and natural expression |
| Left profile | `sarah profile` | Pending | Ear, nose, forehead and hair length |
| Rear view | `sarah rear` | Pending | Hair silhouette, costume and anatomical wrist side |
| Wrist detail | `sarah wrist_detail` | Pending | Star shape, band attachment, blue cuff and child-size hand |
| Upset study | `sarah upset` | Pending | Same identity with an ordinary hurt expression |

## Edit and version procedure

1. Edit this sheet and the matching `subjects.sarah` fields in [presets.json](../../../../../workflows/ehih-opening/references/presets.json). Keep age, wardrobe and token rules aligned with the current screenplay.
2. Increment the sheet revision and record the decision below. If a selected face, base costume or token design changes, preserve the prior preset/images and assign a new family version, such as `CHAR_SARAH_V02`.
3. Run `node scripts/build-opening-references.mjs` to rebuild the canvases and API graphs. Generate and select the revised anchor before deriving new views.
4. Keep prior run IDs and hashes. Update affected shot references explicitly so one scene does not accidentally mix identities or token versions.

A new expression or angle can remain in the same family. Token-on-wrist and loose-token shots are different prop states of the same physical object. When Ethan and Sarah first share a composed frame, review their relative height and eyelines together; separate references do not establish shared scale.

## Revision history

| Revision | Date | Change | Decision |
|---|---|---|---|
| 01 | 2026-10-16 | Established editable test appearance, wardrobe, token state and reference panels | Josh accepted the proposed appearance for tests; rendered identity still pending |

## Production links

- [Anchor and matching-view walkthroughs](sarah.md)
- [Asset register](../../../../../assets/ehih-opening/references/asset-register.json)
- [Shared workflow setup and current Cloud status](README.md)

Cloud rendering currently awaits valid authentication. No image slots have been populated.
