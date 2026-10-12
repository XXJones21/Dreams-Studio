# The Dreams Studio workflow

`workflows/dream_film.json` is the node workflow; open it in ComfyUI or Comfy Cloud. `workflows/dream_film.api.json` is the same graph exported with **Export (API)**, and it's what the app runs. One job makes the keyframe, three chained clips and the stitched film.

```
Style ─┬─► Keyframe prompt + Avoid ─► Nano Banana 2.1 ─┐
       │                                                ├─► Switch ─┬─► Save keyframe
       │                              Load Image ───────┘           │
       │                                                            ▼
       ├─► Clip 1 prompt ─────────────────► Clip 1 (H3) ─► last frame ─► Clip 2 (H3) ─► last frame ─► Clip 3 (H3)
       ├─► Clip 2 prompt ────────────────────────────────────────────────┘                             │
       └─► Clip 3 prompt ───────────────────────────────────────────────────────────────────────────────┘
Clip 1 + (Clip 2 − first frame) + (Clip 3 − first frame) ─► Stitch ─► Save film
```

## Nodes by job

| Job | Nodes (id) | Notes |
|---|---|---|
| Inputs the app sets | Style `2001`, Keyframe scene `2002`, Clip actions `2003`–`2005`, Avoid `4452018332049331`, Length `2213` | Titled primitive nodes; `workflows/dream_film.inputs.json` names them |
| Prompts | `2011`–`2014`, `4452018332049332` (String Concatenate) | Style + each action. Avoid goes only into the keyframe prompt, because Nano Banana has no negative-prompt input |
| Keyframe | Nano Banana 2.1 `4452018332049330` (partner node, 9:16), Load Image `8`, Switch `2201`, Save keyframe `4452018332049327` | Save sits after the switch, so Nano Banana runs only when the switch picks it |
| Models | `1` H3 FL2VA int8, `2` 4-step turbo LoRA, `3` Qwen3-VL text encoder, `4`/`5` video and audio VAEs, `6`/`7` sampler with 4 steps | All in Comfy Cloud's catalog; they run on Cloud's GPU, not as a partner API |
| Clip 1, 2, 3 | `101`–`108`, `201`–`208`, `301`–`307` | Image to video, then sample, decode video and audio, and make the video. `108`/`208` take the last frame for the next clip |
| Size | Width `2211` (768), Height `2212` (1344), Length `2213` | `Basic data handling: IntCreate` nodes, from a pack in Cloud's catalog |
| Stitch | Crop `910`/`911`, math `4452018332049333`, Concatenate `900`, Save film `901` | See below |

## Clip length and the seam frames

MiniMax H3 takes frame counts on a 17k + 5 grid (124, 141, 158, … frames). The app offers three points on that grid:

| Clip length | Frames (Length `2213`) | Film |
|---|---|---|
| 5 s | 124 | 15.4 s |
| 10 s | 243 | 30.3 s |
| 15 s | 362 | 45.2 s |

Clip 2 starts on clip 1's last frame, so that frame appears twice. Crop Video (Temporal) drops it from clips 2 and 3: it starts at frame 1, and its length comes from a Math Expression node, `a - 1`, with `a` wired to Length. Change the length in one place and the crops follow. `npm test` checks this wiring.

## Cost

On Comfy Cloud, the three H3 clips bill GPU time: about 210 credits for a 3 × 15 s film. A Nano Banana keyframe adds about 13 credits. To skip it, set the switch to your own image.

## Changing the workflow

1. Open `workflows/dream_film.json` in Comfy Cloud, edit it, and run it once there.
2. Save it over `workflows/dream_film.json`, and use **Export (API)** to save over `workflows/dream_film.api.json`.
3. If node ids changed, update `workflows/dream_film.inputs.json`. `npm run inspect -- workflows/dream_film.api.json` lists the ids.
4. Run `npm test`.
