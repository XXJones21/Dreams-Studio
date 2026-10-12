"use client";

import { useEffect, useRef, useState } from "react";
import { isActive, restore, runFromJob, serialize, type Dream, type JobJson } from "../lib/dream.ts";
import { CLIP_FRAMES, CLIP_SECONDS, CLIPS, filmSeconds, FPS, HEIGHT, WIDTH, type ClipSeconds } from "../lib/film.ts";
import { PRESETS, type PresetName } from "../lib/styles.ts";

const STORE = "dreams-studio:dream";
const MAX_IMAGE_BYTES = 10 * 1024 * 1024;

function dreamFrom(name: PresetName): Dream {
  const p = PRESETS[name];
  return { version: 2, style: p.style, scene: p.scene, avoid: p.avoid, clips: [...p.clips], clipSeconds: 15, generateKeyframe: true };
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error((data as { error?: string }).error ?? `Request failed (${response.status}).`);
  return data as T;
}

const clock = (ms: number) => {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

export function Dreams() {
  const [dream, setDream] = useState<Dream>(() => dreamFrom("Skeleton cavern"));
  const [image, setImage] = useState<{ url: string; name: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [fields, setFields] = useState(false);
  const [restored, setRestored] = useState(false);
  const misses = useRef(0);

  // Reload safety: restore once, then save on every change. Saving waits for `restored`, so the first
  // render never overwrites the saved dream. Storage can be missing or blocked. The uploaded image is not saved.
  useEffect(() => {
    try { const saved = restore(localStorage.getItem(STORE)); if (saved) setDream(saved); } catch {}
    setRestored(true);
  }, []);
  useEffect(() => {
    if (!restored) return;
    try { localStorage.setItem(STORE, serialize(dream)); } catch {}
  }, [dream, restored]);

  // Poll the film job every 5 s while it is queued or running. Each poll also moves the elapsed clock.
  useEffect(() => {
    const run = dream.run;
    if (!run || !isActive(run)) return;
    const timer = setTimeout(async () => {
      let next = run;
      try {
        const response = await fetch(`/api/jobs/${run.jobId}`);
        const data = (await response.json().catch(() => ({}))) as JobJson & { error?: string };
        if (response.ok) { next = runFromJob(data, run.startedAt); misses.current = 0; }
        else if (response.status < 500) next = { ...run, status: "failed", error: data.error ?? "Comfy no longer knows this job." };
        else misses.current += 1;
      } catch { misses.current += 1; }
      // A few failed polls in a row (network, Comfy busy) are normal; six means we lost track of the job.
      if (misses.current >= 6) {
        misses.current = 0;
        next = { ...run, status: "failed", error: `Lost track of job ${run.jobId}. It may still finish: check Runs in Comfy Cloud.` };
      }
      setDream((d) => (d.run?.jobId === run.jobId ? { ...d, run: { ...next } } : d));
    }, 5000);
    return () => clearTimeout(timer);
  }, [dream.run]);

  const update = (patch: Partial<Dream>) => setDream((d) => ({ ...d, ...patch }));
  const setClip = (i: number, value: string) =>
    setDream((d) => ({ ...d, clips: d.clips.map((c, j) => (j === i ? value : c)) as Dream["clips"] }));

  function pickImage(file: File | undefined) {
    setMessage("");
    if (!file) return;
    if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) return setMessage("Use a PNG, JPEG or WebP image.");
    if (file.size > MAX_IMAGE_BYTES) return setMessage("Keep the keyframe image under 10 MB.");
    const reader = new FileReader();
    reader.onload = () => setImage({ url: String(reader.result), name: file.name });
    reader.readAsDataURL(file);
  }

  const missing = !dream.style.trim() ? "the style"
    : dream.generateKeyframe && !dream.scene.trim() ? "the keyframe scene"
    : !dream.generateKeyframe && !image ? "a keyframe image"
    : dream.clips.findIndex((c) => !c.trim()) >= 0 ? `the clip ${dream.clips.findIndex((c) => !c.trim()) + 1} action` : "";

  async function makeFilm() {
    setBusy(true); setMessage("");
    try {
      const { job } = await post<{ job: JobJson }>("/api/dream/film", {
        style: dream.style, scene: dream.scene, avoid: dream.avoid, clips: dream.clips, clipSeconds: dream.clipSeconds,
        generateKeyframe: dream.generateKeyframe, image: dream.generateKeyframe ? undefined : image?.url,
      });
      update({ run: runFromJob(job, Date.now()) });
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const run = dream.run;
  const active = isActive(run);
  const frames = CLIP_FRAMES[dream.clipSeconds];

  return (
    <div className={fields ? "wrap fields" : "wrap"}>
      <a className="back" href="https://comfy.org/hub">‹ Back to apps</a>
      <div className="titlerow"><h1>Dreams Studio</h1><span className="beta">BETA</span></div>
      <div className="subrow">
        <p className="sub">Describe a dream and watch it play out as a short film with sound.</p>
        <a className="gh" href="https://github.com/">View on GitHub ↗</a>
      </div>
      <div className="grid">
        <section className="card">
          <div className="card-h">
            <span className="t">New dream</span>
            <span className="opts">{(Object.keys(PRESETS) as PresetName[]).map((name) => (
              <button key={name} type="button" className="opt" disabled={active}
                onClick={() => { setDream({ ...dreamFrom(name), run: dream.run }); setImage(null); }}>{name}</button>))}</span>
          </div>
          <div className="body">
            <div className="picker"><span className="k">Keyframe</span><span className="grow">Nano Banana 2.1</span><span className="tag">partner</span></div>
            <div className="picker"><span className="k">Video</span><span className="grow">MiniMax H3 · 3 chained clips</span><span className="tag cloud">Cloud GPU</span></div>

            <label className="prompt"><span className="lbl"><span>Style <code className="field">2001 · every prompt</code></span><span>{dream.style.length} / 3000</span></span>
              <textarea value={dream.style} maxLength={3000} disabled={active} onChange={(e) => update({ style: e.target.value })} />
            </label>

            <div className="rows">
              <button type="button" className="row-h" disabled={active} onClick={() => update({ generateKeyframe: !dream.generateKeyframe })}>
                <span className="row-l">Keyframe</span><span className="row-v">{dream.generateKeyframe ? "Generate" : "My image"}</span>
                <span className="chips"><span className="chip">{dream.generateKeyframe ? "Nano Banana · ~13 credits" : "PNG / JPEG / WebP"}</span></span>
                <code className="field">2201 switch</code></button>
            </div>
            {dream.generateKeyframe ? (<>
              <label className="prompt"><span className="lbl"><span>Keyframe scene <code className="field">2002</code></span><span>{dream.scene.length} / 2000</span></span>
                <textarea value={dream.scene} maxLength={2000} disabled={active} placeholder="The first frame of the film: where you are and what you see."
                  onChange={(e) => update({ scene: e.target.value })} />
              </label>
              <label className="prompt"><span className="lbl"><span>Avoid · keyframe only <code className="field">Nano Banana has no negative prompt</code></span></span>
                <textarea value={dream.avoid} maxLength={1000} disabled={active} onChange={(e) => update({ avoid: e.target.value })} />
              </label>
            </>) : (
              <label className="prompt upload"><span className="lbl"><span>Keyframe image <code className="field">8 · Load Image</code></span><span>9:16 works best</span></span>
                <input type="file" accept="image/png,image/jpeg,image/webp" disabled={active} onChange={(e) => pickImage(e.target.files?.[0])} />
                {image && <img src={image.url} alt="Your keyframe" />}
              </label>
            )}

            {dream.clips.map((clip, i) => (
              <label className="prompt" key={i}><span className="lbl"><span>Clip {i + 1} action <code className="field">{2003 + i}</code></span>
                <span>{i === 0 ? "starts on the keyframe" : `starts on clip ${i}'s last frame`}</span></span>
                <textarea value={clip} maxLength={3000} disabled={active} placeholder="Stage directions: who does what, beat by beat, and where the clip ends."
                  onChange={(e) => setClip(i, e.target.value)} />
              </label>))}

            <div className="bar">
              <label className="box"><span className="k">Clip length</span>
                <select value={dream.clipSeconds} disabled={active} onChange={(e) => update({ clipSeconds: Number(e.target.value) as ClipSeconds })}>
                  {CLIP_SECONDS.map((s) => <option key={s} value={s}>{s} s</option>)}</select></label>
              <span className="box"><span className="k">Film</span><span>{filmSeconds(dream.clipSeconds).toFixed(1)} s</span></span>
            </div>
            <div className="split">{CLIPS} clips × {frames} frames · {WIDTH}×{HEIGHT} · {FPS} fps <code className="field">2213 Length</code></div>
            <button className="gen" disabled={busy || active || !!missing} onClick={makeFilm}>{active ? "MAKING THE FILM…" : "MAKE THE FILM"}</button>
            <p className={message ? "status error" : "status"} role="status">{message || (missing && !active ? `Add ${missing} to start.` : "")}</p>
            <p className="prov">About 210 credits for 3 × 15 s (measured), plus ~13 for a generated keyframe. Shorter clips cost less.</p>
            <div className="foot">
              <button className={fields ? "toggle on" : "toggle"} type="button" onClick={() => setFields(!fields)}><span className="sw" />Show workflow fields</button>
              <span>One workflow on Comfy Cloud</span>
            </div>
          </div>
        </section>

        <section className="card out">
          <div className="card-h"><span className="t">OUTPUT</span>{run && <span className="chip">job {run.jobId.slice(0, 8)}</span>}</div>
          {!run && <div className="empty"><div className="h">Your film appears here</div>
            <div className="s">One job on Comfy Cloud makes the keyframe, three chained clips and the stitched film.</div></div>}
          {run && active && <div className="empty"><div className="h">Making the film… {run.status} · {clock(Date.now() - run.startedAt)}</div>
            <div className="s">A 3 × 15 s film takes about 13–15 minutes on Comfy Cloud. You can reload this page; the job keeps running.</div></div>}
          {run?.status === "failed" && <div className="empty"><div className="h">The film did not finish</div><p className="status error">{run.error}</p></div>}
          {run?.status === "done" && run.film && (
            <div className="film">
              <video src={run.film} controls className="f9x16" />
              <div>
                {run.keyframe && <img className="keyframe" src={run.keyframe} alt="The keyframe the film started from" />}
                <div className="actions">
                  <a className="button" href={run.film} download="dream.mp4">Download .mp4</a>
                  {run.keyframe && <a className="button" href={run.keyframe} download="keyframe.png">Download keyframe</a>}
                  <a className="button" download="dream.json" href={`data:application/json,${encodeURIComponent(serialize(dream))}`}>Download dream.json</a>
                </div>
                <p className="prov">Comfy Cloud keeps outputs for 24 hours. Download the film to keep it.</p>
              </div>
            </div>)}
        </section>
      </div>
    </div>
  );
}
