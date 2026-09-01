#!/usr/bin/env python3
"""Generate a private, aggregate-only development-agent activity report."""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, html, json, os, re, sqlite3, webbrowser
from pathlib import Path
from typing import Any

HOME=Path.home(); ROOT=HOME/".hermes/cache/agent-insights"
DEFAULT_HTML=ROOT/"report.html"; DEFAULT_JSON=ROOT/"report-data.json"
SENSITIVE=[r"sk-[A-Za-z0-9_-]{16,}",r"ghp_[A-Za-z0-9]{20,}",r"github_pat_[A-Za-z0-9_]{20,}",r"xox[baprs]-[A-Za-z0-9-]{10,}",r"AKIA[0-9A-Z]{16}",r"Bearer\s+[A-Za-z0-9._-]{20,}",r"-----BEGIN [A-Z ]*PRIVATE KEY-----",r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s<]+",r"/Users/[^/\s<]+/",r"/home/[^/\s<]+/",r"[A-Za-z]:\\Users\\[^\\\s<]+\\"]
FORBIDDEN_JSON_KEYS={"text","content","prompt","prompt_text","transcript","tool_output","response"}
AUTO=[r"<teammate-message",r"<system-reminder",r"<command-name",r"<command-message",r"=== INSTRUCTIONS",r"^You are ",r"^ROLE:",r"^Task:",r"Output exactly",r"external-import-turn",r"\[OUT-OF-BAND USER MESSAGE"]
PATTERNS={
 "build / change":r"\b(build|create|implement|add|make|update|fix|change|improve|extend|restore|remove|replace|move|convert|generate)\b|сделай|добавь|исправ|обнови",
 "visual calibration":r"\b(visual|image|screenshot|screen|sprite|pixel|font|layout|ui|ux|design|color|spacing|menu|button|animation|texture|readable|cent(?:er|re)|looks?)\b|выгляд|визуал|скрин|интерфейс",
 "narrow / preserve":r"\b(only|just|simpl|minimal|remove|without|don[’']?t|do not|instead|too (?:big|small|much|many)|keep .* same|preserve|scope)\b|только|просто|убери|не надо|слишком|сохрани",
 "verify / test":r"\b(test|verify|validate|check|proof|confirm|read.?back|live target)\b|проверь|протест",
 "ship / release":r"\b(commit|push|merge|deploy|release|publish|ship|launch|npm)\b|запуш|задеплой|релиз",
 "review / audit":r"\b(review|audit|inspect|critique|second opinion|security review)\b|проверь|ревью",
 "delegate / second opinion":r"\b(sub-?agents?|delegate|delegation|parallel|summon|second opinion|codex review|agent team)\b|субагент|делегир",
 "workflow as product":r"\b(agent harness|agent workflow|orchestrat|hooks?|skills?|claude code|codex cli|opencode|agent tooling)\b"}
FRICTIONS={
 "visual mismatch":r"(?:wrong|doesn[’']?t|didn[’']?t|still|again|issue|problem|broken|I don[’']?t like|too (?:big|small|dark|light)).{0,100}(?:visual|screen|sprite|pixel|font|layout|ui|ux|design|color|menu|animation)|(?:visual|screen|sprite|pixel|font|layout|ui|ux|design).{0,100}(?:wrong|doesn[’']?t|still|again|issue|broken|too)",
 "failed verification":r"\b(test|build|lint|deploy|release|proof|verify|command).{0,80}\b(fail|failed|error|broken|didn[’']?t|doesn[’']?t)|\b(fail|failed|error|broken).{0,80}\b(test|build|lint|deploy|release|verify)",
 "auth / user presence":r"\b(oauth|login|sign.?in|credential|permission|vpn|browser confirmation|captcha|2fa|token expired|authorization)\b",
 "environment / shell":r"\b(shell|quoting|grep|path|cache|cached|environment|unicode|serialization|origin/head|working tree|port)\b",
 "context / continuity":r"\b(check .*history|read .*history|previous session|continue|resume|you forgot|already told|rebrief)\b",
 "scope rework":r"\b(remove|undo|revert|instead|only|just|do not|don[’']?t|not what|preserve|keep .*same)\b"}
CONTAINERS={"(unknown)","unknown",".claude","playground",""}

