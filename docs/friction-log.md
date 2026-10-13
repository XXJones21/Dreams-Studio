# Friction log: Dreams Studio

Raw notes, written as things happened while building Dreams Studio on the Comfy SDK. One line per item where possible.

Setup: Windows 11, RTX 4080 16 GB, 32 GB RAM. Local ComfyUI v0.39.0 portable (pinned `7d9e5a04`) for the original workflow. Comfy Cloud (browser UI, APP mode, Comfy Agent, the comfy-cloud MCP) for the Cloud version. `@comfyorg/sdk` 0.4.0 (TypeScript) for the app, `comfy-sdk` 0.4.0 (Python) for scripts. Backend: Comfy Cloud through the Comfy API.

Section 1 is a mix of my handwritten journal notes and my own findings while building. Sections 2 - 7 are items converted into actionable items taken from section 1 and additional details from runs and Agents to tackle as investigation items. 

## 1. Dated log

### 2026-10-10: single continuation workflow rebuilt for Cloud

- Rebuilt the Oct 7 single continuation workflow (Krea 2 keyframe + 3 chained MiniMax H3 clips + stitch) for Comfy Cloud. I had a lot of custom nodes that I installed and created that needed to be replaced. GGUF loaders -> core `UNETLoader`/`CLIPLoader`, `SeamlessContinuationLastFrame` -> core `ImageFromBatch` (batch_index −1 = last frame), `SeamlessContinuationStitch` -> core `VideoTemporalCrop` (drop seam frame) + `ConcatenateVideo`. Every other node, even the turbo LoRA, and both VAEs were already on Cloud.
- App build: the template's demo-specific negative prompt replaced; `canceled`/`expired` status mismatch found in review; `next dev` generated `AGENTS.md` (gitignored).

### 2026-10-10/11: first Cloud runs

- Run 1: H3 length 243 (:10 sec) × 3, crops `{start_frame: 1, length: 242}`. 30.3 s film, 6 min 36 s on Cloud. The door closed and reopened inside one clip (too little action for 10 s).
- Run 2: H3 length 362 (:15 sec) × 3, crops 1/361. 45.2 s film. Seams clean, sleeves consistent, hands hover in frame.
- Tested a few partner-model versions (Flux 2 Max keyframe + 3 × 30 s Seedance 2.5 First-Last-Frame, Minimax H3 partner vs H3 open weights). That was costly. Not doing that again.

### 2026-10-11: APP mode and Comfy Agent

- Turned the workflow into an APP mode form. Width, Height, and Length became shared inputs (Old Unreal Habits), and Length landed in the keyframe's batch size causing OOM issues. I found the issue but I poked Comfy Agent to see if it could solve it. Comfy Agent found it after two wrong diagnoses.
- The canvas went blank with all 62 nodes present; a Windows restart fixed it. Still no idea what happened.

### 2026-10-12: deployed to the Comfy Cloud API

I deployed the workflow from Comfy Cloud. The deploy flow hands you a "Call the Comfy Cloud API from code" page. I had Claude investigate it against `comfy-sdk` 0.5.0 and `@comfyorg/sdk` 0.5.0 (downloaded, not installed) to try and understand why the app pins 0.4.0. This was very confusing tbh. I was just kind of tossed into the developer portal. 

- For a catalog-only workflow, deploying is an API key plus an API format export, with no build. The page covers output lifetime and what each typed error means (`Unauthorized`, `InsufficientCredits`, `QueueFull`, `JobFailed`).
- Custom nodes have a stated path: a build packaged with comfy-cli's `comfy-build` skill gets its own endpoint. Untested.
- The Deploy page and the SDK disagree on `JobFailed`. The page says "Read the message and fix the workflow". In 0.5.0 the message is still `job <id> ended failed`.
- The Deploy page has only a Python snippet. The TypeScript SDK isn't shown.
- The "Comfy Cloud" deployment page looks like a deploy of my workflow, but it's actually weirdly just a shared endpoint. It shows "Deployment URL", "Managed", "Always on", and a Runs tab, but nothing about your workflow is stored there. It was a lot of  "I've deployed it, now what?"
- Easy to send the wrong format. A file saved as "… - API.json" from the canvas was still the save format (`nodes`/`links`); only **Export (API)** produces the format the endpoint accepts.
- Nano Banana 2.1 failed with "Unauthorized: Please login first to use this node" even though the client had a valid key (first API run, job `2486a9d5…`). The client's key only authenticates the call. Partner Nodes (here `GeminiNanoBanana2V2`) need the key again apparently, passed as `submit(wf, api_key=...)`. 
	- That's documented only in the SDK's module docstring, and the cause was visible only through `exc.error`. (set up a PR when confirmed)


