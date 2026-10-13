"use client";
import { useState } from "react";

const FINAL = ["succeeded", "failed", "canceled", "expired"];

export default function Page() {
  const [style, setStyle] = useState("");
  const [status, setStatus] = useState("");
  const [url, setUrl] = useState<string | null>(null);

  async function make() {
    setUrl(null);
    setStatus("submitting");
    const res = await fetch("/api/film", { method: "POST", body: JSON.stringify({ style }) });
    const { id } = await res.json();

    while (true) {
      const job = await (await fetch(`/api/film/${id}`)).json();
      setStatus(job.status);
      if (FINAL.includes(job.status)) return setUrl(job.url);
      await new Promise((r) => setTimeout(r, 5000));
    }
  }

  return (
    <main>
      <h1>Mini Dreams</h1>
      <textarea rows={4} cols={60} value={style} onChange={(e) => setStyle(e.target.value)} />
      <p><button onClick={make}>Make the film</button> {status}</p>
      {url && <video src={url} controls autoPlay width={360} />}
    </main>
  );
}
