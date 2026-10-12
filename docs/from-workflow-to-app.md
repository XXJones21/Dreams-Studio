# From a ComfyUI workflow to your own app

You already have a workflow that works in ComfyUI. This guide turns it into something your own code can run on Comfy Cloud, using Dreams Studio as the example. Every step points at the file in this repo that does it.

It takes six steps:

1. Make the workflow Cloud-ready.
2. Export it twice.
3. Name the inputs your app will set.
4. Submit a job from your server.
5. Poll the job and read its outputs.
6. Handle secrets and failures.

## 1. Make the workflow Cloud-ready

Comfy Cloud runs a workflow only with the nodes and models in its catalog. It can't install a custom node pack or a model file for you. Open the workflow in Comfy Cloud and run it once there before writing any code. If it runs in the browser, it will run from code.

Three changes make the workflow easier to drive from code. Dreams Studio makes all three (see [workflow.md](workflow.md)):

- **Put each value your app changes in a primitive node with a title.** Dreams Studio keeps its style, keyframe scene and three clip actions in `PrimitiveStringMultiline` nodes, and its clip length in an int node. Then the code sets one obvious node, not an input buried inside a sampler.
- **Compute derived values in the graph.** The seam crops need "clip length − 1". A `ComfyMathExpression` node (`a - 1`) works it out, so the app sets the length once.
- **Put output nodes after any switch.** `ComfySwitchNode` skips the branch it doesn't pick, unless something else needs that branch. Save Image and Preview Image always run, so one of them placed before the switch runs the skipped branch anyway. In Dreams Studio that would bill a Nano Banana keyframe even when you upload your own image. Save keyframe sits after the switch.

## 2. Export it twice

ComfyUI saves a workflow in two formats, and you need both:

| File | How to make it | Who uses it |
|---|---|---|
| `workflows/dream_film.json` | **Save** (the default) | People: open it in ComfyUI or Comfy Cloud to see and edit the graph |
| `workflows/dream_film.api.json` | **Export (API)** | Code: the format Comfy Cloud runs |

The API format is an object keyed by node id, with `class_type` and `inputs` on each node. Comfy Cloud rejects the default format, which has `nodes` and `links` at the top level. Export it; don't write it by hand.

Edit the node workflow and export again rather than editing the API file. `npm test` checks that the two files are wired the same.

## 3. Name the inputs your app will set

The API file refers to nodes only by id. List them:

```sh
npm run inspect -- workflows/dream_film.api.json
```

Then record what each id means in one small file, `workflows/dream_film.inputs.json`:

```json
{ "style": "2001.value", "clip1": "2003.value", "frames": "2213.value", "film": "901", ... }
```

The app code uses names like `style` and `film`, never raw ids. When a re-export renumbers nodes, you change this one file. `npm test` fails if a name points at a node or input that no longer exists.

## 4. Submit a job from your server

`lib/comfy.ts` is the only file that talks to Comfy. These are the core lines:

```ts
import { Comfy } from "@comfyorg/sdk";

const c = new Comfy({ apiKey: process.env.COMFY_API_KEY });  // Comfy Cloud unless COMFY_BASE_URL is set
const wf = await c.workflows.fromFile("workflows/dream_film.api.json");

wf.setInput("2001", "value", style);                      // a text input
wf.setInput("2213", "value", "362");                      // this int node takes its value as text
wf.setInput("8", "image", c.assets.fromBytes(bytes, { filename, contentType }));  // a file input

const job = await c.submit(wf, { apiKey: process.env.COMFY_API_KEY });
```

Two things here are easy to miss:

- **Partner nodes need the key a second time.** The client's key authenticates the API call. A partner node (here Nano Banana) also needs the key inside the job, and `submit(wf, { apiKey })` sends it there. Without it, the job fails with "Please login first to use this node". The same workflow works in the browser because you're logged in there.
- **A skipped branch still gets checked.** Comfy validates Load Image even when the switch generates the keyframe, so the app always sends a real file. With no upload, it sends `workflows/default-keyframe.png`.

`submit` returns right away. `run` submits and then waits for the result, which suits a short script. Dreams Studio uses `submit` and polls the job itself, even in `scripts/smoke.ts`: a film takes about 15 minutes, a web request can't wait that long, and polling yourself lets you retry a single slow poll.

## 5. Poll the job and read its outputs

A 3 × 15 s film takes 13–15 minutes, so the browser polls `GET /api/jobs/<id>` every 5 seconds, and the server calls `c.jobs.get(id)`.

A job has seven statuses: `queued`, `running`, `succeeded`, `canceling`, `canceled`, `failed` and `expired`. Handle all of them. A loop that waits only for "succeeded or failed" never ends on `canceled` or `expired`. `lib/dream.ts` turns them into the four states the UI shows.

Find each output by the node that saved it, not by its position in the list:

```ts
const film = job.outputs.find((o) => o.nodeId === "901");
const { url, expiresAt } = await film.getDownloadUrl();  // signed, expires in about an hour
```

The app redirects the browser to that signed URL, so video seeking works and the bytes never pass through your server. Comfy Cloud keeps outputs for 24 hours. When a link expires, fetch the job again for a fresh one; don't re-run the workflow. To keep a result, save the bytes (`output.toBytes()` or `toFile()`).

## 6. Handle secrets and failures

- **The key stays on the server.** Only the API routes read `COMFY_API_KEY`, from `.env.local`, which git ignores. Never give it a `NEXT_PUBLIC_` prefix.
- **Check input before spending credits.** `lib/requests.ts` checks text lengths, the clip length and the uploaded image (type, size, magic bytes) before any job starts.
- **Turn errors into actions.** `lib/job-error.ts` maps failures to one sentence a person can act on:

| What happened | What the user sees |
|---|---|
| Key missing or rejected | Check `COMFY_API_KEY` and restart |
| Workspace out of credits | Add credits on platform.comfy.org |
| Partner node rejected the key | Use a key with partner access, or upload your own keyframe |
| Node or model missing on the server | Which node or file is missing |

The SDK's `JobFailed` error message only says the job failed. Read the job's `error` field for the node and the cause.

## Where "Deploy to Comfy API" fits

Comfy Cloud's **Deploy to Comfy API** page describes this same path: an API key, the exported workflow, and an SDK call to `https://cloud.comfy.org`. A workflow that uses only catalog nodes needs no build. One with custom nodes or extra models needs a build (`comfy-cli`, `comfy skills show comfy-build`), which gives it its own endpoint. Point the app at a build or at your own ComfyUI with `COMFY_BASE_URL`.