Thank you Claude Opus 5.5 and Sulivan (my local fine-tuned Gemma 4) for the following:
- `isTerminal()` and `TERMINAL` exist in `@comfyorg/sdk` 0.5.0 (`dist/sdk/core`) but aren't exported from the package root. The `JobStatus` union is `queued | running | succeeded | canceling | canceled | failed | expired`.
- the deploy page says "Submission is idempotent, so retrying after a network error does not run the workflow twice." The SDK docstring (0.4.0) says each `submit()` mints a fresh idempotency key, so a retry is a new job unless you pass your own `idempotency_key`.

### 2026-10-12: Callouts

- **The two deploy surfaces disagree on workflow format.** The serverless build page accepted the save format by drag and drop; the Comfy Cloud API endpoint rejects it and needs **Export (API)**.
- **Partner Node login: the UI and the API handle it differently.** In the Comfy Cloud UI, Nano Banana raised a "log in" notification. Through the API, it failed the job.
- **An output node upstream of a lazy switch defeats the switch.** Nano Banana fed a Preview Image and a Save Image before the switch. ComfyUI always runs output nodes, so Nano Banana ran, and billed about 13 credits, on every run, including "use my own image" runs. The canvas looks right. 
	- Fix: Save keyframe after the switch. A test in the app now fails if any output node reaches Nano Banana without going through the switch.

### 2026-10-12: docs check while writing the tutorial

- **The deploy page and the docs site disagree on output lifetimes.** The deploy page: outputs kept 24 h, the link dies after about 1 h. The v2 API overview: signed URLs last "approximately 6 hours", and a job's `expires_at` is a placeholder because "the platform has no job retention or garbage-collection policy". The tutorial says "read `expiresAt`" instead of quoting a number.
- **The docs site's SDK guide never mentions the Partner Node key.** `submit(wf, { apiKey })` → `extra_data.api_key_comfy_org` is documented only in the SDK READMEs and the deprecated v1 Cloud page.
- **The SDK guide says `result()` raises `JobFailed` "with the node-level detail".** In `@comfyorg/sdk` 0.4.0 the message is still `job <id> ended failed`.
- **The official examples are stale.** `Comfy-Org/comfy-examples` pins `@comfyorg/sdk ^0.1.8`; the docs say 0.4.0 is current.
- **The frame grid isn't shown anywhere in the UI:** a user picking Total Frames in APP mode can't know 360 is invalid and 362 is right.

## 2. Additional notes before Before Dreams Studio 

Notes from my first pass at the SDK (a Flux still -> LTX video pipeline, then MiniMax H3) that carried into Dreams Studio. Not new friction, just what I already knew going in.

1. **`JobFailed` hides the reason.** The message is only `job <id> ended failed`; the cause (`node_execution_error`, node ID, class, message) is on `exc.error`. Put it in the exception message.
2. **Base URL only from an env var.** `Comfy()` has no `base_url=`; switching local and Cloud means changing the environment.
3. **Chaining jobs needs download + re-upload.** `set_input` takes an uploaded `Asset`, not a finished job's `Output`.
4. **Core PR #16816 broke ComfyUI-GGUF** (`input_act` kwarg) the day it merged. Pinned core to `7d9e5a04`.
5. **The MiniMax H3 license excludes the US,** while Comfy's docs describe commercial licensing through Comfy. Got personal-use authorization from MiniMax.
6. **Switching model families on 32 GB RAM pages to disk** (LTX after H3: 554 s/step vs 26 s/step). Restart between families.
7. **No memory guidance for H3 on 16 GB.**
8. **Low-memory flags made H3 worse;** default flags worked. Most "failures" were my agent's low-memory guard stopping idle jobs.

## 3. SDK feedback shortlist

Short list of what I would call out to investigate 

