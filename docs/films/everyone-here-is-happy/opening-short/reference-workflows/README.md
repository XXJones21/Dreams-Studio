# Opening reference workflows

These workflows establish Ethan, Sarah and the birthday venue for the five-minute opening. They create still references for later shot composition and animation. They do not generate the entire film or make a character automatically consistent across shots.

## Current delivery and validation

Six Comfy Cloud workflow canvases, six matching API graphs, input maps, editable presets, a build script, and a submit/collect helper are included. Each run has one Nano Banana 2.1 generation and one SaveImage output. No extra custom node pack, local checkpoint or LoRA is required by these graphs.

The node structures come from this repository's existing Cloud workflow. The reference socket was also checked against the [official Nano Banana 2.1 image-edit template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/api_nano_banana_2_1_image_edit.json). API/canvas consistency is checked by `test/opening-references.test.ts`.

Local verification on October 16: all 25 repository tests passed, TypeScript checking passed, the runner's syntax and offline preparation passed, and all relative links in these walkthroughs resolved. The machine's global `npm` shim points to a missing `npm-cli.js`, so the test commands were executed directly as `node --test --experimental-strip-types test/*.test.ts` and `node node_modules/typescript/bin/tsc --noEmit`. No package or global tooling change was needed.

**Cloud execution is not yet verified.** On October 16, 2026, the Ethan anchor pilot first encountered sandbox network restrictions; a network-enabled attempt with the same request key reached Cloud and received `Unauthorized`. No job ID or image was returned. The saved record is `assets/ehih-opening/references/runs/ethan-anchor-pilot-01/record.json`. Authentication failed before graph acceptance could be established. Canvas import and rendering still need a live Cloud check. No character or environment asset is approved.

## Packages

All workflow links below are relative to this guide; save/import the `.json` canvas, not the `.api.json` file, in the Cloud editor.

| Package and walkthrough | Discover an anchor | Derive matching views |
|---|---|---|
| [Ethan](ethan.md) | [ethan-anchor.json](../../../../../workflows/ehih-opening/references/ethan-anchor.json) | [ethan-views.json](../../../../../workflows/ehih-opening/references/ethan-views.json) |
| [Sarah](sarah.md) | [sarah-anchor.json](../../../../../workflows/ehih-opening/references/sarah-anchor.json) | [sarah-views.json](../../../../../workflows/ehih-opening/references/sarah-views.json) |
| [Birthday venue](birthday.md) | [birthday-anchor.json](../../../../../workflows/ehih-opening/references/birthday-anchor.json) | [birthday-views.json](../../../../../workflows/ehih-opening/references/birthday-views.json) |

Each stem also has `.api.json` for the SDK and `.inputs.json` for named overrides. [presets.json](../../../../../workflows/ehih-opening/references/presets.json) is the editable prompt source. [registry.json](../../../../../workflows/ehih-opening/references/registry.json) indexes all six graphs. [Agent review and extension](agent-handoff.md) describes the handoff contract.

## Design decisions

Josh accepted the proposed character appearances for testing on October 16, 2026. The editable [Ethan character sheet](ethan-character-sheet.md) and [Sarah character sheet](sarah-character-sheet.md) track appearance, wardrobe, reference panels and revisions alongside the prompt presets. Both await rendered anchors; test-direction acceptance does not mark an unseen image approved.

Use one anchor to establish identity or room design. Pick a candidate on visual merit, then feed those exact image bytes into the views workflow through `LoadImage → model.images.image_1`. Repeated text and seeds are insufficient identity controls. A reference-conditioned result can still drift and must be inspected.

Each view is a separate photograph. This avoids ambiguous faces in generated contact sheets and provides clean inputs for later shot composition. Review sheets may be assembled after the individual images pass inspection. Always branch from the selected anchor; repeatedly editing the previous derivative can accumulate drift.

