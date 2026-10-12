import assert from "node:assert/strict";
import test from "node:test";
import { parseFilm, parseJobId, RequestError } from "../lib/requests.ts";

const PNG = `data:image/png;base64,${Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).toString("base64")}`;
const good = { style: "s", scene: "a cave", avoid: "", clips: ["a", "b", "c"], clipSeconds: 15, generateKeyframe: true };

test("a good request passes and is trimmed", () => {
  const r = parseFilm({ ...good, style: "  s  " });
  assert.equal(r.style, "s");
  assert.equal(r.image, undefined);
});

test("only 5, 10 and 15 s clips are accepted", () => {
  for (const clipSeconds of [0, 7, 20, "15"]) assert.throws(() => parseFilm({ ...good, clipSeconds }), /5, 10 or 15/);
});

test("all three clip actions are required", () => {
  assert.throws(() => parseFilm({ ...good, clips: ["a", "b"] }), /three clip actions/);
  assert.throws(() => parseFilm({ ...good, clips: ["a", " ", "c"] }), /clip 2 action/);
});

test("a generated keyframe needs a scene; your own keyframe needs an image", () => {
  assert.throws(() => parseFilm({ ...good, scene: "" }), /keyframe scene/);
  assert.throws(() => parseFilm({ ...good, generateKeyframe: false }), /PNG, JPEG or WebP/);
  const r = parseFilm({ ...good, scene: "", generateKeyframe: false, image: PNG });
  assert.deepEqual([r.image?.contentType, r.image?.filename, r.image?.bytes.byteLength], ["image/png", "keyframe.png", 8]);
});

test("other file types and oversized images are refused", () => {
  assert.throws(() => parseFilm({ ...good, generateKeyframe: false, image: "data:image/gif;base64,R0lG" }), RequestError);
  const big = `data:image/png;base64,${Buffer.alloc(10 * 1024 * 1024 + 1).toString("base64")}`;
  assert.throws(() => parseFilm({ ...good, generateKeyframe: false, image: big }), /10 MB/);
  const fake = `data:image/png;base64,${Buffer.from("GIF89a").toString("base64")}`;
  assert.throws(() => parseFilm({ ...good, generateKeyframe: false, image: fake }), /not the image type/);
});

test("job ids must look like ids", () => {
  assert.equal(parseJobId("2486a9d5-b791-4b13-a480-cdbdc1da3435"), "2486a9d5-b791-4b13-a480-cdbdc1da3435");
  assert.throws(() => parseJobId("../../etc"), RequestError);
});
