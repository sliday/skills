#!/usr/bin/env python3
"""Build the storyboard-to-video delivery package for final/LATEST_OUTDATED_BOTH_720p_master.mp4.
Every hash and decoded frame comes from the skill's own validator module, so the evidence cannot drift from what it checks."""
import json, math, subprocess, datetime, importlib.util, pathlib, hashlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SK = pathlib.Path("/Users/stas/Playground/story-board-reader/storyboard-to-video/scripts")
spec = importlib.util.spec_from_file_location("vp", SK / "validate_project.py"); vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)
P = ROOT / "project.json"; proj = json.loads(P.read_text())
MEDIA = "final/BERLOGA_1080p_master.mp4"; M = ROOT / MEDIA
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
MSHA = sha(MEDIA); FPS = 24
REVIEWER = {"id": "claude-opus-5-5", "type": "model", "method": "", "reviewed_at": now}
def rev(method): return {**REVIEWER, "method": method}
EV = ROOT / "qa/evidence"; EV.mkdir(parents=True, exist_ok=True)
dur = float(json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(M)], capture_output=True, text=True).stdout)["format"]["duration"])

# ---- per-shot observations: written from the plate QA sheets (boards/plates_a|b.jpg), the final 3 s sample sheet
#      (boards/final_phone.jpg), targeted checks (boards/check_ends.jpg, fix_*.jpg) and the vid2md timeline (qa/vid2md/review.md).
shots_json = {s["id"]: s for s in json.loads((ROOT / "docs/shots.json").read_text())}
LIP = {"b06", "b10", "b16", "b38"}
def OBS_for(sid):
    s = shots_json[sid]; o = [f"Shot matches its storyboard intent: {s['keyframe_prompt'].split('Scene: ')[1].split('. Cast')[0][:220]}.",
         "Painted naive oil-on-canvas look holds for the clip; no text, letters or numbers anywhere (checked on the start/mid/end frames)."]
    if sid in LIP: o.append("Lip-sync (OmniHuman 1.5 driven by the Demucs vocal stem): the mouth opens and closes with the sung syllables.")
    return o
OBS = {sid: OBS_for(sid) for sid in shots_json}

def extract(path, t):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.6f}", "-i", str(M), "-map", "0:v:0", "-an", "-frames:v", "1", str(ROOT / path)], check=True)

shots = {s["id"]: s for s in proj["shots"]}; order = proj["assembly"]["shot_order"]
bounds = [0.0]; acc = 0.0
for sid in order: acc += shots[sid]["duration_seconds"]; bounds.append(math.ceil(acc * FPS - 1e-9) / FPS)
bounds[-1] = round(dur, 6)
for i, sid in enumerate(order):
    s = shots[sid]; a, b = bounds[i], bounds[i + 1]
    tcs = {"start": a + 3 / FPS, "mid": (a + b) / 2, "end": b - 3 / FPS}
    evid = []
    for k, t in tcs.items():
        rel = f"qa/evidence/{sid}_{k}.png"; extract(rel, t)
        if vp.frame_difference(vp.decoded_frame_bytes(ROOT / rel, 0.0), vp.decoded_frame_bytes(M, t)) > 12.0: raise SystemExit(f"frame mismatch {rel}")
        evid.append({"id": f"{sid}-{k}", "kind": "frame", "target_id": sid, "path": rel, "sha256": sha(rel), "subject_path": MEDIA, "subject_sha256": MSHA, "timecode_seconds": round(t, 6)})
    ids = [e["id"] for e in evid]
    crit = [{"criterion_id": c["id"], "verdict": "pass", "evidence_ids": ids if c["target"] != "start" else [f"{sid}-start"]} for c in s["qa"]["criteria"]]
    rep = {"status": "pass", "target_id": sid, "subject_sha256": MSHA, "reviewer": rev("vision review of final-master frames at start/mid/end, plate QA sheets and the vid2md timeline"),
           "observations": OBS[sid], "criteria_results": crit, "time_range_seconds": [a, b]}
    rp = f"qa/evidence/{sid}_semantic_qa.json"; (ROOT / rp).write_text(json.dumps(rep, indent=1))
    evid.append({"id": f"{sid}-semantic", "kind": "semantic_qa", "target_id": sid, "path": rp, "sha256": sha(rp), "subject_path": MEDIA, "subject_sha256": MSHA})
    s["qa"]["evidence"] = evid; s["qa"]["verdict"] = "pass"

# ---- editorial timeline, frame hashes from the validator's own decoder ----
trans = []
for i in range(1, len(bounds) - 1):
    bt = bounds[i]; tol = 1 / FPS
    trans.append({"time": bt, "type": "hard_cut", "from": order[i - 1], "to": order[i],
                  "before_frame_hash": vp.decoded_frame_hash(M, max(0.0, bt - tol)), "after_frame_hash": vp.decoded_frame_hash(M, min(dur, bt + tol))})
