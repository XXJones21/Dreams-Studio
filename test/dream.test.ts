import assert from "node:assert/strict";
import test from "node:test";
import { isActive, restore, runFromJob, serialize, type Dream, type JobJson } from "../lib/dream.ts";

const job = (status: string, extra: Partial<JobJson> = {}): JobJson => ({ id: "j", status, error: null, film: null, keyframe: null, ...extra });

test("every SDK job status maps onto four simple states", () => {
  assert.equal(runFromJob(job("queued"), 0).status, "queued");
  assert.equal(runFromJob(job("running"), 0).status, "running");
  assert.equal(runFromJob(job("canceling"), 0).status, "running");
  const done = runFromJob(job("succeeded", { film: "/f", keyframe: "/k" }), 0);
  assert.deepEqual([done.status, done.film, done.keyframe], ["done", "/f", "/k"]);
  assert.equal(runFromJob(job("failed", { error: "boom" }), 0).error, "boom");
});

test("canceled and expired jobs stop the polling (one l in canceled)", () => {
  for (const status of ["canceled", "expired"]) {
    const run = runFromJob(job(status), 0);
    assert.equal(run.status, "failed", status);
    assert.equal(isActive(run), false, status);
  }
});

test("a finished job without a film is a failure, not a blank player", () => {
  assert.equal(runFromJob(job("succeeded"), 0).status, "failed");
});

test("a dream survives a reload; old or broken ones do not crash", () => {
  const d: Dream = { version: 2, style: "s", scene: "k", avoid: "", clips: ["a", "b", "c"], clipSeconds: 15, generateKeyframe: true,
    run: { jobId: "j", status: "running", startedAt: 1 } };
  assert.deepEqual(restore(serialize(d)), d);
  assert.equal(restore(null), null);
  assert.equal(restore("{not json"), null);
  assert.equal(restore(JSON.stringify({ version: 1, cards: [], clips: [] })), null, "the old multi-job dream");
  assert.equal(restore(JSON.stringify({ ...d, style: 5 })), null, "a corrupt field");
  assert.equal(restore(JSON.stringify({ ...d, clipSeconds: 20 })), null, "a clip length the app no longer offers");
});
