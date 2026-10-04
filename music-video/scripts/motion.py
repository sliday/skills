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
    if sid in ("c39", "c40"): cont.append("the bears are asleep: their eyes stay CLOSED the whole time")
    elif bears and s["t0"] >= 19.3: cont.append("the bears' eyes keep glowing witchy green the whole time (they are hypnotised by the moth)")
    if bears: cont.append("the bears keep their grey ushankas with red stars and their bagels")
    txt = (sh["prompt"]["start"] + " ".join(acts)).lower()
    t2 = txt.replace("flame-shaped", "").replace("blazing", "").replace("blazes", "")
    if any(k in t2 for k in ("fire", "flame", "burn", "bomb", "shell", "explos")): cont.append("all fire is flat painted Khokhloma lacquer ornament (scarlet and gold curling flame-leaves and berries outlined on black) exactly as painted in the opening frame; it moves ONLY by its painted flame-leaves swaying and new painted leaves and berries unfurling, like a lacquer pattern growing; NO realistic yellow or orange flame tongues, no photographic fire, no flickering real flames at any moment; it never spreads onto the characters or the vehicle")
    else: cont.append("there is NO fire anywhere in this shot: no flames, no sparks, no glowing ornaments appear")
    if s["t0"] < 76.5: cont.append("forest act: no houses, villages or churches appear anywhere")
    op = pr["camera"]["operation"]; trike = bool(pr.get("prop_ids"))
    if trike: cont.append("the war-trike keeps exactly the decoration it has in the opening frame: olive riveted steel with a Khokhloma ornament panel on the sidecar side and front mudguard; no stars, no extra flowers, no fire and no new decorations appear on it")
    move = ""
    if op in ("tracking", "truck_left", "truck_right") and trike:
        move = ("The vehicle is really travelling fast: the camera moves alongside it, so the background trees, houses and hills stream past quickly in the opposite direction with strong parallax, the ground and puddles rush by underneath, the wheels spin, mud and water fly backwards off the tyres, the flag whips. ")
    elif op in ("tracking", "truck_left", "truck_right", "dolly_in", "dolly_out", "zoom_out", "pedestal"):
        move = f"The camera really moves ({pr['camera']['instruction']}) with clear parallax between near and far layers. "
    EXTRA = {"c40": "the whole group stays fully in frame at the same size the whole time (no zoom, no push-in); the small moth flutters down and hides between the sleeping father and mother bear, peeking out", "c19": "the tiny people and little elephants run FORWARD in the direction they face, to the right, away from the trike: real running with legs moving forward, they never walk backwards and never turn back toward the trike; the trike follows them and rolls over the houses behind them", "c13": "the bottle starts IN the cub's raised paw; real throwing physics: the arm swings forward, the bottle leaves the paw, travels one short arc under gravity, lands in the fire and disappears into it; it never hangs or hovers in the air; the fire grows ONLY by unfurling more flat painted Khokhloma flame-leaves and berries, like a lacquer ornament growing; no realistic yellow flame tongues, no real fire, no flickering photographic flames at any moment", "c14": "the camera barely moves; the bears stay standing in this same night forest clearing beside the parked trike the whole time (nobody gets on the trike, the trike does not move); the father bear swings a big paw at the deer and stamps toward the squirrels; the deer and squirrels turn and run away out of the frame to the right and do not come back; it stays night, the same dark forest, no daylight, no village, no new landscape", "c08": "ONLY the tarpaulin cloth, the father's arm and the headlamp light change. The war-trike does not move at all and every part of it stays exactly as in the opening frame: same samovar at the same size and place, same banner, same pipes; no object rises, flies, grows, appears or disappears. The mother stands still holding the icon."}
    if sid in EXTRA: cont.insert(0, EXTRA[sid])
    end = sh["prompt"]["end"]
    # --- time-coded beat schedule spread over the WHOLE clip (fixes hold-then-act / act-then-freeze) ---
    beats = list(acts)
    if sid in EXTRA: beats = beats  # EXTRA goes into continuity
    if len(beats) > 3: beats = [beats[0], beats[1], "; ".join(beats[2:])]
    marks = {1: [(0, 1.0)], 2: [(0, .45), (.45, 1.0)], 3: [(0, .3), (.3, .65), (.65, 1.0)]}[max(1, len(beats))]
    tl = "; ".join(f"{a*dur:.1f}-{b*dur:.1f}s: {beat}" for (a, b), beat in zip(marks, beats))
    amb = ["rain keeps falling" if sid not in ("c02", "c04", "c05") else "rain streams down the window"]
    if trike: amb.append("the red banner flutters")
    if any(k in t2 for k in ("fire", "flame", "burn", "bomb", "shell")): amb.append("the ornament fire keeps swaying")
    LOCKED = {"c39", "c40", "c34", "c16"}
    amb.append("the camera stays completely still on the same wide framing" if sid in LOCKED else "the camera keeps drifting very slightly")
    cap_short = cap if len(cap) <= 900 else cap[:900].rsplit(" ", 1)[0] + "..."
    opener = (f"A single continuous {dur}-second shot filmed from a LOCKED-OFF CAMERA ON A TRIPOD: the framing never changes at all (no zoom, no push-in, no pan, no tilt). Gentle movement inside the frame continues from the first frame to the last, with no frozen hold: " if sid in LOCKED else
              f"A single continuous {dur}-second shot that is IN MOTION from the very first frame to the very last frame: no still hold at the start and no freeze at the end; the action fills the whole duration at an even, lively pace. ")
    prompt = (opener +
              f"TIMELINE: {tl}; and by {dur:.1f}s: {end}, while the movement still continues. "
              f"THROUGHOUT: " + ", ".join(amb) + ". "
              + move +
              f"CAMERA: {pr['camera']['instruction']}. "
              f"THE OPENING FRAME shows: {cap_short} "
              "Anything frozen mid-motion in the opening frame (splashes, flying dirt, debris, smoke) continues its motion naturally and settles. "
              "CONTINUITY: " + "; ".join(cont) + ". "
              "STYLE: a naive oil painting on woven canvas brought to life; brush texture and canvas weave stay visible; clear, readable, continuous movement; no text, no letters, no photorealism, no 3D look.")
    out[sid] = {"prompt": prompt, "duration": dur}
json.dump(out, open("docs/motion.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "prompts; max len", max(len(v["prompt"]) for v in out.values()))
print(out["c19"]["prompt"][:1400])
