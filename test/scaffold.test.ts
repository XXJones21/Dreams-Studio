import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

test("the example env names the one required secret and no public prefix", () => {
  const env = readFileSync(".env.example", "utf8");
  assert.match(env, /^COMFY_API_KEY=$/m);
  assert.doesNotMatch(env, /NEXT_PUBLIC_/);
});