def clean(v:Any)->str:return re.sub(r"\s+"," ",str(v or "").strip())
def epoch(v:Any)->float|None:
 if v is None:return None
 try:
  n=float(v);return n/1000 if n>1e10 else n
 except (ValueError,TypeError):pass
 try:return dt.datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
 except ValueError:return None
def candidate(t:str)->bool:return bool(t) and len(t)<=1500 and not any(re.search(x,t,re.I) for x in AUTO)
def ro(path:Path):
 c=sqlite3.connect(f"file:{path}?mode=ro",uri=True);c.row_factory=sqlite3.Row;return c
def pname(v:Any)->str:
 s=clean(v) or "(unknown)"
 if "/" in s or "\\" in s:s=Path(os.path.expanduser(s)).name or s
 return s[:80]
def stub(name:str,path:Path,kind:str)->dict:return {"name":name,"available":path.exists(),"kind":kind}
def private_write(path:Path,text:str):
 path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);path.write_text(text)
 try:os.chmod(path,0o600)
 except OSError:pass
def sensitive_hits(text:str)->list[str]:return [x for x in SENSITIVE if re.search(x,text,re.I)]
def forbidden_json_paths(value:Any,path:str="$",out:list[str]|None=None)->list[str]:
 out=[] if out is None else out
 if isinstance(value,dict):
  for k,v in value.items():
   if str(k).lower() in FORBIDDEN_JSON_KEYS:out.append(f"{path}.{k}")
   forbidden_json_paths(v,f"{path}.{k}",out)
 elif isinstance(value,list):
  for i,v in enumerate(value):forbidden_json_paths(v,f"{path}[{i}]",out)
 return out

def claude(cutoff:float)->dict:
 p=HOME/".claude-mem/claude-mem.db";o=stub("Claude + claude-mem",p,"authored prompts")
 if not p.exists():o["error"]="database not found";return o
 try:
  c=ro(p);rows=c.execute("""select p.id,p.content_session_id,p.prompt_text,p.created_at,p.created_at_epoch,coalesce(max(s.project),'(unknown)') project from user_prompts p left join sdk_sessions s on s.content_session_id=p.content_session_id group by p.id,p.content_session_id,p.prompt_text,p.created_at,p.created_at_epoch""").fetchall();c.close()
 except Exception as e:o["error"]=type(e).__name__;return o
 uniq={};recent=0
 for r in rows:
  when=epoch(r["created_at_epoch"]) or epoch(r["created_at"])
  if when is None or when<cutoff:continue
  recent+=1;t=clean(r["prompt_text"])
  if candidate(t):uniq[t]={"session":r["content_session_id"],"project":pname(r["project"]),"text":t}
 rec=list(uniq.values());projects=collections.Counter(x["project"] for x in rec)
 pats={k:sum(bool(re.search(rx,x["text"],re.I)) for x in rec) for k,rx in PATTERNS.items()}
 fric={k:sum(bool(re.search(rx,x["text"],re.I)) for x in rec) for k,rx in FRICTIONS.items()}
 o.update(recent_rows=recent,unique_authored_candidates=len(rec),sessions=len({x["session"] for x in rec}),projects=len(projects),patterns=pats,frictions=fric,top_projects=[{"name":n,"count":v,"container":n.lower() in CONTAINERS or n.lower().startswith("main.")} for n,v in projects.most_common(20)],notes=["exact-text deduplicated","known generated templates excluded","authored candidates are heuristic"]);return o

def codex(cutoff:float)->dict:
 idx=HOME/".codex/session_index.jsonl";o=stub("Codex",idx,"indexed parent sessions")
 items=[]
 try:
  if idx.exists():items=[json.loads(x) for x in idx.read_text(errors="replace").splitlines() if x.strip()]
  else:o["error"]="index not found";return o
 except Exception as e:o["error"]=type(e).__name__;return o
 recent=[]
 for x in items:
  if (epoch(x.get("updated_at")) or 0)>=cutoff:recent.append(x)
 candidates=[];imports=templates=scanned=0
 for x in recent:
  t=clean(x.get("first_user") or x.get("thread_name") or x.get("title"))
  path=Path(os.path.expanduser(x.get("path") or ""))
  imported=False
  if path.is_file():
   scanned+=1
   try:
    with path.open("rb") as f:imported=b"external-import-turn-" in f.read(2_000_000)
   except OSError:pass
  if imported:imports+=1;continue
  if not candidate(t):templates+=1;continue
  candidates.append(x)
 projects=collections.Counter(pname(x.get("cwd") or "(unknown)") for x in candidates)
 titles=[clean(x.get("thread_name") or x.get("title")) for x in candidates]
 notes=[]
 if scanned<len(recent):notes.append("raw-session paths unavailable for some rows; import exclusion is partial")
 o.update(recent_index_rows=len(recent),non_template_candidates=len(candidates),imports_excluded=imports,import_detection_coverage=f"{scanned}/{len(recent)}",templates_excluded=templates,projects=len(projects),top_projects=[{"name":n,"count":v,"container":n.lower() in CONTAINERS} for n,v in projects.most_common(12)],title_signals={"review":sum(bool(re.search(r"\b(review|audit|validate)\b",t,re.I)) for t in titles),"build":sum(bool(re.search(r"\b(build|create|fix|add|update)\b",t,re.I)) for t in titles)},notes=notes);return o

