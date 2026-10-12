// The only file that talks to Comfy: one film job on Comfy Cloud, then its status and outputs.
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { Comfy, type Job } from "@comfyorg/sdk";
import { CLIP_FRAMES } from "./film.ts";
import type { JobJson } from "./dream.ts";
import { jobErrorMessage } from "./job-error.ts";
import type { FilmRequest } from "./requests.ts";

const WORKFLOWS = join(process.cwd(), "workflows");
const DEFAULT_KEYFRAME = join(WORKFLOWS, "default-keyframe.png");

type Roles = Record<string, string>;
let roles: Roles | undefined;
async function loadRoles(): Promise<Roles> {
  roles ??= JSON.parse(await readFile(join(WORKFLOWS, "dream_film.inputs.json"), "utf8")) as Roles;
  return roles;
}

function apiKey() {
  return process.env.COMFY_API_KEY?.trim() || undefined;
}

function client() {
  const key = apiKey();
  if (!key && !process.env.COMFY_BASE_URL?.trim()) {
    throw new Error("Add COMFY_API_KEY to .env.local and restart the app.");
  }
  return new Comfy({ apiKey: key, clientInfo: "comfy-dreams-studio" });
}

const randomSeed = () => Math.floor(Math.random() * 2 ** 31);

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
  const seeds = { keyframe: randomSeed(), clips: [randomSeed(), randomSeed(), randomSeed()] };
  set("keyframe_seed", seeds.keyframe);
  seeds.clips.forEach((seed, i) => set(`seed${i + 1}`, seed));

  // The client's key authenticates this call. Partner nodes (Nano Banana) need it again inside the job.
  const job = await c.submit(wf, { apiKey: apiKey() });
  return { job: await publicJob(job), seeds };
}

async function publicJob(job: Job): Promise<JobJson> {
  const r = await loadRoles();
  const url = (role: string) => {
    const output = job.outputs.find((o) => o.nodeId === r[role]);
    return output ? `/api/jobs/${job.id}/outputs/${output.id}` : null;
  };
  return {
    id: job.id, status: job.status, error: job.error ? jobErrorMessage(job.error) : null,
    film: url("film"), keyframe: url("keyframe"),
  };
}

export async function getJob(id: string) {
  return publicJob(await client().jobs.get(id));
}

async function findOutput(jobId: string, outputId: string) {
  const job = await client().jobs.get(jobId);
  const output = job.outputs.find((o) => o.id === outputId);
  if (!output) throw new Error("That output is gone. Comfy Cloud keeps outputs for 24 hours; make the film again.");
  return output;
}

/** Comfy Cloud gives a short-lived signed URL; the browser fetches the film from it directly, so video seeking works. */
export async function getOutputLink(jobId: string, outputId: string) {
  const { url, expiresAt } = await (await findOutput(jobId, outputId)).getDownloadUrl();
  return expiresAt ? url : null; // a self-hosted proxy's URL is not signed, so the app serves those bytes itself
}

/** Read an output to the end before answering, so an abandoned browser load never leaves a transfer open. */
export async function getOutput(jobId: string, outputId: string) {
  const output = await findOutput(jobId, outputId);
  return { bytes: await output.toBytes({ timeoutMs: 300_000 }), type: output.contentType || "application/octet-stream", name: output.name };
}
