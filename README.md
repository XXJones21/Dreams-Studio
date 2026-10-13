# Dreams Studio

A standalone app that turns a written dream into a short first-person film with sound. One ComfyUI workflow does all of it on Comfy Cloud: Nano Banana draws the opening keyframe (or you upload your own), MiniMax H3 animates three clips in a row, each starting on the last frame of the one before, and the workflow joins them into one film. The app calls it through the [Comfy SDK](https://docs.comfy.org/development/api-development/sdks) for TypeScript (`@comfyorg/sdk`) and runs on Comfy Cloud.

New to building on ComfyUI? Read [Deploying a local ComfyUI workflow as an app](docs/Developer%20Docs/from-workflow-to-app.md). It takes this workflow from a local machine to Comfy Cloud, APP mode, the Comfy API, and this app, with the snags we hit along the way.

## Run locally

### Start with a double-click

1. Install [Node.js 22.6 or newer](https://nodejs.org/).
2. Download this repository (**Code** > **Download ZIP**, then unzip it) or clone it.
3. In the folder, double-click `start-windows.cmd` on Windows or `start-mac.command` on macOS.
4. On the first run, create a [Comfy API key](https://platform.comfy.org/profile/api-keys) for a workspace with credits when the page opens, then paste the key into the window. The key is saved to `.env.local` on your computer, and the packages install.

The app opens at <http://127.0.0.1:3000>. Keep the window open while you use it, and close it to stop the app. Starting the app spends nothing; **Make the film** spends credits.

> **Note:** If macOS says the file can't be opened, right-click `start-mac.command` and select **Open**. If it says you don't have permission, run `chmod +x start-mac.command` in Terminal from the folder, then double-click it again.

### Start from a terminal

1. Install [Node.js 22.6 or newer](https://nodejs.org/) and create a [Comfy API key](https://platform.comfy.org/profile/api-keys) for a workspace with credits.
2. Clone and configure the app:

   ```sh
   git clone https://github.com/XXJones21/Dream-studio.git
   cd Dream-studio
   cp .env.example .env.local
   ```

3. Put your key in `COMFY_API_KEY` in `.env.local`, then install and start:

   ```sh
   npm ci
   npm run dev
   ```

4. Open <http://127.0.0.1:3000>. Start from the **Skeleton cavern** example or a blank form, edit the style, the keyframe scene and the three clip actions, choose a clip length, and select **Make the film**. A 3 × 15 s film takes about 13–15 minutes and uses about 210 credits, plus about 13 when Nano Banana draws the keyframe.

Keep `COMFY_API_KEY` in `.env.local`; only server code reads it (`lib/comfy.ts`, called from the routes in `app/api/`). Do not prefix it with `NEXT_PUBLIC_` or commit the file.

## How it works

`POST /api/dream/film` submits one job: `workflows/dream_film.api.json`, exported from Comfy Cloud with **Export (API)**. `workflows/dream_film.inputs.json` names the node input behind each form field, and `lib/comfy.ts` sets them:

| Form field | Workflow input |
|---|---|
| Style (added to every prompt) | `2001.value` |
| Keyframe scene, Avoid list | `2002.value`, `4452018332049331.value` |
| Clip 1–3 actions | `2003`–`2005.value` |
| Clip length (124, 243 or 362 frames) | `2213.value` |
| Generate keyframe or use your image | `2201.switch`, `8.image` |

Inside the workflow:

1. A switch picks the keyframe: Nano Banana 2.1 (a partner node, 9:16) or your uploaded image.
2. Three MiniMax H3 image-to-video clips run in a row on Comfy Cloud's GPU (int8 model with the 4-step turbo LoRA, 768×1344, 24 fps, with sound). Clip 2 starts on clip 1's last frame, and clip 3 on clip 2's.
3. Clips 2 and 3 drop their repeated first frame. The crop length is the clip length minus 1, worked out by a math node, so any length keeps the seams clean. Then the clips are joined into one film.

The browser polls `GET /api/jobs/<id>` every 5 seconds and keeps the dream in `localStorage`, so a reload picks the running job up again. Films and keyframes are served through the app (`/api/jobs/<id>/outputs/<outputId>`), which redirects to a short-lived signed link. Outputs don't last forever, so download the film to keep it.

Two details in `lib/comfy.ts` are easy to miss:

- **Partner nodes need the key twice.** The client's key authenticates the call. Nano Banana also needs it inside the job, so `submit(wf, { apiKey })` sends it again. Without it the job fails with "Please login first to use this node".
- **Load Image always gets a file,** even when the switch generates the keyframe, because Comfy validates the branch it skips. The app sends `workflows/default-keyframe.png` in that case.

## What's in the repo

| Path | What it is |
|---|---|
| `workflows/dream_film.json` | The node workflow: open it in ComfyUI or Comfy Cloud |
| `workflows/dream_film.api.json` | The same workflow from **Export (API)**: what the app runs |
| `workflows/dream_film.inputs.json` | Which node input each form field sets |
| `workflows/Local/minimax_continuation_krea_workflow.json` | The original local version, kept for comparison: a Krea 2 keyframe, GGUF H3 and two custom nodes (`SeamlessContinuationLastFrame`, `SeamlessContinuationStitch`). It needs the GGUF and custom node packs, so it doesn't run on Comfy Cloud, and the app doesn't use it |
| `lib/comfy.ts` | The only file that talks to Comfy: submit, job status, outputs |
| `lib/requests.ts`, `lib/job-error.ts` | Input checks before a paid job; errors turned into plain sentences |
| `app/api/` | Server routes; the only code that reads the API key |
| `components/dreams.tsx` | The page |
| `start-windows.cmd`, `start-mac.command`, `scripts/launch.ts` | Double-click start: asks for a key on the first run, installs, starts the app and opens the browser |
| `Developer Docs` | [The tutorial](docs/Developer%20Docs/from-workflow-to-app.md): from a local workflow to this app |
| `On-site Docs` | [How the app calls the Comfy API](docs/On-site/how-the-app-works.md), [the live build script](docs/On-site/live-build-script.md) and [the dream prompts](docs/On-site/dream-prompts.md) |
| `Friction log` | [The friction log](docs/friction-log.md): what helped and what got in the way while building this |
| `Prompts` | [Web app prompts](docs/On-site/web-app-prompts.md): A set of prompts to use in your own Claude Code or Codex to configure to your own needs |

## Make a change

- **Change the workflow:** open `workflows/dream_film.json` in Comfy Cloud, edit it, save it back, export it with **Export (API)** over `workflows/dream_film.api.json`, and update `workflows/dream_film.inputs.json` if node ids changed (`npm run inspect -- workflows/dream_film.api.json` lists them). Run `npm test`: it fails if a role points at a node or input that no longer exists, if the two workflow files are wired differently, or if the seam crops stop following the clip length.
- **Add an example:** add a preset to `lib/styles.ts`.

## If a run fails

- **"Add COMFY_API_KEY…":** put the key in `.env.local` and restart `npm run dev`.
- **Out of credits or a rejected key:** check the balance of the workspace that created the key.
- **"A partner node (Nano Banana) rejected the key":** use a key with partner-node access, or switch the keyframe to your own image.
- **The page says "Making the film…" for a long time:** that's normal. The first run loads the models, and a 3 × 15 s film takes about 13–15 minutes. You can close and reopen the page.

### Self-hosting

Set `COMFY_BASE_URL` in `.env.local` to your own ComfyUI (through `comfy-api-proxy`) or a Comfy API deployment. That server needs the MiniMax H3 model files, and Nano Banana still needs a Comfy API key.

## License

MIT. See [`LICENSE`](LICENSE). Model licenses are separate: MiniMax H3 has its own license, including territory limits, and Nano Banana is a Google partner model billed through Comfy.