def tree_meta(name:str,path:Path,cutoff:float,kind:str)->dict:
 o=stub(name,path,kind)
 if not path.exists():o["error"]="directory not found";return o
 files=[]
 try:files=[x for x in path.rglob("*") if x.is_file() and x.stat().st_mtime>=cutoff]
 except OSError:o["error"]="scan failed";return o
 o.update(recent_files=len(files),markdown=sum(x.suffix.lower()==".md" for x in files),protobuf=sum(x.suffix.lower()==".pb" for x in files));return o

def kimi(cutoff:float)->dict:
 p=HOME/".kimi/sessions";o=stub("Kimi",p,"collapsed session metadata")
 if not p.exists():o["error"]="directory not found";return o
 wires=[]
 try:wires=[x for x in p.rglob("wire.jsonl") if x.stat().st_mtime>=cutoff]
 except OSError:o["error"]="scan failed";return o
 hashes=collections.Counter();retry=0
 for path in wires:
  prompt=""
  try:
   with path.open(errors="replace") as f:
    for _ in range(300):
     line=f.readline()
     if not line:break
     try:j=json.loads(line)
     except json.JSONDecodeError:continue
     if j.get("type")=="TurnBegin":
      payload=j.get("payload") if isinstance(j.get("payload"),dict) else j
      prompt=clean(payload.get("user_input") or payload.get("input") or payload.get("prompt"));break
  except OSError:pass
  if prompt:
   norm=re.sub(r"\b(?:retry|attempt|run)\s*#?\d+\b","retry",prompt,flags=re.I);hashes[hashlib.sha256(norm.encode()).hexdigest()]+=1;retry+=int(bool(re.search(r"\bretry\b",prompt,re.I)))
 o.update(recent_wire_sessions=len(wires),unique_parent_hashes=len(hashes),retry_marked=retry);return o

def hermes(cutoff:float)->dict:
 p=HOME/".hermes/state.db";o=stub("Hermes",p,"usage context")
 if not p.exists():o["error"]="database not found";return o
 try:c=ro(p);rows=c.execute("select source,model,message_count,tool_call_count,input_tokens,output_tokens from sessions where started_at>=?",(cutoff,)).fetchall();c.close()
 except Exception as e:o["error"]=type(e).__name__;return o
 plats=collections.Counter(str(r["source"] or "unknown") for r in rows)
 o.update(sessions=len(rows),messages=sum(int(r["message_count"] or 0) for r in rows),tool_calls=sum(int(r["tool_call_count"] or 0) for r in rows),input_tokens=sum(int(r["input_tokens"] or 0) for r in rows),output_tokens=sum(int(r["output_tokens"] or 0) for r in rows),platforms=plats.most_common(8),notes=["includes non-development sessions"]);return o

def recommendations(c:dict)->list[dict]:
 p=c.get("patterns",{});f=c.get("frictions",{});r=[]
 def add(title,why,rule):r.append({"title":title,"why":why,"rule":rule})
 if p.get("visual calibration",0)>=10:add("Rendered verification","Visual calibration recurs across projects.","For visual changes, inspect the existing surface before editing and verify rendered pixels after every meaningful change. Preserve unrelated accepted choices.")
 if p.get("narrow / preserve",0)>=10:add("Scoped diffs by default","Narrowing and preservation are repeated instructions.","Make only the requested change. Do not refactor, restyle, rename, or repair unrelated code without explicit approval.")
 if p.get("verify / test",0)>=10:add("Completion matrix","Verification requests recur, while generated summaries may overstate completion.","Report implemented, tested, built, visually/manually verified, live-read-back verified, released, documented, and blocked as separate states.")
 if p.get("delegate / second opinion",0)>=3:add("One integrator","Independent review helps, but agent volume is not progress.","Use bounded specialist reviewers and keep one owner responsible for reconciliation, execution, and final verification.")
 if p.get("workflow as product",0)>=10:add("Harness earning test","Agent infrastructure is a recurring workstream and diffusion risk.","Do not improve the harness unless a repeated measured bottleneck is named and the current product finish cycle becomes observably easier.")
 return r[:5]

