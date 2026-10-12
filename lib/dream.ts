// The dream the browser keeps, and how a Comfy job status maps onto it.
import { isClipSeconds, type ClipSeconds } from "./film.ts";

export type Run = {
  jobId: string; status: "queued" | "running" | "done" | "failed"; startedAt: number;
  film?: string; keyframe?: string; error?: string;
};
export type Dream = {
  version: 2; style: string; scene: string; avoid: string; clips: [string, string, string];
  clipSeconds: ClipSeconds; generateKeyframe: boolean; run?: Run;
};
export type JobJson = { id: string; status: string; error: string | null; film: string | null; keyframe: string | null };

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

export const isActive = (run?: Run) => run?.status === "queued" || run?.status === "running";

export const serialize = (d: Dream) => JSON.stringify(d);

export function restore(text: string | null): Dream | null {
  if (!text) return null;
  try {
    const d = JSON.parse(text) as Dream;
    const strings = [d?.style, d?.scene, d?.avoid, ...(Array.isArray(d?.clips) ? d.clips : [])];
    const ok = d?.version === 2 && Array.isArray(d.clips) && d.clips.length === 3 && strings.every((s) => typeof s === "string")
      && isClipSeconds(d.clipSeconds) && typeof d.generateKeyframe === "boolean";
    return ok ? d : null;
  } catch {
    return null;
  }
}
