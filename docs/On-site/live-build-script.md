# Live build: Mini Dreams (Stage 4, about 8 minutes)

Build the app by hand on the MacBook: four files, about 60 lines. The finished version is `examples/minimal-app/` in the repo. The full Dreams Studio is the "here's where it goes" reveal afterwards.

## Prep on my Macbook

1. Pull the repo, then:

   ```sh
   cd Dream-studio/examples/minimal-app
   npm install
   echo "COMFY_API_KEY=YOUR_API_KEY" > .env.local     # use the real key
   npm run dev                                       # once, to check it starts; then Ctrl+C
   ```

2. Save the finished files as the fallback, then empty the starter:

   ```sh
   mkdir -p ~/mini-done && cp -R lib app ~/mini-done/
   rm -rf lib app/api app/page.tsx                   # keeps app/layout.tsx
   ```

3. In VS Code, open the `examples/minimal-app` folder. Font size up (Cmd +) twice. Terminal panel open.
4. Fallback at any point: `cp -R ~/mini-done/* .` restores the finished files.

## Live session

Slides at: https://docs.google.com/presentation/d/1VbbFcxgS1_tj6VrpvljRo_DYt8Oj3kPic2rJUEjJv-Y/edit?usp=sharing

### 1. `lib/comfy.ts`: the whole SDK story (3 min)

Type `makeFilm` first.

```ts
import { join } from "node:path";
import { Comfy } from "@comfyorg/sdk";

const WORKFLOWS = join(process.cwd(), "..", "..", "workflows");
const apiKey = process.env.COMFY_API_KEY;

export async function makeFilm(style: string) {
  const comfy = new Comfy({ apiKey });
  const wf = await comfy.workflows.fromFile(join(WORKFLOWS, "dream_film.api.json"));

  wf.setInput("2001", "value", style); // Style
  wf.setInput("2213", "value", "124"); // Length: 5 s clips
  wf.setInput("2201", "switch", false); // use Load Image, skip Nano Banana
  wf.setInput("8", "image", comfy.assets.fromFile(join(WORKFLOWS, "default-keyframe.png")));

  const job = await comfy.submit(wf, { apiKey }); // the key again, for Partner Nodes
  return job.id;
}
```

Then `checkFilm`:

```ts
export async function checkFilm(id: string) {
  const job = await new Comfy({ apiKey }).jobs.get(id);
  const film = job.outputs.find((o) => o.nodeId === "901"); // Save film
  const url = film ? (await film.getDownloadUrl()).url : null;
  return { status: job.status, error: job.error, url };
}
```

Find the output by the node that saved it, 901, not by position. The download URL is a signed link, so the browser plays the film straight from Comfy.

### 2. Two routes (1.5 min)

`app/api/film/route.ts`:

```ts
import { makeFilm } from "../../../lib/comfy";

export async function POST(request: Request) {
  const { style } = await request.json();
  return Response.json({ id: await makeFilm(style) });
}
```

`app/api/film/[id]/route.ts`:

```ts
import { checkFilm } from "../../../../lib/comfy";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return Response.json(await checkFilm(id));
}
```

The browser never talks to Comfy. It talks to these two routes, and only server code ever sees the key.

### 3. `app/page.tsx` (2.5 min)

```tsx
"use client";
import { useState } from "react";

const FINAL = ["succeeded", "failed", "canceled", "expired"];

export default function Page() {
  const [style, setStyle] = useState("");
  const [status, setStatus] = useState("");
  const [url, setUrl] = useState<string | null>(null);

  async function make() {
    setUrl(null);
    setStatus("submitting");
    const res = await fetch("/api/film", { method: "POST", body: JSON.stringify({ style }) });
    const { id } = await res.json();

    while (true) {
      const job = await (await fetch(`/api/film/${id}`)).json();
      setStatus(job.status);
      if (FINAL.includes(job.status)) return setUrl(job.url);
      await new Promise((r) => setTimeout(r, 5000));
    }
  }

  return (
    <main>
      <h1>Mini Dreams</h1>
      <textarea rows={4} cols={60} value={style} onChange={(e) => setStyle(e.target.value)} />
      <p><button onClick={make}>Make the film</button> {status}</p>
      {url && <video src={url} controls autoPlay width={360} />}
    </main>
  );
}
```

Four final statuses, not two. If you only wait for succeeded or failed, a canceled job polls forever. Ask me how I know. It's not fun

### 4. Run it (1 min)

1. `npm run dev`, open `127.0.0.1:3000`.
2. Type a style, select **Make the film**.
3. Open the network tab: `POST /api/film`, then `GET /api/film/<id>` every 5 seconds, status `queued` then `running`.

That's a real job on Comfy Cloud. It finishes in a few minutes, so let's look at the film we started at the beginning, in the full app.

## If something breaks

- **Typo or build error:** read the error out loud, fix it. If it takes more than 30 seconds, `cp -R ~/mini-done/* .`
- **`unauthorized`:** the key isn't in `.env.local`, or the dev server started before you added it. Restart `npm run dev`.
- **The job fails:** open `GET /api/film/<id>` in the network tab and read `error` out loud. That's the stream move.
- **Wifi dies:** switch to the backup film and the finished-app walkthrough. Mention Moonlight to the desktop only if it's quick.

## Full app example

Open the root app's code and point at four things the 60-line version skips:

1. `workflows/dream_film.inputs.json`: names instead of raw node IDs, so a re-export only changes one file.
2. `lib/requests.ts`: input checks before a paid job.
3. `lib/dream.ts`: all seven statuses mapped to what the page shows.
4. `lib/job-error.ts`: each failure as a sentence a user can act on.
