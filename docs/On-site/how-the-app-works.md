# How Dreams Studio calls the Comfy API

How the Dreams Studio app names its workflow inputs, submits and polls a job, reads outputs by node ID, and keeps the API key on the server. It picks up where [Deploying a local ComfyUI workflow as an app](../Developer%20Docs/from-workflow-to-app.md) ends, with the app running.

## Name the inputs

The API format refers to nodes only by node ID. To list them, run:

```sh
npm run inspect -- workflows/dream_film.api.json
```

Each line shows a node ID, the node type, and the literal values of its inputs. An excerpt (the full list has 53 nodes):

```
    8 LoadImage                      image="4f9802c96f741ef8fceea7135cc0d7eea3398052dd46d2f8ce92647586bf545e.png"
  901 SaveVideo                      filename_prefix="dreams/film"  format="auto"  format.codec="auto"  codec="auto"
 2201 ComfySwitchNode                switch=true
 2213 Basic data handling: IntCreate value="362"
```

Record what each node ID means in one small file, `workflows/dream_film.inputs.json`. Each entry gives a name (a role) to one input or output. An input is `node.input`, and an output is the node ID alone:

```json
{
 "style": "2001.value",
 "keyframe_scene": "2002.value",
 "avoid": "4452018332049331.value",
 "clip1": "2003.value",
 "clip2": "2004.value",
 "clip3": "2005.value",
 "frames": "2213.value",
 "generate_keyframe": "2201.switch",
 "keyframe_image": "8.image",
 "keyframe_seed": "4452018332049330.seed",
 "seed1": "102.noise_seed",
 "seed2": "202.noise_seed",
 "seed3": "302.noise_seed",
 "film": "901",
 "keyframe": "4452018332049327"
}
```

The app code uses names like `style` and `film`, never raw node IDs. When a new export renumbers a node, you change this one file. `npm test` (`test/workflows.test.ts`) fails when:

- A name points at a node or input that no longer exists.
- The two workflow files are wired differently.
- The seam crops stop following the length minus 1.
- An output node can reach Nano Banana without going through the switch.
- The API format file contains save format keys.

## Submit a job

`lib/comfy.ts` creates the client, loads the export, sets each named input, and submits (trimmed). `apiKey()` reads `COMFY_API_KEY`, and `loadRoles()` reads `workflows/dream_film.inputs.json`:

```ts
import { Comfy, type Job } from "@comfyorg/sdk";

function client() {
  const key = apiKey();
  if (!key && !process.env.COMFY_BASE_URL?.trim()) {
    throw new Error("Add COMFY_API_KEY to .env.local and restart the app.");
  }
  return new Comfy({ apiKey: key, clientInfo: "comfy-dreams-studio" });
}

export async function submitFilm(input: FilmRequest) {
  const c = client();
  const r = await loadRoles();
  const wf = await c.workflows.fromFile(join(WORKFLOWS, "dream_film.api.json"));
  const set = (role: string, value: unknown) => {
    const [node, ...field] = r[role].split(".");
    wf.setInput(node, field.join("."), value);
  };

  set("style", input.style);
  set("keyframe_scene", input.scene);
  set("avoid", input.avoid);
  input.clips.forEach((action, i) => set(`clip${i + 1}`, action));
  set("frames", String(CLIP_FRAMES[input.clipSeconds])); // the workflow's Length node takes text
  set("generate_keyframe", input.generateKeyframe);
  // Load Image is validated even when the switch skips it, so it always gets a real file.
  set("keyframe_image", input.image
    ? c.assets.fromBytes(input.image.bytes, { filename: input.image.filename, contentType: input.image.contentType })
    : c.assets.fromFile(DEFAULT_KEYFRAME));
  // …sets a random seed for the keyframe and each clip

  // The client's key authenticates this call. Partner nodes (Nano Banana) need it again inside the job.
  const job = await c.submit(wf, { apiKey: apiKey() });
  return { job: await publicJob(job), seeds };
}
```

