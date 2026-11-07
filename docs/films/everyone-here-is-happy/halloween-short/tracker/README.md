# Shot tracker

A local, ShotGrid-style page for the Halloween short. `shots.json` is the single source of truth for every
shot: its status, prompt fields, versions (takes) and notes. The page and the prompt builder both read it.

## Run it

```
python tracker/server.py
```

Then open http://127.0.0.1:8765/tracker/ (link to one shot with `#S10`). `j` / `k` step through shots.

## What each shot shows

- The blockout (clay animatic) next to the current take. "Play both" starts them together.
- Every version, with its ControlNet setting, seed and prompt version. Pick one to preview, then make it the current take.
- Pictures: the blockout first and last frame of the shot (the keyframes an FLF take has to hit) and the
  reference images the shot uses. Click any of them to open it full size. Built by `tracker/media.py`.
- The cuts: the previous shot's last frame, this shot's first / middle / last frames, and the next shot's first frame.
- The prompt fields: references, look, cast with exact counts, timed beats, end state, sound, extra avoid.
  "Full prompt sent to H3" shows the exact text, rendered by `prompts/batch_h3_v02.py` from the saved fields.
- Notes from Josh and Claude, and a status: Waiting, Ready to generate, Generating, Review, Needs fix, Approved.

## How the pieces connect

- `prompts/batch_h3_v02.py` loads its shot table from `shots.json` (set `EHIH_NO_TRACKER=1` to use its built-in seed table).
  A prompt edited and saved in the tracker is the prompt the next generation uses.
- After a new take is downloaded, add it to that shot's `versions` in `shots.json`, then run
  `python tracker/media.py` to make its stills.
- Every save keeps a copy in `tracker/history/` (last 200). Saves are per shot and checked against the shot's
  `rev`, so two people editing different shots never overwrite each other.

## Files

| File | Purpose |
|---|---|
| `shots.json` | Source of truth |
| `server.py` | Serves the film folder and the JSON API |
| `index.html` | The tracker page |
| `media.py` | Blockout clips and stills in `media/` |
| `migrate.py` | One-time seed of `shots.json` (2026-11-01) |