Default previews are 1K, Medium thinking, with fixed documented seeds. The seed helps record an attempt; it does not promise identical provider outputs. Character reference images use 2:3 for full-body coverage; the room uses 16:9 as a proposed film frame. Reference portrait aspect ratio does not force the final film aspect ratio. Raise resolution only after the design works. [Comfy's announcement](https://blog.comfy.org/p/gemini-nano-banana-21-is-now-available) describes the model's editing and reference support.

## Common Cloud editor walkthrough

1. Open Comfy Cloud while signed in to the intended workspace. Import a package's `*-anchor.json`. Check that the Nano Banana node is recognized and its model is **Gemini Nano Banana 2.1**. A missing node/model is a compatibility issue, not a prompt problem.
2. Read the package guide and edit the prompt if casting or set choices need changing. The preset details are proposals, not previously approved character designs.
3. Check resolution, aspect ratio, thinking level and seed. Run **one** candidate. Partner generation uses credits; the displayed current price and workspace balance govern. Download the saved PNG immediately.
4. Inspect it at full size against that package's acceptance criteria. Record failures as well as successes. Select an anchor; keep its original PNG and SHA-256. A visually plausible candidate is not automatically project-approved.
5. Import the matching `*-views.json`. Its LoadImage filename is deliberately an instruction placeholder, not an included reference image. Upload and select the actual anchor PNG before running. The anchor workflow has no LoadImage node and needs no placeholder upload.
6. The default view is a portrait for characters and `pit_axis` for the room. Other ready-to-use tasks are in `presets.json → subjects → <subject> → views`. Retain the style, identity and preserve paragraphs, replacing only the final task paragraph. Change SaveImage's filename prefix to the chosen view and version.
7. Queue one view, compare it side by side with the anchor, and reject drift. Repeat individually for needed views. Keep the original anchor selected throughout.
8. Save the edited canvas and Export (API) if changes will be retained. Reconcile presets and input maps before handing the package to another agent. A UI-only edit is not automatically applied to the SDK graph.

## Node and input contract

| Node | Purpose | Inputs agents may override |
|---|---|---|
| `1`, views only | Load selected anchor | `image`: uploaded Cloud filename, or SDK asset handle |
| `10` | Nano Banana 2.1 | `prompt`, `seed`, `model.aspect_ratio`, `model.resolution`, `model.thinking_level` |
| `20` | Save one candidate image | `filename_prefix`; `images` stays connected to node 10 output 0 |

Dots inside names such as `model.aspect_ratio` are part of the actual field name. In role maps, split at the first dot only. `model.images.image_1` is a reference image socket, not a string filename field; it must remain connected to node 1's IMAGE output in views graphs. Never replace this connection with a description of the image.

## Rebuild and local checks

From `D:\Comfy\Dreams-studio`:

```powershell
node scripts/build-opening-references.mjs
npm test
```

Rebuilding overwrites the six canvas/API/map sets and registry from the presets and existing Dream Film node shapes. It does not overwrite saved run records, images, or the asset register. For a new visual version, first preserve the old preset/graphs and change the asset-family version rather than silently redefining an approved identity.

## SDK walkthrough

Use an authorized Comfy Cloud API key in `.env.local`; never paste keys into prompts, workflow JSON, commits or run records. The helper uses the existing SDK dependency and passes authentication for both Cloud submission and the partner node. It is independent of the existing film app and does not change the app's UI.

```powershell
# Offline inspection, no network or generation:
node scripts/run-opening-reference.mjs prepare ethan anchor ethan-anchor-dry-01

# One paid candidate, after authentication is working:
node --env-file=.env.local scripts/run-opening-reference.mjs submit ethan anchor ethan-anchor-02

# Read status once; if succeeded, save the PNG and its hash:
node --env-file=.env.local scripts/run-opening-reference.mjs collect ethan-anchor-02

# One derived portrait, using the selected actual anchor file:
node --env-file=.env.local scripts/run-opening-reference.mjs submit ethan portrait ethan-portrait-02 assets/ehih-opening/references/runs/ethan-anchor-02/candidate-1.png
node --env-file=.env.local scripts/run-opening-reference.mjs collect ethan-portrait-02
```

`prepare` reserves its run directory but does not submit it later; use a distinct run ID with `submit`. `collect` polls once and never queues another job; call it again after a reasonable interval if queued/running. A timeout while collecting is a reason to collect again, not submit again.

The helper records the authored API graph, prompt, parameters, source graph hash, preset hash, anchor hash, request key and returned job ID. The submitted graph snapshot contains a local reference path; at submission the SDK replaces that LoadImage input with an uploaded asset. It is therefore the pre-materialization request graph, not a claim to be Cloud's executed graph. Where needed, retrieve the latter with `job.getWorkflow()` and retain it separately.

For a failed submission, inspect the record first. `retry-submit <run-id>` is an explicit recovery command that preserves the same graph, image and unexpired request key; duplicate keys can be rejected without returning the first job. It refuses changed inputs, known job IDs and keys approaching expiry. Do not switch to a new run ID to bypass an ambiguous error. If no job ID was returned, inspect Cloud history manually. The [SDK documentation](https://docs.comfy.org/development/api-development/sdks) explains submission and recovery behavior.

## Failure triage

| Symptom | Next action |
|---|---|
| Unauthorized | Replace/re-authorize the local key through the account's normal key management. Never ask another agent to print it. Check the workspace/API entitlement. |
| Login required inside Gemini | Verify partner-node authentication is included with submit, not only the SDK client. |
| LoadImage missing file | Upload/select the intended anchor in Cloud, or supply the actual local path to the helper. |
| Missing node/model | Compare current Cloud template and saved canvas; re-export on Cloud if schema changed. Do not install arbitrary local nodes as a Cloud fix. |
| Wrong face, age, hair, wardrobe | Reject the derivative; confirm the correct anchor hash, simplify the view instruction, retry one candidate. |
| Mirrored wrist or room | Reject it. Explicit anatomical/world directions matter more than apparent screen-left/right. |
| Prompt rejected by provider | Read the actual rejection; these are ordinary nonviolent fictional reference portraits. Do not bypass provider controls. |

## Outputs and the film manifest

[asset-register.json](../../../../../assets/ehih-opening/references/asset-register.json) starts with empty candidate lists and null selected anchors. Fill it from actual run records after inspection. Record who selected and approved each anchor. Preserve original PNGs; don't use an expiring output URL as the only asset record.

The existing shot manifest is an editorial plan, not a finished shot-generation pipeline. Once reference assets are approved, add their real paths, hashes and IDs to its `assets` section, and connect the matching workflow records. Do not fill `first_frame_asset` with a character portrait: that field needs a composed shot keyframe. The next package will combine the selected characters, room angle and action into those keyframes.
