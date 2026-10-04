#!/usr/bin/env python3
"""fal.py <endpoint> <input.json> <out_prefix>
Local file paths in the input (strings, or lists of strings) are uploaded to fal storage once (cached by sha256).
Logs every job to jobs/jobs.jsonl. Watchdog: FAL_TIMEOUT seconds (default 900) -> cancel + fail."""
import os, sys, json, time, hashlib, pathlib, datetime, urllib.request
import fal_client
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "jobs/fal_uploads.json"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
def up(v):
    if isinstance(v, list): return [up(x) for x in v]
    if isinstance(v, str) and os.path.isfile(v):
        h = hashlib.sha256(open(v, "rb").read()).hexdigest()
        if h not in cache:
            cache[h] = fal_client.upload_file(v); CACHE.write_text(json.dumps(cache, indent=1))
        return cache[h]
    return v
def run(ep, inp, prefix):
    raw = dict(inp); inp = {k: up(v) for k, v in inp.items()}
    h = fal_client.submit(ep, arguments=inp); rid = h.request_id; t0 = time.time(); status = "failed"; err = None; res = None
    tmo = float(os.environ.get("FAL_TIMEOUT", 900))
    while True:
        st = fal_client.status(ep, rid)
        name = type(st).__name__
        if name == "Completed":
            try: res = fal_client.result(ep, rid); status = "succeeded"
            except Exception as e: err = str(e)[:400]
            break
        if time.time() - t0 > tmo:
            try: fal_client.cancel(ep, rid)
            except Exception: pass
            err = "watchdog timeout, canceled"; break
        time.sleep(6)
    files = []
    if res:
        urls = []
        for key in ("video", "image", "images", "videos"):
            v = res.get(key)
            if isinstance(v, dict) and v.get("url"): urls.append(v["url"])
            if isinstance(v, list): urls += [x["url"] for x in v if isinstance(x, dict) and x.get("url")]
        for i, u in enumerate(urls):
            ext = os.path.splitext(u.split("?")[0])[1] or ".bin"
            fn = f"{prefix}{'' if len(urls) == 1 else '_' + str(i)}{ext}"
            pathlib.Path(fn).parent.mkdir(parents=True, exist_ok=True); urllib.request.urlretrieve(u, fn); files.append(fn)
    rec = {"ts": datetime.datetime.now().isoformat(), "provider": "fal", "model": ep, "id": rid, "status": status, "prefix": prefix, "error": err,
           "seconds": round(time.time() - t0, 1), "input": {k: (v if not (isinstance(v, str) and len(v) > 400) else v[:400]) for k, v in raw.items()}, "files": files}
    with open(ROOT / "jobs/jobs.jsonl", "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({"id": rid, "status": status, "files": files, "error": err}))
if __name__ == "__main__":
    ep, src, prefix = sys.argv[1:4]; run(ep, json.load(open(src)), prefix)
