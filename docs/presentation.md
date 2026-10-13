# Presentation: from a ComfyUI workflow to your own app

A 20-minute live tutorial for developers who already use ComfyUI but haven't built on it. It follows [from-workflow-to-app.md](from-workflow-to-app.md) step by step, so viewers can reread any part afterwards.

**The promise (say it in the first minute):** "You have a workflow that works. In 20 minutes you'll see everything it takes to put it behind your own app on Comfy Cloud, and you can clone this repo to do the same."

**The demo rule:** a 3 × 15 s film takes 13–15 minutes. Start a real run in minute 2 and teach while it renders, so it finishes on stage. Keep a pre-rendered film open as a backup.

## Run of show

| Time | Beat | Tutorial step | On screen |
|---|---|---|---|
| 0:00–2:00 | The hook: what we're building | n/a | A finished film plays; Dreams Studio UI |
| 2:00–3:00 | **Start the live run** | n/a | Fill the form, select Make the film, show the job id |
| 3:00–6:00 | Make the workflow Cloud-ready | 1 | `dream_film.json` on the Comfy Cloud canvas |
| 6:00–8:00 | Export it twice | 2 | Save vs Export (API), side by side |
| 8:00–10:00 | Name the inputs | 3 | `npm run inspect`, `dream_film.inputs.json`, `npm test` |
| 10:00–13:00 | Submit from your server | 4 | `lib/comfy.ts` |
| 13:00–16:00 | Poll and read outputs | 5 | Browser network tab, `lib/dream.ts`, the film arriving |
| 16:00–18:30 | Secrets and failures | 6 | `.env.local`, a live failure, `lib/job-error.ts` |
| 18:30–20:00 | Recap and where to go next | n/a | The six steps, the repo, the official docs |

## Beats

### 0:00–2:00: The hook
- Play 15 s of a finished film.
- "One ComfyUI workflow made this: a keyframe, three chained clips and the stitched film. The app around it is a form and about 100 lines that talk to Comfy."
- Show the UI: fields on the left, output on the right.

### 2:00–3:00: Start the live run
- Pick the Skeleton cavern preset, keep 15 s clips, and select **Make the film**.
- Point at the job id and the timer. "This takes about 13 minutes. We'll build the whole thing while it renders."
- It costs about 225 credits. Check the balance before going on stage.

### 3:00–6:00: Step 1, make the workflow Cloud-ready
- Open `dream_film.json` in Comfy Cloud and walk the groups: inputs, keyframe, three clips, stitch.
- **Catalog nodes only.** "Comfy Cloud can't install a custom node pack. My local version used GGUF loaders and two custom nodes; on Cloud they became core nodes and Cloud's int8 model files."
- **Titled primitive nodes** hold everything the app changes. "Code sets a node called Style, not an input buried in a sampler."
- **Derived values live in the graph.** The `a - 1` math node feeds the seam crops from Length.
- **Output nodes go after the switch.** Tell the trap story: Save and Preview ran Nano Banana even when the switch was off, about 13 credits a run that the canvas never showed.

### 6:00–8:00: Step 2, export it twice
- In the menu: **Save** gives `nodes` and `links` (for people); **Export (API)** gives `class_type` and `inputs` keyed by node id (for code).
- "A file I named '… API.json' was still the UI format. Only Export (API) makes the format the API accepts."
- Rule: edit the node workflow, then re-export. Never hand-edit the API file.

### 8:00–10:00: Step 3, name the inputs
- Run `npm run inspect -- workflows/dream_film.api.json` live.
- Show `dream_film.inputs.json`: names to node ids, in one file.
- Run `npm test`: "If a re-export renumbers a node, or the two files drift apart, this fails before you spend a credit."

### 10:00–13:00: Step 4, submit from your server
- Walk `submitFilm` in `lib/comfy.ts`: `new Comfy`, `fromFile`, `setInput`, assets, `submit`.
- **The partner key story:** "The workflow ran fine in the browser. From code, Nano Banana failed with 'Please login first'. The client's key authenticates the call, but a partner node needs the key inside the job too: `submit(wf, { apiKey })`."
- **Skipped branches are still validated,** so Load Image always gets a file.
- `submit` vs `run`: a web request can't wait 15 minutes.

### 13:00–16:00: Step 5, poll and read outputs
- Open the network tab: `GET /api/jobs/<id>` every 5 s.
- Show the seven statuses in `lib/dream.ts`. "If your loop only waits for succeeded or failed, it never ends on canceled or expired."
- Find outputs by node id (`901` is the film), then redirect to the signed URL.
- **If the live run has finished, play it here.** Otherwise switch to the backup film and come back to the live one at the end.

### 16:00–18:30: Step 6, secrets and failures
- `.env.local` and the server routes are the only places that see the key.
- **Live failure (free):** upload a text file renamed to `.png`. It's rejected before a job starts, because `lib/requests.ts` checks the magic bytes.
- **Live failure (free; rehearse it once):** put a wrong key in `.env.local`, restart, and submit. Show the plain-English message from `lib/job-error.ts`, then restore the key.
- `JobFailed` only says "ended failed". The cause is on the job's `error` field.

### 18:30–20:00: Recap and where to go next
- The six steps on one slide.
- "Clone the repo, swap in your workflow, rewrite `dream_film.inputs.json`, and run `npm test`."
- The official docs table at the end of the tutorial.
- Next milestones, as a teaser: show the keyframe as soon as it's ready (the SDK's `outputReady` event), and more to come.

## Before going on stage

1. Credits: at least 500 (one live run plus a retry).
2. `npm run dev` running; the app open at `127.0.0.1:3000`; one form filled in.
3. Comfy Cloud open on `dream_film.json`; the docs site open on the SDK guide.
4. A backup film downloaded and open in a player.
5. A text file renamed to `.png` on the desktop for the failure demo. Have a copy of `.env.local` ready to restore.
