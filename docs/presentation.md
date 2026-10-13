# From local ComfyUI to a deployed app

Slides and script for a 20-minute workshop for developers who already use ComfyUI but haven't built on it. It follows [from-workflow-to-app.md](from-workflow-to-app.md), the written version of the same four stages, so viewers can reread any part afterwards.

How this file is laid out:
- Slides are separated by `---`.
- Everything above **Script** goes on the slide.
- **Script** is the speaker notes: what to say and do.
- `[IMAGE: …]` marks where a screenshot goes.

| Time | Section |
|---|---|
| 0:00–2:00 | Intro: what we're taking from local to deployed |
| 2:00–7:00 | Stage 1: Bring the workflow to Comfy Cloud |
| 7:00–10:00 | Stage 2: Establish the app in App Mode |
| 10:00–14:00 | Stage 3: Deploy to the Comfy API |
| 14:00–19:00 | Stage 4: Build a standalone app around it |
| 19:00–20:00 | Recap |

---

## 1. Today: local workflow → deployed app (0:00)

[IMAGE: the local workflow on the canvas, next to a frame of a finished film]

**The workflow:** a short first-person film with sound, from text
- A keyframe image from a written scene
- Three MiniMax H3 video clips, each starting on the last frame of the one before
- One stitched 45-second film

**What we'll do with it:**
1. Bring it to Comfy Cloud
2. Establish the app in App Mode
3. Deploy it to the Comfy API
4. Build a standalone app around it

**Script:** "Today we take one ComfyUI workflow from my machine to a deployed app, and I'll show you every snag I hit on the way. Here's the workflow: you write a scene, it makes a keyframe, then three video clips that each pick up on the last frame of the one before, and it stitches them into one film with sound. It started as a local workflow with a Krea 2 keyframe, a GGUF build of MiniMax H3 and two custom nodes I wrote. We'll move it in four stages, and by the end you'll have the pattern to do the same with your own workflow. The repo is public, so you can follow along."

**Do:** Start a film in the finished app now (about 225 credits, 13–15 minutes), so it arrives during stage 4. "That's where we're headed. Let's go back to the start."

---

## Stage 1: Bring the workflow to Comfy Cloud

---

## 2. Why move it at all (2:00)

- Local: a 16 GB GPU, GGUF models
- MiniMax H3's text encoder is **32B**: it doesn't fit
- One clip took **19 minutes**; the first clip of a sequence took **41**

**Script:** "Locally, it worked, slowly. The model itself was fast. The text encoder alone is 32 billion parameters, and my PC spent most of the time moving it in and out of memory. That's where Cloud stopped being optional. The question is what has to change."

---

## 3. Snag: Cloud runs catalog nodes only (2:45)

[IMAGE: the "Join the waitlist" dialog when adding a custom node on Comfy Cloud]

| Local | Comfy Cloud |
|---|---|
| GGUF loaders (custom pack) | Core `UNETLoader` / `CLIPLoader` + Cloud's int8 files |
| My `LastFrame` node | Core `ImageFromBatch`, index −1 |
| My `Stitch` node | Core `VideoTemporalCrop` + `ConcatenateVideo` |

**Script:** "Comfy Cloud can't install custom node packs yet. Try it and you get a waitlist. So step one is an audit: for each custom node, find a core or catalog equivalent. Mine all had one, and every model file was already on Cloud. If a node has no equivalent, you need a build with its own endpoint, which is a different path I'll point to at the end."

---

## 4. Choice: partner node or open weights? (3:45)

Same model, same 3 × 15 s film:

| | MiniMax H3 partner node | Open H3 on Cloud's GPU |
|---|---|---|
| Model | ~1,222 credits | n/a |
| GPU time | ~267 credits (billed while it waited) | ~209 credits |
| **Total** | **~1,490 credits (~$7)** | **~209 credits (~$1)** |

Keyframe: Nano Banana (partner), about 13 credits.

**Script:** "On Cloud, some models exist twice: as a partner node that calls the provider's API, and as open weights on Cloud's own GPUs. I ran the same film both ways. The partner run was about seven times more expensive, and it was also billed GPU time while it sat waiting on the partner. Nothing in the docs compares the two. So check both prices. I kept the open model for video and a partner node only for the keyframe, where it's cheap and much better."

---

## 5. Confirm it works on Cloud (5:00)

[IMAGE: the Cloud canvas with groups: Prompts, Video settings, Generate Keyframe, Clip 1–3, Stitch]