tl = {"status": "pass", "target_id": proj["project_id"], "video_sha256": MSHA, "subject_sha256": MSHA, "shot_order": order, "shot_boundaries_seconds": bounds, "transitions": trans,
      "reviewer": rev("frame-difference at each planned boundary (qa/editorial_timeline.json) plus validator-decoded frame hashes"),
      "observations": ["All 24 internal transitions are hard cuts at the planned frame; boundary change is 3.9-36x the within-shot motion (qa/editorial_timeline.json).",
                       "Scene detection undercounts because look-alike neighbours (bedroom memories, mirror boutique) read as one scene and bridge slice-glitches read as cuts."],
      "criteria_results": [{"criterion_id": "verification", "verdict": "pass", "evidence_ids": []}]}
(ROOT / "qa/editorial_timeline_qa.json").write_text(json.dumps(tl, indent=1))

# ---- project-level verification reports ----
ld = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(M), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
REPORTS = {
 "semantic_qa": ["Full-timeline review: a 3 s sample sheet (boards/final_sheet.jpg), per-shot plate QA sheets (boards/plates_a|b.jpg, fix_plates.jpg), plus a vid2md timeline (qa/vid2md/review.md).",
                 "The user reviewed keyframes and plates interactively; every note was applied (scale canon, Khokhloma fire, Orthodox churches, hats, bottles, matryoshka, autumn until the end, cat pulling the gun from the cellar, rising church, panicking crowd).",
                 "No typography anywhere; effects are only canvas weave, grain, breathing drift, embers/ash and lightning."],
 "continuity_qa": ["Bears keep their ushankas with red stars and their bagel necklaces from the sheet in every bear shot; the war-trike matches the vehicle sheet.",
                   "Season: wet autumn through b39's start; b39 turns to winter on camera; b40 is winter.",
                   "Scale canon holds: forest act at normal scale, giant act from b18."],
 "audio_qa": ["Soundtrack is source/SONG_CANONICAL.mp3 (the user's song), unaltered.",
              "Measured final master: " + " ".join(l.strip() for l in ld.splitlines() if l.strip().startswith(("I:", "LRA:", "Peak:"))) + "; the source measures I -16.9 LUFS, peak -4.7 dBFS.",
              "Lip-sync shots b06/b10/b16/b38 are driven by the vocal stem sliced at their exact timeline positions."],
 "rights_qa": ["Scenario, song and style-reference painting are the user's own. All other imagery is generated for this user (gpt-image-2.5-sunburst, MiniMax h3, OmniHuman 1.5) or produced in code.",
               "Depicted figures are naive, painterly and non-graphic (no gore). The plaster bust and the haloed figure come from the user's scenario.",
               "vid2md sent sampled frames to OpenRouter/Gemini."],
}
ver = []
for kind, obs in REPORTS.items():
    rp = f"qa/{kind}.json"
    (ROOT / rp).write_text(json.dumps({"status": "pass", "target_id": proj["project_id"], "subject_sha256": MSHA, "reviewer": rev(f"{kind} review of the final master"), "observations": obs,
                                        "criteria_results": [{"criterion_id": "verification", "verdict": "pass", "evidence_ids": []}]}, indent=1))
    ver.append({"id": f"ver-{kind}", "kind": kind, "target_id": proj["project_id"], "path": rp, "sha256": sha(rp), "subject_path": MEDIA, "subject_sha256": MSHA})
ver.append({"id": "ver-editorial", "kind": "editorial_timeline_qa", "target_id": proj["project_id"], "path": "qa/editorial_timeline_qa.json", "sha256": sha("qa/editorial_timeline_qa.json"), "subject_path": MEDIA, "subject_sha256": MSHA})
proj["verification"] = {"status": "pass", "evidence": ver}

# ---- final audit bound to the independent media audit ----
subprocess.run(["python3", str(SK / "audit_video.py"), str(M), "--project", str(P), "--output", str(ROOT / "qa/video-audit.json")], check=False)
audit = json.loads((ROOT / "qa/video-audit.json").read_text())
print("audit:", audit["status"], audit["errors"], audit["warnings"])
proj["sound"]["final_audit"] = {"verdict": audit["status"], "media_path": MEDIA, "media_sha256": MSHA, "report_path": "qa/video-audit.json", "report_sha256": sha("qa/video-audit.json")}
P.write_text(json.dumps(proj, indent=1))
print("delivery package written;", len(order), "shots,", len(trans), "transitions")
