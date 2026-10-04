#!/usr/bin/env python3
"""motion.py -- build literal, caption-grounded h3 motion prompts -> docs/motion.json"""
import json, re
P = json.load(open("project.json")); S = {s["id"]: s for s in json.load(open("docs/shots.json"))}
out = {}
for sh in P["shots"]:
    sid = sh["id"]; s = S[sid]; pr = sh["prompt"]; cast = pr["closed_cast"]
    cap = open(f"keyframes/{sid}_start.caption.txt").read().strip()
    cap = re.sub(r"\s+", " ", cap)
    acts = pr["action"]; main = acts if len(acts) <= 2 else [acts[0], acts[-1]]
    dur = int(min(10, max(5, round(s["dur"] + 0.4))))
    bears = any(c in ("big", "she", "cub") for c in cast) or bool(pr.get("prop_ids"))
    cont = ["every character and object keeps exactly the appearance it has in the opening frame",
            "nobody new enters the frame and nobody disappears"]
    if bears and s["t0"] >= 19.3: cont.append("the bears' eyes keep glowing witchy green the whole time (they are hypnotised by the moth)")
    if bears: cont.append("the bears keep their grey ushankas with red stars and their bagels")
    txt = (sh["prompt"]["start"] + " ".join(acts)).lower()
    if any(k in txt for k in ("fire", "flame", "burn", "bomb", "blaze", "shell")): cont.append("all fire stays flat decorative Khokhloma ornament (red and gold curling flame-leaves), it grows and sways but never becomes realistic flames")
    op = pr["camera"]["operation"]; trike = bool(pr.get("prop_ids"))
    if trike: cont.append("the war-trike's body stays plain olive-green riveted steel with rust patches exactly as in the opening frame; no painted flowers or new decorations appear on it")
    move = ""
    if op in ("tracking", "truck_left", "truck_right") and trike:
        move = ("The vehicle is really travelling fast: the camera moves alongside it, so the background trees, houses and hills stream past quickly in the opposite direction with strong parallax, the ground and puddles rush by underneath, the wheels spin, mud and water fly backwards off the tyres, the flag whips. ")
    elif op in ("tracking", "truck_left", "truck_right", "dolly_in", "dolly_out", "zoom_out", "pedestal"):
        move = f"The camera really moves ({pr['camera']['instruction']}) with clear parallax between near and far layers. "
    end = sh["prompt"]["end"]
    prompt = (f"OPENING FRAME, exactly what is painted: {cap} "
              f"CAMERA: {pr['camera']['instruction']}. "
              f"WHAT HAPPENS over {dur} seconds, as real continuous movement through time (not a morph, not a dissolve, not a slideshow): " + "; then ".join(main) + ". "
              f"By the end: {end}. " + move +
              "Anything frozen mid-motion in the opening frame (splashes, flying dirt, debris, smoke, sparks) continues its motion naturally: it falls, settles, drifts away; rain keeps falling. "
              "CONTINUITY: " + "; ".join(cont) + ". "
              "STYLE: a naive oil painting on woven canvas comes to life; the brush texture and canvas weave stay visible; simple, deliberate, slightly awkward movement like a living painting; no text, no letters, no photorealism, no 3D look.")
    out[sid] = {"prompt": prompt, "duration": dur}
json.dump(out, open("docs/motion.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "prompts; max len", max(len(v["prompt"]) for v in out.values()))
print(out["c19"]["prompt"][:1400])