- Run it once in the browser before writing any code
- Check the seams: clip 2 repeats clip 1's last frame → crop it
- H3 lengths sit on a **17k + 5** frame grid: 124 / 243 / 362 frames for 5 / 10 / 15 s
- First Cloud film: **3 × 10 s in 6 min 36 s**

**Script:** "Before any code, run it in the browser. If it runs there, it'll run from code. Two things I had to discover: chained clips repeat the seam frame, so each later clip drops its first frame. And H3 only takes certain frame counts, 17 times something plus 5, which isn't shown anywhere. I worked out the grid by hand."

**Friction to mention in passing:** the canvas JSON stores widget values twice (`widgets_values_named` wins), and one canvas went blank until a restart.

---

## Stage 2: Establish the app in App Mode

---

## 6. App Mode: a UI before writing one (7:00)

[IMAGE: Comfy Cloud App Mode with Style, Generate Keyframe toggle, Keyframe Prompt, Avoid, Input Image, Width/Height, Total Frames, clip actions, Run]

- Pick which inputs a user sees; Comfy Cloud makes the form
- Shows the partner-node price (~12.4 credits per keyframe) before you run
- A cheap way to test the logic before building anything

**Script:** "Before building my own app, I used Comfy Cloud's App Mode. You choose the inputs, and it gives you a form like this. It's a prototype for free: it makes you decide what a user should touch. And because people actually use it, it shows you where the logic breaks."

---

## 7. Decide what's user-facing (8:00)

| In the graph | App Mode | Standalone app |
|---|---|---|
| Style, keyframe scene, Avoid, clip actions | Text boxes | Text boxes |
| Keyframe switch + Load Image | Toggle + image | Generate / My image |
| Width, Height | Exposed | Fixed at 768 × 1344 |
| Total Frames | A free number | **5 / 10 / 15 s** (124 / 243 / 362) |

**Script:** "App Mode exposed everything I wired up, including Width, Height and raw frame counts. A user can't know that H3 wants 362 and not 360. So the standalone app keeps the size fixed and turns frames into three choices on the grid. That's the main design lesson of this stage: put only real choices in front of the user, and do the math for them."

---

## 8. Snag: one shared input, wrong socket (9:00)

- Width, Height and Length became shared inputs for the keyframe and all three clips
- Length (362) was also wired into the keyframe's **batch size** → 362 images → out of GPU memory
- Any INT fits any INT socket, so nothing flagged it
- Comfy Agent found it, after blaming the text encoder and then Cloud

**Script:** "Making it an app caused a real bug. I shared Length across nodes, and it landed in the keyframe's batch size too. Turn on 'generate keyframe' and it asked for 362 images. The error even hinted at it, 'did you set batch_size large?', but the widget said 1, because the link overrides the widget. Comfy's agent found it once it traced the links. The lesson for people and agents alike: trace the links, don't trust the widgets."

**Also from this stage:** the switch trap. Save and Preview nodes placed before a switch ran Nano Banana even with the switch off, about 13 credits a run that the canvas never showed. Output nodes go after the switch.

---

## Stage 3: Deploy to the Comfy API

---

## 9. "Deploy to Comfy API" (10:00)

[IMAGE: the Call the Comfy Cloud API from code page]

1. Create an API key (platform.comfy.org)
2. **Export (API)** the workflow
3. Call `https://cloud.comfy.org` with the SDK

No build needed when the workflow uses only catalog nodes.

**Script:** "Here's what surprised me: 'deploying' a catalog-only workflow doesn't upload it anywhere. The deployment page shows a URL, 'Managed', 'Always on', but it's the shared Comfy Cloud endpoint. Your code sends the whole workflow with every call. So deploying is an API key plus an export."

**Friction:** the Deploy button landed on the platform home page with no next step; I found Comfy API → Deploy in the menu myself.

---

## 10. Export it twice (11:00)

The same Length node in both formats:

**Save** (for people)
```json
{ "id": 2213, "type": "Basic data handling: IntCreate", "title": "Length",
  "pos": [396.6, 12.4], "size": [270, 58],
  "outputs": [{ "name": "INT", "type": "INT", "links": [ ... ] }],
  "widgets_values": ["362"] }
```

**Export (API)** (for code)
```json
"2213": { "class_type": "Basic data handling: IntCreate",
          "_meta": { "title": "Length" }, "inputs": { "value": "362" } }
```

**Script:** "The default Save is for people: positions, sizes, links. Export (API) is for code: node ids, classes and inputs. The endpoint rejects the first. I had a file named '… API.json' that was still the UI format, because the name doesn't matter. The deploy page I dropped a workflow onto accepted the UI format, and the API didn't, which made it more confusing. Rule: edit the node workflow, then re-export."

