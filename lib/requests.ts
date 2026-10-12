// Checks the request body before any paid job starts.
import { isClipSeconds, type ClipSeconds } from "./film.ts";

export class RequestError extends Error {}

export type FilmRequest = {
  style: string; scene: string; avoid: string; clips: [string, string, string]; clipSeconds: ClipSeconds;
  generateKeyframe: boolean; image?: { bytes: Uint8Array; contentType: string; filename: string };
};

type Body = Record<string, unknown>;
const ID = /^[A-Za-z0-9_-]{1,200}$/;
const IMAGE_TYPES: Record<string, string> = { "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp" };
export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const starts = (b: Uint8Array, sig: number[], at = 0) => sig.every((v, i) => b[at + i] === v);
const SIGNATURES: Record<string, (b: Uint8Array) => boolean> = {
  "image/png": (b) => starts(b, [0x89, 0x50, 0x4e, 0x47]),
  "image/jpeg": (b) => starts(b, [0xff, 0xd8, 0xff]),
  "image/webp": (b) => starts(b, [0x52, 0x49, 0x46, 0x46]) && starts(b, [0x57, 0x45, 0x42, 0x50], 8),
};

const obj = (v: unknown): Body => {
  if (!v || typeof v !== "object" || Array.isArray(v)) throw new RequestError("Send a JSON object.");
  return v as Body;
};
const text = (v: unknown, label: string, max: number, required = true) => {
  if (typeof v !== "string") throw new RequestError(`The ${label} must be text.`);
  const t = v.trim();
  if (required && !t) throw new RequestError(`Write the ${label} first.`);
  if (t.length > max) throw new RequestError(`Keep the ${label} under ${max.toLocaleString("en-US")} characters.`);
  return t;
};

/** The browser sends an uploaded keyframe as a data URL. */
function image(v: unknown): NonNullable<FilmRequest["image"]> {
  const match = typeof v === "string" ? v.match(/^data:([a-z/]+);base64,([A-Za-z0-9+/=]+)$/) : null;
  if (!match || !IMAGE_TYPES[match[1]]) throw new RequestError("Upload the keyframe as a PNG, JPEG or WebP image.");
  const bytes = new Uint8Array(Buffer.from(match[2], "base64"));
  if (bytes.byteLength > MAX_IMAGE_BYTES) throw new RequestError("Keep the keyframe image under 10 MB.");
  if (!SIGNATURES[match[1]](bytes)) throw new RequestError("That file is not the image type it claims to be.");
  return { bytes, contentType: match[1], filename: `keyframe.${IMAGE_TYPES[match[1]]}` };
}

export function parseFilm(input: unknown): FilmRequest {
  const b = obj(input);
  if (typeof b.generateKeyframe !== "boolean") throw new RequestError("Choose how to make the keyframe.");
  if (!isClipSeconds(b.clipSeconds)) throw new RequestError("Choose a clip length of 5, 10 or 15 seconds.");
  if (!Array.isArray(b.clips) || b.clips.length !== 3) throw new RequestError("Send three clip actions.");
  const clips = b.clips.map((c, i) => text(c, `clip ${i + 1} action`, 3000)) as [string, string, string];
  const request: FilmRequest = {
    style: text(b.style, "style", 3000),
    scene: text(b.scene ?? "", "keyframe scene", 2000, b.generateKeyframe),
    avoid: text(b.avoid ?? "", "avoid list", 1000, false),
    clips, clipSeconds: b.clipSeconds, generateKeyframe: b.generateKeyframe,
  };
  if (!b.generateKeyframe) request.image = image(b.image);
  return request;
}

export function parseJobId(v: string): string {
  if (!ID.test(v)) throw new RequestError("That job id is not valid.");
  return v;
}