1. **Partner Nodes need the key twice, and the deploy snippet doesn't say so.** The first API run failed with "Unauthorized: Please login first to use this node" although the client had a valid key (job `2486a9d5…`). Ask: send the client's key with the job by default, or fail at `submit` with an error that names `api_key`. (Oct 12)
2. **`JobFailed` says only `job <id> ended failed`.** The failed node and the cause are only on `.error`, while the deploy page and the SDK guide promise node-level detail in the message. Ask: put `exc.error` in the message. (Oct 6, Oct 12)
3. **Cost visibility.** The same 3 × 15 s film cost about 1,490 credits on the MiniMax H3 Partner Node and 209 on open weights, partly because GPU time billed while the job waited on the partner. No page compares the two, and nothing estimates cost before submit. (Oct 12)
4. **An output node upstream of a lazy switch defeats the switch.** Nano Banana ran, and billed, on every film with the switch off. The canvas looked right. Lazy branches are also still validated, so the unused **Load Image** must name a real file. (Oct 12)
5. **Job statuses aren't discoverable.** `canceled` (one l) and `expired` exist; my code checked `cancelled`, so a canceled job would have polled forever. `isTerminal()` exists in 0.5.0 but isn't exported from the package root. Ask: export it and the status union. (Oct 10, Oct 12)
6. **The docs disagree with each other and with the SDK:** output and link lifetimes, the idempotency claim, and `Comfy-Org/comfy-examples` pinning `@comfyorg/sdk ^0.1.8`. (Oct 12)
7. **From the canvas to the first call:** the Deploy button lands on the platform home page, the shared endpoint looks like a deployment of your workflow, and the build page accepts the save format while the API needs **Export (API)**. (Oct 12)
8. **Quick ones:** the client takes no base-URL argument; MiniMax H3's frame grid isn't shown anywhere; the SDK can't list past jobs, so a history page has to store job IDs itself.

## 4. Hits

- **The workflow runs on Comfy Cloud with catalog nodes only.** My two custom nodes swapped cleanly for core ones: last frame = `ImageFromBatch` (batch_index −1); stitch = `VideoTemporalCrop` (drop the repeated seam frame) + `ConcatenateVideo`. Every model file, the turbo LoRA, and both VAEs were already on Cloud.
- **Run 1 (H3, 3 × 10 s):** 727 frames, 30.3 s, 768×1344, 24 fps, AAC audio. 6 min 36 s on Cloud. Seams clean.
- **Run 2 (H3, 3 × 15 s):** 1,084 frames, 45.2 s. Seams clean.
- **`SaveVideo` embeds the whole prompt and workflow in the MP4** (`prompt` and `workflow` tags). `ffprobe -show_entries format_tags=prompt` recovers the exact lengths, crops, and prompts of any run. Great for debugging and for teaching.
- **Pinning wardrobe in the Style box held across clips.**
- **APP mode shows a Partner Node's price before you run** (about 12.4 credits per Nano Banana keyframe).
- **The MCP's `estimate_credits` priced partner video models per clip** without spending anything.
- **Partner Nodes need no model loaders:** the models, CLIP, VAE, and LoRA group disappears from the graph.
- **Comfy Agent works on the live graph** (Oct 11). It read all 62 nodes and their wiring and fixed the batch_size wiring with a new constant node, once it traced the links.
- **Outputting a catalog-only workflow is incredible** (Oct 12): deploying a catalog-only workflow is an API key plus an API format export, and it explains output lifetime and each typed error.
- **Most of the path is documented, just spread out.** The missing piece is the step before any of it: making your own workflow drivable from code (titled inputs, derived values in the graph, output nodes after switches, a node-ID map that survives re-export).
- **The app ran end to end on Comfy Cloud** (Oct 12): submit from the Next.js app, poll, and play the film through a signed link.

## 5. Snags

