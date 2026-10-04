#!/usr/bin/env python3
"""Approval / job / artifact bookkeeping for project.json, hashed through the skill's own validator.
  gate.py approve interpretation bibles prompts [--note "..."]
  gate.py job <id> <provider> <model> <output_path>        (prompt hash = current prompts scope)
  gate.py artifact still|canary <path> <job_id> <provider> <model>
  gate.py stage render_ready|batch_ready|delivery"""
import sys, json, hashlib, datetime, importlib.util, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
V = pathlib.Path("/Users/stas/Playground/story-board-reader/storyboard-to-video/scripts/validate_project.py")
spec = importlib.util.spec_from_file_location("vp", V); vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)
P = ROOT / "project.json"; proj = json.loads(P.read_text())
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
REVIEWER = "claude (model reviewer: vision review of boards/contact sheets; not a human sign-off)"
cmd, args = sys.argv[1], sys.argv[2:]
note = None
if "--note" in args: i = args.index("--note"); note = args[i + 1]; args = args[:i] + args[i + 2:]
if cmd == "approve":
    for kind in args:
        rec = {"kind": kind, "verdict": "approved", "approved_by": REVIEWER, "approved_at": now(),
               "artifact_sha256": vp.approval_scope_sha256(proj, kind, P), "note": note or ""}
        proj["approvals"] = [a for a in proj["approvals"] if a.get("kind") != kind] + [rec]
        print("approved", kind, rec["artifact_sha256"][:12])
elif cmd == "job":
    jid, provider, model, out = args
    rec = {"id": jid, "provider": provider, "model": model, "status": "completed", "output_path": out, "output_sha256": sha(out),
           "prompt_sha256": vp.approval_scope_sha256(proj, "prompts", P), "recorded_at": now()}
    proj["jobs"] = [j for j in proj["jobs"] if j.get("id") != jid] + [rec]; print("job", jid)
elif cmd == "artifact":
    kind, path, jid, provider, model = args
    proj["artifacts"][kind] = {"path": path, "job_id": jid, "provider": provider, "model": model,
                               "prompt_sha256": vp.approval_scope_sha256(proj, "prompts", P)}
    print("artifact", kind, path)
elif cmd == "stage":
    proj["validation_stage"] = args[0]; print("stage", args[0])
P.write_text(json.dumps(proj, indent=1))