---

## 11. Bridging the gap with an agent (12:00)

- The deploy page has **Copy for agents**
- I pasted it into Claude Code with my export; it wrote the first run script
- First run failed: `Unauthorized: Please login first to use this node`

```python
client.submit(wf, api_key=os.environ["COMFY_API_KEY"])  # the key, a second time
```

**Script:** "The deploy page has a button to copy its instructions for an AI agent, so I did that and had Claude Code write the first script. It ran, and the keyframe node failed: 'Please login first'. In the browser I'm logged in. From code, the client's key authenticates the API call, but a partner node needs the key inside the job too. The fix is one argument. The docs site's SDK guide doesn't mention it; it's in the SDK README. And the error only said 'ended failed'. The real cause was on the job's `error` field."

---

## Stage 4: Build a standalone app

---

## 12. The wrapper (14:00)

[IMAGE: the Dreams Studio UI, form on the left, film on the right]

- Next.js + `@comfyorg/sdk`; the key stays on the server
- One file talks to Comfy: `lib/comfy.ts`
- One file names the inputs: `workflows/dream_film.inputs.json`

```json
{ "style": "2001.value", "clip1": "2003.value", "frames": "2213.value",
  "generate_keyframe": "2201.switch", "keyframe_image": "8.image", "film": "901" }
```

**Script:** "The standalone app is a thin wrapper. The API file knows nodes only by id, so I name them once in a small file, and my code says 'style', never 2001. When a re-export renumbers a node, I change one line, and the tests tell me if I missed one."

---

## 13. Submit (15:00)

```ts
const c = new Comfy({ apiKey: process.env.COMFY_API_KEY });
const wf = await c.workflows.fromFile("workflows/dream_film.api.json");

wf.setInput("2001", "value", style);
wf.setInput("2213", "value", "362");
wf.setInput("8", "image", c.assets.fromBytes(bytes, { filename, contentType }));

const job = await c.submit(wf, { apiKey: process.env.COMFY_API_KEY });
```

**Script:** "Make a client, load the export, set inputs, submit. Uploads go in as assets. `submit` returns at once, which you want in a web app; a film takes 15 minutes. One more trap: Comfy validates Load Image even when the switch skips it, so the app always sends a file."

---

## 14. Poll and read outputs (16:00)

```ts
// queued | running | succeeded | canceling | canceled | failed | expired
const job = await c.jobs.get(id);
const film = job.outputs.find((o) => o.nodeId === "901");
const { url, expiresAt } = await film.getDownloadUrl();
```

**Script:** "The browser asks my server every 5 seconds, and my server asks Comfy. There are seven statuses, so a loop that only waits for succeeded or failed never ends on canceled. Find outputs by the node that saved them, and read `expiresAt` rather than guessing how long the link lasts: Comfy's own pages say one hour in one place and six in another."

**Do:** Open the network tab. If the live film is done, play it here. If not, play the backup and come back at the end.

---

## 15. Secrets and failures (17:30)

- The key lives in `.env.local`; only server routes read it
- Inputs are checked **before** a paid job starts
- Every failure becomes one sentence a person can act on

**Script:** "Treat it like any app with a paid backend. The key never reaches the browser. Bad input gets rejected before it costs credits. And errors get translated: out of credits, bad key, partner node rejected, missing node."

**Do (free):** Switch the keyframe to My image and upload a text file renamed to `.png`. The app rejects it before any job starts.

---

## 16. Recap (19:00)

1. **Cloud:** catalog nodes only; compare partner and open-weights prices; run it in the browser first
2. **App Mode:** decide what's user-facing; trace the links
3. **Deploy:** an API key plus Export (API); partner nodes need the key in the job
4. **Standalone:** name your inputs, submit, poll, read outputs by node

Repo: `[your GitHub URL]` · Docs: Quickstart · SDK guide · Workflow API format · API reference v2

**Script:** End on the film rendered during the talk. "Clone it, swap in your workflow, rename the inputs, run the tests." Then drop the presenter voice for the SDK feedback (kept separately).

---

## Before going on stage

1. Credits: at least 500 (one live run plus a retry).
2. `npm run dev` running; the app open at `127.0.0.1:3000` with the form filled in.
3. Comfy Cloud open on `dream_film.json` and on App Mode; the docs site open on the SDK guide.
4. A backup film downloaded and open in a player.
5. A text file renamed to `.png` on the desktop.
