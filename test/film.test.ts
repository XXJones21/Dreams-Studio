import assert from "node:assert/strict";
import test from "node:test";
import { CLIP_FRAMES, CLIP_SECONDS, filmSeconds, isClipSeconds } from "../lib/film.ts";

test("clip frame counts sit on MiniMax H3's 17k+5 grid, inside its 124–362 range", () => {
  for (const s of CLIP_SECONDS) {
    const frames = CLIP_FRAMES[s];
    assert.equal((frames - 5) % 17, 0, `${s} s`);
    assert.ok(frames >= 124 && frames <= 362, `${s} s`);
  }
});

test("the film keeps each repeated seam frame once", () => {
  assert.equal(filmSeconds(15), (3 * 362 - 2) / 24);
  assert.equal(filmSeconds(5), (3 * 124 - 2) / 24);
});

test("only 5, 10 and 15 s clips are offered", () => {
  assert.equal(isClipSeconds(15), true);
  for (const bad of [0, 7, 20, "15", null]) assert.equal(isClipSeconds(bad), false);
});
