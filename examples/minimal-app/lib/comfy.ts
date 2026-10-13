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

export async function checkFilm(id: string) {
  const job = await new Comfy({ apiKey }).jobs.get(id);
  const film = job.outputs.find((o) => o.nodeId === "901"); // Save film
  const url = film ? (await film.getDownloadUrl()).url : null;
  return { status: job.status, error: job.error, url };
}
