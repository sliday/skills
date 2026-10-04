#!/usr/bin/env python3
"""Replicate runner: create prediction, poll, download outputs, log job record.
usage: rep.py <owner/model> <input.json|-> <out_prefix>"""
import json, os, sys, time, urllib.request, pathlib, datetime
TOK = os.environ["REPLICATE_API_TOKEN"]
H = {"Authorization": f"Bearer {TOK}", "Content-Type": "application/json", "Prefer": "wait=5", "User-Agent": "gsb-pipeline/1.0 (python)"}
ROOT = pathlib.Path(__file__).resolve().parent.parent

def req(url, data=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=H)
    for i in range(3):
        try:
            with urllib.request.urlopen(r, timeout=120) as f: return json.load(f)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:500]
            if e.code in (429, 502, 503, 504) and i < 2: time.sleep(10 * (i + 1)); continue
            raise SystemExit(f"HTTP {e.code}: {body}")

def to_uri(v):
    # local file paths -> data URIs
    if isinstance(v, str) and os.path.isfile(v):
        import base64, mimetypes
        mt = mimetypes.guess_type(v)[0] or "application/octet-stream"
        return f"data:{mt};base64," + base64.b64encode(open(v, "rb").read()).decode()
    if isinstance(v, list): return [to_uri(x) for x in v]
    return v

def run(model, inp, prefix):
    inp = {k: to_uri(v) for k, v in inp.items()}
    m = req(f"https://api.replicate.com/v1/models/{model}")
    if m.get("latest_version") and m["owner"] not in ("google","openai","kwaivgi","bytedance","minimax","black-forest-labs","elevenlabs","runwayml","xai"):
        p = req("https://api.replicate.com/v1/predictions", {"version": m["latest_version"]["id"], "input": inp})
    else:
        try: p = req(f"https://api.replicate.com/v1/models/{model}/predictions", {"input": inp})
        except SystemExit as ex:
            if "HTTP 404" not in str(ex) or not m.get("latest_version"): raise
            p = req("https://api.replicate.com/v1/predictions", {"version": m["latest_version"]["id"], "input": inp})
    pid = p["id"]; t0 = time.time()
    while p["status"] not in ("succeeded", "failed", "canceled"):
        time.sleep(4); p = req(f"https://api.replicate.com/v1/predictions/{pid}")
        if time.time() - t0 > float(os.environ.get("REP_TIMEOUT", 1800)):
            req(f"https://api.replicate.com/v1/predictions/{pid}/cancel", {}); p["status"] = "failed"; p["error"] = "watchdog timeout, canceled"; break
    rec = {"ts": datetime.datetime.now().isoformat(), "model": model, "id": pid, "status": p["status"],
           "prefix": prefix, "error": p.get("error"), "metrics": p.get("metrics"),
           "input": {k: (v[:300] if isinstance(v, str) and not v.startswith("data:") else "<file>") for k, v in inp.items()}}
    out = p.get("output"); files = []
    if p["status"] == "succeeded":
        urls = out if isinstance(out, list) else [out]
        for i, u in enumerate(urls):
            if isinstance(u, str) and u.startswith("http"):
                ext = os.path.splitext(u.split("?")[0])[1] or ".bin"
                fn = f"{prefix}{'' if len(urls)==1 else '_'+str(i)}{ext}"
                pathlib.Path(fn).parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(u, fn); files.append(fn)
        if not files: 
            fn = prefix + ".json"; json.dump(out, open(fn, "w"), indent=1); files.append(fn)
    rec["files"] = files
    with open(ROOT / "jobs/jobs.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps({"id": pid, "status": p["status"], "files": files, "error": p.get("error")}))
    return rec

if __name__ == "__main__":
    model, src, prefix = sys.argv[1:4]
    inp = json.load(sys.stdin if src == "-" else open(src))
    run(model, inp, prefix)
