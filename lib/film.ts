// How long the film is: three chained MiniMax H3 clips at 24 fps.

export const FPS = 24;
export const CLIPS = 3;
export const WIDTH = 768;
export const HEIGHT = 1344;

/** MiniMax H3 takes frame counts on a 17k+5 grid; these are the 5, 10 and 15 s points in its trained range. */
export const CLIP_FRAMES = { 5: 124, 10: 243, 15: 362 } as const;
export type ClipSeconds = keyof typeof CLIP_FRAMES;
export const CLIP_SECONDS = Object.keys(CLIP_FRAMES).map(Number) as ClipSeconds[];

export const isClipSeconds = (v: unknown): v is ClipSeconds => CLIP_SECONDS.includes(v as ClipSeconds);

/** Clips 2 and 3 start on the frame the clip before ended on; the workflow keeps that frame once. */
export function filmSeconds(clipSeconds: ClipSeconds): number {
  const frames = CLIP_FRAMES[clipSeconds];
  return (CLIPS * frames - (CLIPS - 1)) / FPS;
}
