# Mini Dreams: the smallest version of the app

The Dreams Studio workflow behind one text box, in four files and about 60 lines. It's the version built by hand in the workshop: a client that submits the workflow, two routes, and a page that polls the job and plays the film. The full app in the repository root adds named inputs, input checks, all the form fields, and error messages.

| File | What it does |
| --- | --- |
| `lib/comfy.ts` | Loads the API format workflow, sets four inputs by node ID, submits, and checks a job |
| `app/api/film/route.ts` | `POST /api/film`: submits a film and returns the job ID |
| `app/api/film/[id]/route.ts` | `GET /api/film/<id>`: returns the job's status and, when it's done, the film's link |
| `app/page.tsx` | A text box, a button, a poll every 5 seconds, and a video player |

To run it:

1. From this folder, install the packages:

   ```sh
   npm install
   ```

2. Create `.env.local` in this folder with your key: `COMFY_API_KEY=YOUR_API_KEY`.
3. Start it, and open `http://127.0.0.1:3000`:

   ```sh
   npm run dev
   ```

> **Important:**
>
> **Make the film** spends credits. This version always makes the low-cost film: three 5 s clips from `workflows/default-keyframe.png`, with Nano Banana switched off.

The page sets only the **Style** node. The other prompts keep the values saved in `workflows/dream_film.api.json`.
