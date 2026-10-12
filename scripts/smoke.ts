// Paid end-to-end check on Comfy Cloud: one film job, then save the film. Spends credits.
// Usage: npm run smoke -- [5|10|15] [--nano]
//   Clip length defaults to 5 s (the cheapest run). The keyframe is workflows/default-keyframe.png
//   unless --nano asks Nano Banana for a new one (a partner node, ~13 credits).
import { readFileSync, writeFileSync } from "node:fs";
import { getJob, getOutput, submitFilm } from "../lib/comfy.ts";
import { runFromJob } from "../lib/dream.ts";
import { filmSeconds, isClipSeconds } from "../lib/film.ts";
import { PRESETS } from "../lib/styles.ts";

try { process.loadEnvFile(".env.local"); } catch {} // the key can also come from the shell
const seconds = Number(process.argv.find((a) => /^\d+$/.test(a)) ?? 5);
if (!isClipSeconds(seconds)) throw new Error("Clip length must be 5, 10 or 15.");
const nano = process.argv.includes("--nano");
const t0 = Date.now();
const log = (msg: string) => console.log(`[${((Date.now() - t0) / 1000).toFixed(0)} s] ${msg}`);

const p = PRESETS["Skeleton cavern"];
const { job, seeds } = await submitFilm({
  style: p.style, scene: p.scene, avoid: p.avoid, clips: p.clips, clipSeconds: seconds, generateKeyframe: nano,
  image: nano ? undefined : { bytes: new Uint8Array(readFileSync("workflows/default-keyframe.png")), contentType: "image/png", filename: "keyframe.png" },
});
log(`submitted ${job.id}: 3 × ${seconds} s (${filmSeconds(seconds).toFixed(1)} s film), ${nano ? "Nano Banana" : "default"} keyframe, seeds ${JSON.stringify(seeds)}`);

let run = runFromJob(job, t0);
while (run.status === "queued" || run.status === "running") {
  if (Date.now() - t0 > 40 * 60_000) throw new Error(`Gave up after 40 min. The job may still finish: ${job.id} (Runs in Comfy Cloud).`);
  await new Promise((r) => setTimeout(r, 10_000));
  try {
    run = runFromJob(await getJob(job.id), t0);
    log(run.status);
  } catch (e) {
    log(`poll failed, trying again: ${e instanceof Error ? e.message : e}`);
  }
}
if (run.status === "failed") throw new Error(`${job.id}: ${run.error}`);

const film = await getOutput(job.id, run.film!.split("/").pop()!); // run.film is /api/jobs/<id>/outputs/<outputId>
writeFileSync(`smoke-${seconds}s.mp4`, film.bytes);
log(`film saved: smoke-${seconds}s.mp4 (${film.bytes.byteLength} bytes)`);
