import assert from "node:assert/strict";
import test from "node:test";
import { jobErrorMessage } from "../lib/job-error.ts";

test("credits and keys get plain messages", () => {
  assert.match(jobErrorMessage({ code: "insufficient_credits", message: "x" }), /out of Comfy credits/);
  assert.match(jobErrorMessage({ code: "unauthorized", message: "x" }), /COMFY_API_KEY/);
});

test("a missing node or model is named", () => {
  assert.match(jobErrorMessage({ message: "Node 'LTXVAddGuide' not found" }), /LTXVAddGuide/);
  assert.match(jobErrorMessage("unet_name: 'ltx-2.5-x.safetensors' not in []"), /ltx-2\.5-x\.safetensors/);
});

test("anything else passes through; nothing gives a fallback", () => {
  assert.equal(jobErrorMessage({ message: "CUDA out of memory" }), "CUDA out of memory");
  assert.match(jobErrorMessage(undefined), /could not run/);
});
