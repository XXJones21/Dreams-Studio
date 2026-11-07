"""Local shot tracker server. Serves the halloween-short folder and a small JSON API over tracker/shots.json.

    python tracker/server.py            # http://127.0.0.1:8765/tracker/

API
  GET   /api/shots                    whole tracker
  PATCH /api/shots/<id>               {"rev": n, "set": {field: value}}  409 if rev is stale
  POST  /api/shots/<id>/notes         {"who": "Josh", "text": "..."}
  GET   /api/prompt/<id>              the full H3 prompt, rendered by prompts/batch_h3_v02.py from shots.json
Every write bumps the shot's rev and the file rev, and keeps a timestamped copy in tracker/history/.
"""
import importlib, json, os, shutil, sys, threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
DB = os.path.join(HERE, "shots.json")
HIST = os.path.join(HERE, "history")
LOCK = threading.Lock()
EDITABLE = {"status", "current", "caption", "camera", "beat", "zone", "refs", "cast", "beats", "end", "sound", "extra_avoid", "raw_prompt", "seam_ok"}
sys.path.insert(0, os.path.join(FILM, "prompts"))


def load():
    with open(DB, encoding="utf-8") as f:
        return json.load(f)


def save(d):
    os.makedirs(HIST, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    shutil.copy2(DB, os.path.join(HIST, f"shots-{stamp}.json"))
    keep = sorted(os.listdir(HIST))[:-200]
    for old in keep:
        os.remove(os.path.join(HIST, old))
    d["rev"] = d.get("rev", 0) + 1
    tmp = DB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    os.replace(tmp, DB)


def find(d, sid):
    return next((s for s in d["shots"] if s["id"] == sid), None)


def render_prompt(sid):
    import batch_h3_v02 as B
    importlib.reload(B)  # picks up the latest shots.json
    d = load()
    s = find(d, sid)
    if s is None:
        return None
    if s.get("raw_prompt"):
        return s["raw_prompt"]
    if sid not in B.S:
        return ""
    return B.prompt(sid)


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=FILM, **kw)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))

    def end_headers(self):
        if self.path.startswith("/tracker/") and not self.path.startswith("/tracker/media/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/":
            self.send_response(302); self.send_header("Location", "/tracker/"); self.end_headers(); return
        if p == "/api/shots":
            return self._json(200, load())
        if p.startswith("/api/prompt/"):
            txt = render_prompt(unquote(p.rsplit("/", 1)[1]))
            return self._json(404, {"error": "no such shot"}) if txt is None else self._json(200, {"prompt": txt})
        return super().do_GET()

    def do_PATCH(self):
        p = urlparse(self.path).path
        if not p.startswith("/api/shots/"):
            return self._json(404, {"error": "not found"})
        sid = unquote(p.split("/")[3])
        req = self._body()
        with LOCK:
            d = load()
            s = find(d, sid)
            if s is None:
                return self._json(404, {"error": f"no shot {sid}"})
            if req.get("rev") != s.get("rev"):
                return self._json(409, {"error": "This shot changed since you opened it. Reload to see the latest, then reapply your edit.", "shot": s})
            bad = set(req.get("set", {})) - EDITABLE
            if bad:
                return self._json(400, {"error": "not editable: " + ", ".join(sorted(bad))})
            s.update(req["set"])
            s["rev"] = s.get("rev", 0) + 1
            save(d)
        return self._json(200, s)

    def do_POST(self):
        p = urlparse(self.path).path
        parts = p.split("/")
        if len(parts) == 5 and parts[1] == "api" and parts[2] == "shots" and parts[4] == "notes":
            sid = unquote(parts[3])
            req = self._body()
            text = (req.get("text") or "").strip()
            if not text:
                return self._json(400, {"error": "Write a note before adding it."})
            with LOCK:
                d = load()
                s = find(d, sid)
                if s is None:
                    return self._json(404, {"error": f"no shot {sid}"})
                s.setdefault("notes", []).append({"who": req.get("who") or "Josh", "when": datetime.now().isoformat(timespec="minutes"), "text": text})
                s["rev"] = s.get("rev", 0) + 1
                save(d)
            return self._json(200, s)
        return self._json(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("TRACKER_PORT", "8765"))
    print(f"Shot tracker: http://127.0.0.1:{port}/tracker/")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