def esc(v):return html.escape(str(v))
def source_cards(src):
 out=[]
 for s in src.values():
  ok=s.get("available") and not s.get("error");bits=[]
  for k in ("unique_authored_candidates","non_template_candidates","recent_files","recent_wire_sessions","sessions"):
   if k in s:bits.append(f"{k.replace('_',' ')}: {s[k]:,}")
  if "import_detection_coverage" in s:bits.append(f"import scan: {s['import_detection_coverage']}")
  out.append(f'<article class="source"><div><h3>{esc(s["name"])}</h3><span class="pill {"ok" if ok else "bad"}">{"available" if ok else "missing"}</span></div><p>{esc(s.get("kind",""))}</p><small>{esc(" · ".join(bits) or s.get("error","no recent data"))}</small></article>')
 return "".join(out)
def bar_rows(items,total):
 return "".join(f'<div class="bar"><div><span>{esc(k)}</span><b>{v:,}</b></div><i><em style="width:{min(100,100*v/total if total else 0):.1f}%"></em></i><small>{(100*v/total if total else 0):.1f}%</small></div>' for k,v in items)
def render(d):
 c=d["sources"].get("claude",{});n=c.get("unique_authored_candidates",0);p=c.get("patterns",{});f=c.get("frictions",{});projects=[x for x in c.get("top_projects",[]) if not x.get("container")][:12];mx=max([x["count"] for x in projects],default=1)
 proj="".join(f'<div class="project"><span>{esc(x["name"])}</span><i><em style="width:{100*x["count"]/mx:.1f}%"></em></i><b>{x["count"]}</b></div>' for x in projects) or '<p class="muted">No canonical-looking labels.</p>'
 friction="".join(f'<article class="friction"><b>{v}</b><div><h3>{esc(k)}</h3><p>Authored-prompt signal, not a verified root cause.</p></div></article>' for k,v in sorted(f.items(),key=lambda x:x[1],reverse=True) if v) or '<p class="muted">No recurring signals.</p>'
 rec="".join(f'<article class="rec"><strong>{i:02d}</strong><div><h3>{esc(x["title"])}</h3><p>{esc(x["why"])}</p><code>{esc(x["rule"])}</code></div></article>' for i,x in enumerate(d["recommendations"],1))
 start=dt.datetime.fromtimestamp(d["cutoff"]).astimezone();now=dt.datetime.fromtimestamp(d["generated_at"]).astimezone()
 return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agent Insights</title><style>
