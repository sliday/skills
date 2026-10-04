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
    t2 = txt.replace("flame-shaped", "").replace("blazing", "").replace("blazes", "")
    if any(k in t2 for k in ("fire", "flame", "burn", "bomb", "shell", "explos")): cont.append("all fire stays flat decorative Khokhloma ornament (red and gold curling flame-leaves) and stays exactly where it is in the opening frame; it grows and sways but never becomes realistic flames and never spreads onto the characters or the vehicle")
    else: cont.append("there is NO fire anywhere in this shot: no flames, no sparks, no glowing ornaments appear")
    if s["t0"] < 76.5: cont.append("forest act: no houses, villages or churches appear anywhere")
    op = pr["camera"]["operation"]; trike = bool(pr.get("prop_ids"))
    if trike: cont.append("the war-trike keeps exactly the decoration it has in the opening frame: olive riveted steel with a Khokhloma ornament panel on the sidecar side and front mudguard; no stars, no extra flowers, no fire and no new decorations appear on it")
    move = ""
    if op in ("tracking", "truck_left", "truck_right") and trike:
        move = ("The vehicle is really travelling fast: the camera moves alongside it, so the background trees, houses and hills stream past quickly in the opposite direction with strong parallax, the ground and puddles rush by underneath, the wheels spin, mud and water fly backwards off the tyres, the flag whips. ")
    elif op in ("tracking", "truck_left", "truck_right", "dolly_in", "dolly_out", "zoom_out", "pedestal"):
        move = f"The camera really moves ({pr['camera']['instruction']}) with clear parallax between near and far layers. "
    EXTRA = {"c13": "the bottle starts IN the cub's raised paw; real throwing physics: the arm swings forward, the bottle leaves the paw, travels one short arc under gravity, lands in the fire and disappears into it; it never hangs or hovers in the air; the fire grows ONLY by unfurling more flat painted Khokhloma flame-leaves and berries, like a lacquer ornament growing; no realistic yellow flame tongues, no real fire, no flickering photographic flames at any moment", "c14": "the father bear swings a big paw at the deer and stamps toward the squirrels; the deer and squirrels turn and run away out of the frame to the right and do not come back", "c08": "ONLY the tarpaulin cloth, the father's arm and the headlamp light change. The war-trike does not move at all and every part of it stays exactly as in the opening frame: same samovar at the same size and place, same banner, same pipes; no object rises, flies, grows, appears or disappears. The mother stands still holding the icon."}
    if sid in EXTRA: cont.insert(0, EXTRA[sid])
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