- **The frame grid lives in code.** `lib/film.ts` holds `CLIP_FRAMES = { 5: 124, 10: 243, 15: 362 }`, so the form offers seconds and the app sends frames (see [Choose the inputs for the form](../Developer%20Docs/from-workflow-to-app.md#choose-the-inputs-for-the-form)).
- **Uploads are assets.** `c.assets.fromBytes` and `c.assets.fromFile` create an asset handle that you set like any other input. Handles are content-addressed, so the same file doesn't upload twice.
- **Use `submit`, not `run`.** `submit` returns at once with a job ID. `run` waits for the result, and a film takes several minutes, longer than a web request can wait.

## Poll the job

The browser polls `GET /api/jobs/<id>` every 5 seconds, and the server calls `client().jobs.get(id)`. A job has seven statuses: `queued`, `running`, `succeeded`, `canceling`, `canceled`, `failed`, and `expired`. Four of them are final: `succeeded`, `failed`, `canceled`, and `expired`. Handle all of them: a loop that waits only for `succeeded` or `failed` never ends on `canceled` or `expired`. `lib/dream.ts` maps the seven statuses to the four states the UI shows:

```ts
/** The SDK's job statuses: queued, running, succeeded, canceling, canceled, failed, expired. */
export function runFromJob(job: JobJson, startedAt: number): Run {
  const base = { jobId: job.id, startedAt };
  switch (job.status) {
    case "succeeded":
      return job.film
        ? { ...base, status: "done", film: job.film, keyframe: job.keyframe ?? undefined }
        : { ...base, status: "failed", error: "The job finished without a film." };
    case "failed":
      return { ...base, status: "failed", error: job.error ?? "The job failed." };
    case "canceled":
      return { ...base, status: "failed", error: "The job was canceled." };
    case "expired":
      return { ...base, status: "failed", error: "The job expired before it finished. Make the film again." };
    case "running":
    case "canceling":
      return { ...base, status: "running" };
    default:
      return { ...base, status: "queued" };
  }
}
```

The browser keeps the form and its job ID in `localStorage`, so a reload picks up the running job.

## Read outputs by node ID

Find each output by the node that saved it, not by its position in the list. Here `r` is the roles map from `workflows/dream_film.inputs.json`, and `role` is a name such as `film`:

```ts
const output = job.outputs.find((o) => o.nodeId === r[role]);   // r.film is "901"
```

When the browser asks for the film, the server gets a fresh signed URL and redirects to it. Video seeking works, and the bytes never pass through your server:

```ts
export async function getOutputLink(jobId: string, outputId: string) {
  const { url, expiresAt } = await (await findOutput(jobId, outputId)).getDownloadUrl();
  return expiresAt ? url : null; // a self-hosted proxy's URL is not signed, so the app serves those bytes itself
}
```

Read `expiresAt` instead of assuming how long a link lasts. When a link expires, fetch the job again for a fresh link instead of running the workflow again. Save the bytes (`output.toBytes()` or `toFile()`) of anything you need to keep.

## Handle secrets and failures

- **Keep the key on the server.** Only server code reads `COMFY_API_KEY` (`lib/comfy.ts`, called from the routes in `app/api/`), from `.env.local`, which git ignores. Never give the key a `NEXT_PUBLIC_` prefix, because Next.js sends variables with that prefix to the browser.
- **Check input before you spend credits.** `lib/requests.ts` checks text lengths, the clip length, and any uploaded image before a job starts. An image must be PNG, JPEG, or WebP, under 10 MB, and its first bytes must match its type. A bad request gets a 400 response and never reaches Comfy.
- **Turn errors into actions.** `lib/job-error.ts` maps each failure to one sentence a person can act on:

| What happened | What the user sees |
| --- | --- |
| `unauthorized` | Comfy rejected the key: check `COMFY_API_KEY` and restart |
| `insufficient_credits` | The workspace is out of credits: add credits on platform.comfy.org |
| `Please login first to use this node` | The Partner Node rejected the key: use a key with Partner Node access, or upload your own keyframe |
| A node or model file missing on the server | Which node or model file is missing |