- **H3 frame counts sit on a 17k+5 grid at 24 fps,** so "10 s" is 243 frames and "15 s" is 362 (15.08 s). I had to work the grid out; the trained range is about 124 to 362.
- **Chained clips repeat the seam frame.** Clip N+1 starts on clip N's last frame, so clips 2 to 3 need `VideoTemporalCrop` start 1, length N−1. You need the exact frame count to set it.
- **Too little action per clip makes the model fill time by undoing it.** One "open the door" beat in a 10 s clip: the door opened, closed, and reopened. Fix: one beat per 4 to 5 s, each clip ends where the next starts, no reversible actions.
- **Wardrobe drifted between clips** until the sleeves were pinned in the Style box.
- **"My hands enter the lower frame" in the Style box** keeps hands hovering in frame all clip.
- **`widgets_values_named` overrides `widgets_values`** in canvas JSON, so editing one copy left Cloud reading stale values.
- **`https://cloud.comfy.org/#<uuid>` links opened a blank canvas** for MCP-saved workflows; `?share=<id>` links work.
- **A workflow saved through the MCP's file-upload path doesn't show in the Workflows sidebar** (Oct 11). Workaround: drag the JSON file onto the canvas and save it from there.
- **Making the workflow an App let one shared input feed the wrong socket, and the out-of-memory error pointed elsewhere** (Oct 11). Length (362 frames) also got wired into the keyframe's `Empty Latent Image` batch_size, so with "generate keyframe" on, the sampler tried 362 images and ran out of GPU memory. Any INT output fits any INT socket, so nothing flagged it. Fix: a constant batch size of 1.
- **Comfy Cloud canvas showed no nodes** (Oct 11). The workflow had all 62 nodes, but the viewport was blank. A full Windows restart fixed it.
- **Comfy Agent misdiagnosed the out-of-memory error twice before finding it** (Oct 11). First it blamed the 32B text encoder, then a change on Cloud's side. The error's own hint ("did you set batch_size large?") was right; the agent dismissed it because the batch_size widget said 1 and it didn't check the link overriding it.
- **The official LTX-2.5 FLF2V template's negative prompt is demo-specific** ("PNTR" cap, "JUST DO IT" shirt, sniff sounds, "smiling"). Copied as-is, it steers every clip.
- **Cloud template JSON nests nodes under a top-level `graph` key,** unlike an API export.
- **SDK job status spelling:** `canceled` (one l), plus `expired`. My first poll loop checked `cancelled`.
- **`next dev` writes an `AGENTS.md` into the repo.** Gitignored.
- **Partner video costs much more than the open-model graph.** Seedance 2.5 FLF 30 s: about 5,154 credits at 1080p, 2,095 at 720p, 932 on 2.5 Draft 480p.
- **The same film cost ~7x more on the partner node, and the partner run was also billed GPU time while it waited** (Oct 12, from billing). Partner: 3 × 407.34 = 1,222 credits, plus 1,005 GPU-seconds (~267 credits at 0.266/s) while MiniMax did the work. Open H3 int8 with the turbo LoRA: 770 GPU-seconds, 209 credits. The docs list both prices but never compare them, and no page says whether GPU time includes waiting on a partner node.
- **Seedance 2.5 ignores `model.ratio`** (only the 2.0 tiers use it); the aspect ratio follows the first frame.
- **Local baseline:** on the RTX 4080 16 GB, H3's 32B text encoder didn't fit in memory, so one GGUF clip took about 19 minutes.
- **Self-hosted only:** streaming an output straight to the browser through `comfy-api-proxy` left transfers open when the browser gave up; the app reads the output to the end before answering.

## 6. Asks for the SDK, API, and platform

1. Export the job status union and an `isTerminal()` helper.
2. Send the client's key with the job for Partner Nodes by default, or fail at `submit` with an error that names `api_key`.
3. Put the failed node and cause in the `JobFailed` message.
4. Show valid frame counts (or snap and display seconds) on video nodes with a frame grid.
5. One source of truth for widget values in canvas JSON.
6. Keep demo-specific text out of template defaults.
7. Show estimated credits before Run, on the canvas and through the API.
8. Don't bill GPU-seconds while a job only waits on a partner node, or document that it does. Where an open-weights twin runs on Cloud, show both costs side by side.
9. App mode: when one shared input fans out, show every socket it feeds, and warn when a value lands somewhere unexpected.
10. The canvas could mark nodes that will run no matter what a lazy switch picks.
11. Comfy Agent: trace linked inputs before diagnosing from widget values.
12. One number for output and link lifetimes, in one place.
13. Point **Deploy to Comfy API** at the Deploy page, and say on it that the endpoint runs any workflow you send.
14. A way to list past jobs.