:root{{--ivory:#FAF9F5;--white:#fff;--slate:#141413;--clay:#D97757;--olive:#788C5D;--rust:#B04A3F;--oat:#E3DACC;--g1:#F0EEE6;--g3:#D1CFC5;--g5:#87867F;--g7:#3D3D3A;--serif:ui-serif,Georgia,serif;--sans:system-ui,-apple-system,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,monospace}}*{{box-sizing:border-box}}body{{margin:0;background:var(--ivory);color:var(--g7);font:15px/1.6 var(--sans)}}main{{max-width:1080px;margin:auto;padding:52px 26px 100px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:34px}}h1,h2{{font-family:var(--serif);font-weight:500;color:var(--slate)}}h1{{font-size:48px;line-height:1;margin:8px 0}}h2{{font-size:27px;margin:0}}h3{{margin:0;color:var(--slate);font-size:15px}}.eyebrow,.pill,small,footer{{font-family:var(--mono)}}.eyebrow{{font-size:11px;color:var(--clay);text-transform:uppercase;letter-spacing:.08em}}.muted,small{{color:var(--g5)}}section{{margin-bottom:52px}}hr{{border:0;border-top:1px solid var(--g3);margin:3px 0 20px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.stat,.source,.panel,.friction{{background:var(--white);border:1.5px solid var(--g3);border-radius:12px}}.stat{{padding:19px}}.stat b{{display:block;font:500 39px/1 var(--serif);color:var(--slate)}}.stat span{{font:10px var(--mono);text-transform:uppercase}}.thesis{{margin-top:16px;padding:20px;border-left:4px solid var(--clay);background:rgba(217,119,87,.06);font:21px/1.45 var(--serif)}}.sources{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.source{{padding:16px}}.source>div{{display:flex;justify-content:space-between;gap:8px}}.source p{{font-size:12px;color:var(--g5)}}.pill{{font-size:9px;padding:3px 7px;border-radius:99px}}.pill.ok{{background:rgba(120,140,93,.16);color:var(--olive)}}.pill.bad{{background:rgba(176,74,63,.12);color:var(--rust)}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.panel{{padding:21px}}.bar{{margin:0 0 15px}}.bar>div{{display:flex;justify-content:space-between}}.bar b,.project b{{font:11px var(--mono)}}.bar i,.project i{{display:block;height:7px;background:var(--g1);border-radius:99px;overflow:hidden}}.bar em{{display:block;height:100%;background:var(--clay)}}.bar small{{font-size:9px}}.project{{display:grid;grid-template-columns:1.5fr 3fr 35px;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--g1)}}.project em{{display:block;height:100%;background:var(--oat)}}.frictions{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.friction{{display:flex;gap:12px;padding:15px}}.friction>b{{font:500 28px/1 var(--serif);color:var(--rust)}}.friction p{{font-size:11px;color:var(--g5);margin:3px 0}}.rec{{display:grid;grid-template-columns:40px 1fr;gap:13px;padding:18px 0;border-bottom:1px solid var(--g3)}}.rec>strong{{font:11px var(--mono);color:var(--clay)}}.rec code{{display:block;margin-top:9px;padding:12px;background:var(--slate);color:#E8E6DF;border-radius:8px;font:12px/1.5 var(--mono)}}.caveats{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.caveat{{background:var(--oat);border-radius:12px;padding:17px}}footer{{border-top:1px solid var(--g3);padding-top:18px;font-size:10px;color:var(--g5)}}@media(max-width:800px){{.stats{{grid-template-columns:repeat(2,1fr)}}.sources{{grid-template-columns:1fr 1fr}}.two,.caveats{{grid-template-columns:1fr}}}}@media(max-width:520px){{main{{padding:34px 15px 70px}}header{{display:block}}h1{{font-size:38px}}.sources,.frictions{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div><div class="eyebrow">Private · aggregate only · no raw transcripts</div><h1>Agent Insights</h1><p class="muted">{start:%b %d, %Y} — {now:%b %d, %Y} · rolling {d["days"]} days</p></div><small>generated {now:%Y-%m-%d %H:%M}</small></header><section><div class="stats"><div class="stat"><b>{n:,}</b><span>authored candidates</span></div><div class="stat"><b>{c.get("sessions",0):,}</b><span>content sessions</span></div><div class="stat"><b>{c.get("projects",0):,}</b><span>project labels</span></div><div class="stat"><b>{sum(f.values()):,}</b><span>friction signals</span></div></div><div class="thesis">This report maps how development work is directed, where correction loops recur, and whether requests for implementation, verification, and shipping stay in balance.</div></section><section><h2>Source coverage</h2><hr><div class="sources">{source_cards(d["sources"])}</div></section><section class="two"><div><h2>How the work is directed</h2><hr><div class="panel">{bar_rows(sorted(p.items(),key=lambda x:x[1],reverse=True),n)}</div></div><div><h2>Project concentration</h2><hr><div class="panel">{proj}</div><p class="muted">Container-like labels are hidden; aliases remain noisy.</p></div></section><section><h2>Friction signals</h2><hr><div class="frictions">{friction}</div></section><section class="two"><div><h2>Requested completion signals</h2><hr><div class="panel">{bar_rows([("build / change",p.get("build / change",0)),("verify / test",p.get("verify / test",0)),("ship / release",p.get("ship / release",0))],n)}</div></div><div><h2>Interpretation boundary</h2><hr><div class="caveat"><strong>Requests are not outcomes.</strong><p>“Test”, “release”, and “deploy” prove intent only. Completion requires repository state, test output, rendered/manual inspection, or live read-back.</p></div></div></section><section><h2>Rules worth trying</h2><hr>{rec}</section><section><h2>What this report will not claim</h2><hr><div class="caveats"><div class="caveat"><strong>Not established</strong><ul><li>One preferred model</li><li>Unconditional autonomy</li><li>That each release happened</li><li>That terse agent feedback describes human relationships</li></ul></div><div class="caveat"><strong>Controls</strong><ul><li>Exact-text dedupe</li><li>Generated templates excluded</li><li>Codex imports excluded where detectable</li><li>No prompt bodies in HTML/JSON</li></ul></div></div></section><footer>Agent Insights v1 · local metadata + authored-prompt candidates · complements Hermes /insights telemetry</footer></main></body></html>'''
def check(path:Path)->dict:
 t=path.read_text(errors="replace");req=["<!doctype html>","Agent Insights","Source coverage","Friction signals","What this report will not claim"];missing=[x for x in req if x not in t];bad=sensitive_hits(t);return {"ok":not missing and not bad,"path":str(path),"bytes":len(t.encode()),"missing":missing,"sensitive_pattern_hits":bad}
def check_json(path:Path)->dict:
 try:data=json.loads(path.read_text(errors="replace"))
 except (OSError,json.JSONDecodeError) as e:return {"ok":False,"path":str(path),"error":type(e).__name__}
 bad=sensitive_hits(json.dumps(data,ensure_ascii=False));keys=forbidden_json_paths(data);return {"ok":not bad and not keys,"path":str(path),"sensitive_pattern_hits":bad,"forbidden_keys":keys}
def selftest():
 assert candidate("review and test");assert not candidate("<teammate-message> work");assert epoch(1_800_000_000_000)==1_800_000_000;assert pname("/Users/x/Playground/demo")=="demo";assert sensitive_hits("token ghp_abcdefghijklmnopqrstuvwxyz");assert forbidden_json_paths({"prompt_text":"secret"})==["$.prompt_text"];print(json.dumps({"ok":True,"tests":6}));return 0
def main():
 a=argparse.ArgumentParser();a.add_argument("--days",type=int,default=30);a.add_argument("--sources",default="claude,codex,gemini,kimi,hermes");a.add_argument("--output",type=Path,default=DEFAULT_HTML);a.add_argument("--json-output",type=Path,default=DEFAULT_JSON);a.add_argument("--open",action="store_true");a.add_argument("--check",type=Path);a.add_argument("--check-json",type=Path);a.add_argument("--self-test",action="store_true");x=a.parse_args()
 if x.self_test:return selftest()
 if x.check:
  q=check(x.check.expanduser());jp=x.check_json.expanduser() if x.check_json else x.check.expanduser().with_name("report-data.json");jq=check_json(jp) if jp.exists() else {"ok":False,"path":str(jp),"error":"not found"};result={"ok":q["ok"] and jq["ok"],"html":q,"json":jq};print(json.dumps(result,indent=2));return 0 if result["ok"] else 1
 if not 1<=x.days<=3650:a.error("--days must be 1..3650")
 now=dt.datetime.now(dt.timezone.utc).timestamp();cut=now-x.days*86400;want={z.strip() for z in x.sources.split(",")};collect={"claude":claude,"codex":codex,"gemini":lambda c:tree_meta("Gemini / Antigravity",HOME/".gemini/antigravity/brain",c,"artifact metadata"),"kimi":kimi,"hermes":hermes};unknown=want-set(collect)
 if unknown:a.error("unknown sources: "+",".join(sorted(unknown)))
 src={k:collect[k](cut) for k in collect if k in want};d={"schema_version":1,"generated_at":now,"cutoff":cut,"days":x.days,"sources":src};d["recommendations"]=recommendations(src.get("claude",{}));out=x.output.expanduser();js=x.json_output.expanduser();private_write(out,render(d));private_write(js,json.dumps(d,ensure_ascii=False,indent=2));q=check(out);jq=check_json(js);valid=q["ok"] and jq["ok"];summary={"ok":valid,"report":str(out),"data":str(js),"days":x.days,"sources":{k:{"available":v.get("available",False),"error":v.get("error")} for k,v in src.items()},"validation":{"html":q,"json":jq}};print(json.dumps(summary,ensure_ascii=False,indent=2));
 if x.open and valid:webbrowser.open(out.as_uri())
 return 0 if valid else 1
if __name__=="__main__":raise SystemExit(main())
