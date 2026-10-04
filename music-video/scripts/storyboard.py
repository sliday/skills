#!/usr/bin/env python3
"""BERLOGA 2 storyboard: single source of truth -> project.json (storyboard-to-video, author mode) + docs/shots.json."""
import json, hashlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
STYLE = (ROOT / "bibles/STYLE.txt").read_text().strip()
SHEET = {"family": "bibles/char/oil_family.jpeg", "moth": "bibles/char/moth_fix.jpeg", "trike": "bibles/char/trike_khokh.jpeg", "world": "bibles/char/oil_world.jpeg", "samovar": "bibles/char/samovar_v2.jpeg"}
STYLE_REFS = ["bibles/char/library.jpeg", "source/refs/style/s1_bears_bed.png"]
SHEET_DESC = {"family": "the bear family and cat character sheet", "moth": "the moth model sheet (the one moth in all its formats, including the sky-covering super-moth)", "trike": "the war-trike model sheet (one exact vehicle from five angles)", "samovar": "the samovar and top-mortar props sheet (ignore the realistic bear in it; bears come only from the family sheet)", "world": "the world sheet (Rozh, Jesus-airplane, onion churches, elephants, flying man, trees, houses, tiny people)"}
CAST = {
 "big": "FATHER BEAR from the family sheet (largest; heavy brown; crooked-teeth deadpan grimace; grey ushanka with red star; CROSSED bagel bandoliers; plain vodka bottle in paw)",
 "she": "MOTHER BEAR from the family sheet (0.85 of father; reddish-brown; stern narrowed eyes; grey ushanka with red star; black shawl cut from the den rug, woven with symmetrical Khokhloma ornament of scarlet berries and golden leaves, short red fringe)",
 "cub": "the CUB from the family sheet (0.5 of father; round caramel bear child; oversized ushanka with red star over his brows; one-bagel pendant; balalaika on a strap)",
 "cat": "the CAT from the family sheet (fat grey-and-rust striped tabby, flat deadpan face, half-closed eyes, always sitting or walking BACKWARDS)",
 "moth": "THE MOTH from the moth sheet (pale grey-brown patterned wings, long feathery antennae, two tiny dark eyes, no mouth)",
 "rozh": "ROZH from the world sheet (sad big-headed man, thin dark hair, heavy tired eyes, drooping lower lip showing teeth, small body, tiny hands, pale grey-green shirt)",
 "jesus_plane": "the JESUS-AIRPLANE from the world sheet (pale grey rounded toy airplane with Jesus lying along it, arms along the wings, two small propellers, soft white halo-glow)",
 "winged": "the FLYING MEN from the world sheet (barefoot, long pale blue-grey shirts, curly brown hair, flying horizontally, wings of a few single white feathers sticking out in tufts)",
}
PROPS_DESC = "the WAR-TRIKE from the trike sheet (patched olive sidecar motorcycle, brass samovar fuel tank, eye-like headlamp, organ-pipe exhausts, plain torn red banner with NO symbol, crate of bagels and bottles; NO statue or bust)"

def rules(t0, sid, cast, has_trike):
    act = ("FOREST ACT: only dark forest, road, den, fields and sky; NO villages, houses or tiny people; trees are tall."
           if t0 < 76.5 else
           "GIANT ACT: the world is tiny; the bears (when present) are colossal; houses reach only their ankles; tiny people are ant-sized marks of a few strokes; one trike wheel is as tall as a two-storey house; rivers are ankle-deep for them.")
    season = ("SEASON: filthy cold early WINTER: grey sky, snow falling, frost, dirty snow and sooty ice." if sid in ("c41",)
              else "SEASON: wet late AUTUMN: dark mud, bare wet ground, cold rain; absolutely NO snow, NO frost, NO ice." if sid != "c40"
              else "SEASON: wet late autumn turning into the first snow of winter.")
    bears = any(c in ("big", "she", "cub", "cat") for c in cast) or has_trike
    nobody = "" if bears else " ABSOLUTELY NO bears, NO bear paws, NO cat and NO motorcycle anywhere in this frame; the bears are elsewhere."
    canon = ("CAST SCALE CANON: father bear = 1.0 height; mother bear = 0.85; cub = 0.5; cat sitting = 0.35; the war-trike is 1.6 father-bears long with its seat at his hip, and all four ride it together. " if bears else "")
    hyp = (" HYPNOSIS RULE: the bears' eyes glow witchy pale green (hypnotised by the moth) in every frame from now on." if bears and t0 >= 19.3 else (" The bears' eyes are closed (asleep)." if bears else ""))
    nocat = (" The CAT is NOT in this frame." if bears and "cat" not in cast else "")
    if "she" in cast and t0 >= 115: nocat += " ICON STATE: the moth has LEFT the icon: the mother bear holds an EMPTY ornate gold-red-green icon frame (plain pale canvas inside, no moth painted in it)."
    elif "she" in cast and 19.3 <= t0 < 109: nocat += " ICON STATE: the mother bear holds the moth icon with the moth painted inside it, glowing faintly green."
    return (f"{canon}{act} {season}{hyp}{nocat} ICON RULE: the only icon anywhere is the moth icon; no saints, no Madonna, no other religious pictures."
            + (" SEATING RULE (whenever they ride the war-trike): the FATHER bear always drives, paws on the handlebars; the MOTHER bear always rides pillion directly behind him holding the moth icon; the CUB always sits in the sidecar with his balalaika and NEVER drives; the CAT always sits BACKWARDS on the front nose of the sidecar behind the Maxim gun. " if has_trike else "") + " UNIQUENESS RULE: the moth icon exists only once (if a bear holds it, it is NOT on the wall); every character appears EXACTLY ONCE in the frame: one father, one mother, one cub, one cat; never duplicates, never twins, never the same character both riding and standing; the war-trike appears at most once. ANATOMY RULE: every bear and the cat has clear, readable anatomy: one head firmly attached to the top of the torso by a neck, two arms from the shoulders, two legs from the hips, the pose readable as a silhouette; never a flat rug-like body, never a head floating on the belly, never extra or missing limbs; lying or sleeping bears are slumped SITTING against something with the head dropped onto the chest. FIRE RULE: any fire, flame, explosion or blaze is flat decorative KHOKHLOMA folk ornament (curling scarlet, vermilion and gold flame-leaves, berries and tendrils on black smoke), never realistic fire."
            " HOUSE RULE: every house is a crude naive box with heavily distorted wrong perspective (leaning walls, roof tilted toward the viewer, mismatched windows). CHURCH RULE: every church is an ONION church: whitewashed blocks with domes that are literal brown-gold onion bulbs with tall green onion sprouts; never a spire."
            " TREE RULE: trees are tall dark soft flame-shaped silhouettes like blurred dark cypresses, in small groups."
            " HAT RULE: every bear always wears his grey ushanka with a red star and his own bagels exactly as on the family sheet; never bare-headed. BOTTLE RULE: every bottle is the same plain unlabeled clear half-litre bottle whose length equals the width of the father bear's muzzle."
            " DETAIL RULE: soft, simplified, rounded forms, smoky edges, broad brushwork, few details; no fine fur strands, no engraving hatching, no clutter."
            f" NO TEXT: no letters, numbers, words or symbols on any sign, banner or object.{nobody}")

# id, t0, t1, beats, cast, trike, sheets, camera(op, instruction), start, mid (None|(frac, change)), end (None|change), actions[], vref (None|v1 clip path)
S = [
 ("c01", 0.0, 7.8, ["sb01"], [], False, ["world"], ("dolly_in", "very slow push in toward the den door"),
  "Night: a dark forest of tall flame-shaped trees in the rain; a huge mossy den mound like a sleeping hill with a small grey Soviet apartment-stairwell door and one warm yellow window; a low pale moon with only the faint suggestion of a sleepy face", None, None,
  ["rain falls steadily", "the dark trees sway gently in the wind", "the yellow window flickers once"], None),
 ("c02", 7.8, 19.3, ["sb01", "sb02"], ["big", "she", "cub", "moth"], False, ["family", "moth", "world"], ("locked", "static interior"),
  "Inside the cramped den at night: the three bears asleep in one bed under a patterned blanket, all still wearing their ushankas, the father snoring with the vodka bottle on his chest; on the wall above them a patterned rug, the MOTH ICON in its ornate gold-red-green frame, and a shelf with seven white porcelain elephants; an old radiator and an enamel mug",
  None, "the moth in the icon now radiates a witchy pale green-white glow that spills over the sleeping bears' faces",
  ["the bears sleep and breathe slowly, blanket rising and falling", "the moth inside the icon starts to glow, faint at first", "its wings twitch inside the frame and the glow grows strong", "green-white light creeps over the sleeping bears' faces"], None),
 ("c04", 19.3, 23.1, ["sb02"], ["big", "she", "cub"], False, ["family"], ("locked", "static medium"),
  "The three bears sitting bolt upright in their bed like zombies, arms hanging forward, eyes blank and reflecting green glow, ushankas on their heads, the green light of the icon falling on them from the left",
  None, "the three bears have climbed out of bed and are walking like sleepwalkers, arms stretched forward, all turned toward the low wooden den door at the far RIGHT of the room, their backs half to the icon",
  ["the bears sit up stiffly at the same moment", "they swing their legs out of bed like puppets", "they turn toward the den door and shuffle toward it like sleepwalkers"], None),
 ("c05", 23.1, 26.85, ["sb03", "sb06"], ["big", "she", "cub", "moth"], False, ["family", "moth"], ("locked", "static medium"),
  "Inside the den, the bears have already climbed OUT of bed and stand on the wooden floor in front of the bed, on the side nearest the low den door at the right: the MOTHER BEAR reaches up and lifts the glowing moth icon down from the wall with both paws, reverently, like a holy relic; behind her the FATHER BEAR slinging strings of golden bagels across his chest; the CUB tying on his one-bagel pendant",
  None, "the mother bear holds the glowing icon in front of her chest with both paws like a relic; on the wall where the icon hung there is now only a BARE NAIL and a paler empty rectangle on the dark planks (the icon is no longer on the wall); the father's bagel bandoliers are crossed on his chest",
  ["the mother bear raises the icon off its nail and lowers it to her chest", "the father loops bagel strings over his shoulders into crossed bandoliers", "the cub straightens his too-big hat"], None),
 ("c06", 26.85, 30.45, ["sb04"], ["big", "she", "cub", "moth"], False, ["family", "moth"], ("locked", "static wide"),
  "Night, rain: the small grey stairwell door of the den mound swings open; the three bears squeeze out one by one into the rain, the mother first holding the glowing moth icon before her like a lantern, the father scratching his belly, the cub stretching",
  None, "the three bears stand outside in the rain in a row; the father's cheeks are puffed out in an enormous burp",
  ["the door swings open", "the mother steps out holding the glowing icon high", "the father follows and lets out an enormous burp, cheeks puffing", "the cub stretches his arms"], None),
 ("c07", 30.45, 34.2, ["sb05", "sb12"], ["cat"], False, ["family", "trike"], ("locked", "static medium"),
  "Next to the den mound, a low dark wooden CELLAR door stands open; the fat striped CAT comes out of the cellar WALKING BACKWARDS, facing the dark doorway, hauling the brass wheeled MAXIM machine gun out of the cellar by its trail handle; the gun's front wheels are still inside the dark doorway",
  None, "the machine gun is fully out of the cellar on the wet path, the cat sitting beside it backwards, looking over its shoulder, unimpressed",
  ["the cat heaves backwards step by step", "the Maxim gun rolls out of the dark cellar doorway", "the cat sits down beside it, glancing back over its shoulder"], None),
 ("c08", 34.2, 37.7, ["sb05"], ["big", "she"], True, ["family", "trike"], ("locked", "static wide"),
  "Wide side view in the rain by the den: the WAR-TRIKE stands parked in the centre, facing right, completely on-model and clearly visible (samovar fuel tank, round headlamp unlit, handlebars, three exhaust pipes, knobbly wheels, red banner); ONLY its seat, sidecar tub and bagel crate are covered by one loose, sagging olive canvas tarpaulin. The FATHER bear stands at the LEFT, behind the trike, holding the back corner of the tarp in one paw; the MOTHER bear stands at the RIGHT, holding the glowing moth icon against her chest with both paws",
  None, "the tarpaulin lies crumpled on the mud behind the trike; the trike is unchanged and fully uncovered; its round headlamp is now lit",
  ["the father bear pulls the tarp straight backwards off the seat and sidecar and drops it on the mud behind the trike", "the trike's round headlamp switches on"], None),
 ("c09", 37.7, 41.62, ["sb05"], ["big", "she", "cub", "cat", "moth"], True, ["family", "trike", "moth"], ("locked", "static wide"),
  "Everyone mounted on the WAR-TRIKE in the dark forest: FATHER driving, MOTHER behind him holding the glowing moth icon, the CUB in the sidecar with his balalaika, the CAT sitting BACKWARDS on the sidecar nose behind the Maxim gun",
  None, "grey exhaust smoke puffs from the organ-pipe exhausts and the trike lurches forward a little",
  ["the father kicks the starter with his heel", "the exhaust pipes cough out rings of grey smoke", "the whole trike shakes, the cub bouncing in the sidecar"], "clips/v1/b09_h3.mp4"),
 ("c10", 41.62, 45.05, ["sb07"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("truck_left", "side tracking shot moving with the trike"),
  "Side view: the WAR-TRIKE with all four riders roaring left to right along a dark muddy forest road between flame-shaped trees, mud spraying from the wheels, the red banner whipping",
  None, None,
  ["the trike drives fast from left to right", "mud sprays from the wheels in arcs", "the banner whips", "the riders bounce"], "clips/v1/b11_h3.mp4"),
 ("c11", 45.05, 47.81, ["sb07"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("locked", "static wide"),
  "HEAD-ON FRONT VIEW from low on the road: the war-trike charges straight TOWARD the viewer up a forest road that climbs like a theatre stage, its single eye-like headlamp blazing in the centre of the frame, the father bear at the handlebars facing us, the mother behind him, the cub peeking from the sidecar on the left, the cat backwards on the sidecar nose; leaning dark flame-shaped trees on both sides; NOT a side view",
  None, None, ["the trike climbs the road toward camera", "the headlamp beam swings", "the trees on their layers lean aside as it passes"], None),
 ("c12", 47.81, 51.77, ["sb07", "sb14"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("locked", "static wide"),
  "The WAR-TRIKE plows straight through the dark forest, snapping flame-shaped trees like matchsticks; a deer and three squirrels flee to the right; the father tosses an empty bottle and bagel crumbs fly behind",
  None, "a long path of broken, toppled trees behind the trike; the animals gone",
  ["trees topple one after another", "the deer and squirrels bolt out of frame to the right", "the empty bottle spins away"], "clips/v1/b13_h3.mp4"),
 ("c13", 51.77, 56.31, ["sb10", "sb17"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("locked", "static wide"),
  "By the forest road at night: the bears on the parked trike laugh and burp beside a roadside campfire painted as flat Khokhloma ornament fire; the CUB stands by the fire holding an empty bottle high in his raised paw, about to throw it, the bottle still in his paw (nothing in the air yet); heavy rain falls INTO the fire",
  None, "the Khokhloma ornament fire has grown about twice as tall, still a flat painted pattern of red-and-gold flame-leaves and berries",
  ["the cub throws the bottle: it leaves his paw, flies in a short low arc and drops into the fire", "the ornament fire grows about twice as tall by unfurling more flat painted Khokhloma flame-leaves and berries while the bears throw their heads back laughing"], None),
 ("c14", 56.31, 65.52, ["sb10", "sb14"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("truck_right", "very slow lateral camera drift to the right"),
  "The bears have climbed off the trike at a forest clearing in the rain: the FATHER drinks from his bottle and smokes a thin cigarette, the MOTHER holds the glowing icon, the CUB sits on a stump; a curious deer and two squirrels approach from the right",
  (0.5, "the father bear swats at the deer with a huge paw and the mother bear stamps her foot at the squirrels; the animals recoil in fright"),
  "the deer and squirrels are fleeing far away to the right; the father drinks again, the mother looks after them with contempt",
  ["the father drinks and puffs smoke", "the deer and squirrels creep closer, curious", "the father swats, the mother stamps", "the animals flee in panic to the right", "the father takes another swig"], None),
 ("c15", 65.52, 68.98, ["sb07"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("dolly_out", "slow pull back"),
  "The WAR-TRIKE with all four riders stops at the edge of the dark forest on a rise; below them stretches a wide golden RYE FIELD under the rainy night sky; the bears look out over it deadpan",
  None, None, ["the trike rolls to a stop", "the bears turn their heads slowly to look at the rye field", "rain sweeps across the rye"], None),
 ("c16", 68.98, 72.68, ["sb21"], ["rozh"], False, ["world"], ("locked", "static close-up"),
  "CLOSE-UP: ROZH fills most of the frame, his big sad head and shoulders centred, standing chest-deep in the golden rye field at night in the rain, looking straight at the viewer, drooping lower lip, tired eyes; rain on his face; the dark forest edge and sky behind him are small and simple",
  None, "a huge dark shadow has slid across the rye and over Rozh; he has not moved at all",
  ["rain falls on Rozh", "a giant shadow slowly passes over the rye and over him", "he does not move; only his eyes blink once, slowly"], None),
 ("c17", 72.68, 76.53, ["sb10"], ["big", "she", "cub", "cat"], False, ["family"], ("locked", "static medium"),
  "The three bears hugging clumsily like brothers in the rain, the father and mother clinking plain bottles, their bagel strings tangled together, the cub squeezed in the middle; the cat sits backwards beside them",
  None, None, ["the bears clink bottles", "they sway together in a heavy hug", "the cub's hat slips over his eyes"], None),
 ("c18", 76.53, 80.25, ["sb08", "sb23"], ["big", "she", "cub", "cat"], True, ["family", "trike", "world"], ("dolly_out", "slow pull back to reveal scale"),
  "Close shot: the war-trike with all four riders seen against the dark rainy night sky and dark field edge only; the frame is filled by the trike and the bears; NO village, houses or people visible yet",
  None, "the camera has pulled far back: the bears and the war-trike are GIANTS; a whole tiny village of crude distorted houses and onion churches lies at their feet; ant-sized people and little grey elephants start running away",
  ["the camera pulls back far and fast, revealing the tiny village at their feet"], None),
 ("c19", 80.25, 83.65, ["sb08"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("tracking", "low tracking shot moving right alongside the wheel"),
  "Low view: the war-trike with all four riders on the LEFT third of the frame, its enormous knobbly front wheel just touching the first of a row of INTACT tiny crude houses with warm lit windows that stretches ahead of it to the right; tiny people and little grey elephants in the street ahead, not yet running",
  None, "the row of houses is flattened like paper behind the wheel",
  ["the war-trike drives forward to the right, its wheels turning, rolling over the row of houses and flattening each one like paper as it passes", "tiny people and elephants flee ahead of it"], "clips/v1/b19_h3.mp4"),
 ("c20", 83.65, 87.52, ["sb08", "sb12"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("locked", "static wide"),
  "The giant war-trike with all four riders in their seats drives straight through a wide river, the water only up to its wheel hubs, a big bow wave spraying; the cat sits backwards on the sidecar nose firing the Maxim gun into the sky, tracers like shooting stars; tiny boats and tiny houses on the banks",
  None, None, ["the trike ploughs through the river from left to right", "a bow wave sprays up from the wheels", "the cat fires and tracers streak upward", "tiny boats rock in the wave"], "clips/v1/b21_h3.mp4"),
 ("c21", 87.52, 91.22, ["sb11"], ["she"], False, ["family", "trike"], ("locked", "static medium"),
  "The giant MOTHER BEAR aims the brass SAMOVAR FLAMETHROWER, painted with red-and-gold Khokhloma flowers, at a tiny crude house; a stream of flat ornamental Khokhloma fire pours from its spout; tiny people with tiny buckets try to put it out",
  None, "the house is wrapped in tall curling Khokhloma flame-leaves; the tiny buckets do nothing",
  ["the ornamental fire pours from the spout", "it curls over the house", "the tiny people throw tiny buckets of water, which only make it grow"], "clips/v1/b24_h3.mp4"),
 ("c22", 91.22, 94.64, ["sb17"], [], False, ["world"], ("locked", "static insert"),
  "Close insert of a bonfire in the mud at night: the fire is flat Khokhloma ornament (curling scarlet and gold flame-leaves and berries) and heavy rain falls into it",
  None, "the ornamental fire is twice as tall, every raindrop having made it flare",
  ["raindrops fall into the fire", "each drop makes a new ornamental flame-leaf unfurl", "the fire grows"], None),
 ("c23", 94.64, 97.38, ["sb11", "sb10"], ["big", "she", "cub", "cat"], True, ["family", "trike", "world"], ("truck_right", "side tracking shot"),
  "The giant war-trike with all four riders rolls through a burning village at night; Khokhloma ornament fire burns in every tiny window and on the onion churches; the bears laugh with mouths wide open",
  None, None, ["the trike rolls from left to right", "ornamental fire bursts from the roofs", "the bears laugh"], None),
 ("c24", 97.38, 101.39, ["sb09"], ["cub"], True, ["family", "trike"], ("locked", "static medium"),
  "The CUB in the sidecar of the stopped war-trike leans over and stares down at the muddy road, where a small broken MUSIC BOX lies open with its tiny ballerina bent sideways",
  None, "the cub has climbed out of the sidecar and crouches over the music box",
  ["the cub notices something and leans over the side", "he climbs out of the sidecar", "he crouches down over the music box"], None),
 ("c25", 101.39, 105.81, ["sb09"], ["cub"], False, ["family", "trike"], ("dolly_in", "slow push in"),
  "Close-up: the CUB (exactly the cub from the family sheet: same crooked-teeth bear muzzle as his parents, oversized ushanka with red star, one-bagel pendant) crouching in the mud holding the small broken music box in both big paws; the tiny ballerina stands bent on one leg; his face is soft and curious for the first time, eyes wide; rain",
  None, "the ballerina has turned slowly half a circle on her broken spring; the cub smiles a little",
  ["the cub lifts the music box closer", "the tiny ballerina slowly turns on her bent spring", "the cub's face softens into a small smile"], None),
 ("c26", 105.81, 109.0, ["sb09"], ["she", "cub"], False, ["family"], ("locked", "static medium"),
  "The MOTHER BEAR looms over the crouching CUB, who holds the music box; her paw reaches down for the scruff of his neck; she is stern, glowing icon under her other arm",
  None, "the mother has yanked the cub up by the scruff; the music box lies dropped in the mud; the cub hangs his head",
  ["the mother grabs the cub by the scruff", "she yanks him up roughly", "the music box drops into the mud", "the cub hangs his head and is dragged back"], None),
 ("c27", 109.0, 115.0, ["sb15"], ["she", "moth"], False, ["family", "moth"], ("dolly_in", "slow push in"),
  "Night, rain, red glow on the horizon: the giant MOTHER BEAR holds up the glowing MOTH ICON; the moth inside the frame blazes with witchy green-white light",
  None, "the moth has peeled itself off the icon and hovers free in the air above it, wings spread, glowing; the icon's frame is empty",
  ["the icon blazes brighter", "the moth slowly peels itself off the painted icon surface, wings first", "it flutters up and hovers above the empty frame"], None),
 ("c28", 115.0, 123.0, ["sb15"], ["moth"], False, ["moth", "world"], ("zoom_out", "slow zoom out"),
  "The glowing MOTH, small, flutters up into a dark night sky above a burning landscape of flame-shaped trees and tiny houses",
  (0.5, "the moth is now enormous, its spread wings covering half the sky"),
  "the GIANT MOTH covers the entire sky from edge to edge, its patterned wings blotting out all the stars, its tiny dark eyes looking down; the burning land below glows red",
  ["the moth flutters upward", "it grows bigger and bigger with each wingbeat", "its wings spread across the whole sky", "the stars vanish behind its wings"], None),
 ("c29", 123.0, 128.5, ["sb15"], ["big", "she", "cub", "cat", "moth"], False, ["family", "moth"], ("locked", "static wide"),
  "Under a sky completely covered by the GIANT MOTH's wings, the three giant bears kneel in the mud with paws raised in worship, eyes glowing zombie-green; the cat sits BACKWARDS beside them, unimpressed",
  None, "the bears bow down low, foreheads to the ground, while the moth's wings slowly beat above",
  ["the moth's wings slowly beat", "the bears sway with raised paws", "they bow down to the ground"], None),
 ("c30", 128.5, 133.5, ["sb22"], ["jesus_plane", "moth"], False, ["world", "moth"], ("truck_left", "slow pan following the plane"),
  "The JESUS-AIRPLANE flies across the dark sky, its halo-glow flickering, beneath the edge of the GIANT MOTH's enormous wing; far below, tiny burning houses and onion churches",
  None, "the Jesus-airplane banks away and flies off into the distance, small",
  ["the Jesus-airplane flies left to right", "the moth's wing shifts above it", "the plane veers away and shrinks into the distance"], None),
 ("c31", 133.5, 138.8, ["sb13"], ["cub"], False, ["family", "trike", "world"], ("locked", "static wide"),
  "The giant CUB, eyes glowing zombie-green, spins a colossal red-yellow-green striped SPINNING TOP; it bores into the earth like a drilling machine, throwing up clods of soil and tiny crude houses; tiny people and little grey elephants flee",
  None, "a long ploughed trench of overturned earth runs across the land behind the top",
  ["the cub spins the top", "the top drills along the ground", "clods and tiny houses fly up", "people and elephants run"], None),
 ("c32", 138.8, 145.0, ["sb18"], ["big", "she", "cub"], False, ["family", "trike"], ("locked", "static wide"),
  "On a burning hill under a red-orange stormy sky the three giant bears dance a heavy clumsy dance: the CUB plays the balalaika, the FATHER sprays Khokhloma ornament fire from the samovar flamethrower into the sky, the MOTHER stomps; lightning",
  None, None, ["they stomp and turn in a circle", "the cub strums fast", "ornamental fire arcs into the sky", "lightning flashes"], "clips/v1/b27_h3.mp4"),
 ("c33", 145.0, 151.32, ["sb11"], ["big", "cub"], False, ["family", "trike", "world"], ("locked", "static wide"),
  "The giant FATHER BEAR throws round black cartoon bombs like snowballs over a tiny village of crude houses and onion churches; the bombs burst into big Khokhloma flower-shaped explosions; the cub cheers",
  None, "the sky over the village is full of red-and-gold Khokhloma flower bursts",
  ["the father winds up and throws", "the bombs arc through the air", "they bloom into ornamental fire-flowers", "the cub cheers"], "clips/v1/b28_h3.mp4"),
 ("c34", 151.32, 154.96, ["sb16"], [], False, ["world"], ("locked", "static wide"),
  "A burnt field in the rain among ruins of crude houses: in the foreground three naive painted widows in black headscarves: schematic, elongated, almost doll-like bodies flattened into black cloth, small simple faces with painted tears and hands over their mouths, painted as in a naive folk icon; one widow MONUMENTAL, taller than the ruined houses, the other two small; deadpan grief; Khokhloma fires smoulder in the ruins",
  None, None, ["rain falls", "the women's shoulders shake as they weep", "smoke drifts"], None),
 ("c35", 154.96, 158.58, ["sb11"], ["big", "she", "cub"], True, ["family", "trike"], ("truck_left", "slow side tracking"),
  "Wide: the giant silhouettes of the three bears and the war-trike march along the horizon under a sky covered by the moth's dark wings; the cub in the sidecar fires the brass TOP-MORTAR: striped spinning-top shells spiral up into the sky and burst into big flat Khokhloma fire-flowers over the tiny village; tiny people hide in cellars below",
  None, None, ["the giants march across the horizon", "the cub drops a spinning-top shell into the mortar and it spirals up out of the tube with a puff of smoke", "the shell bursts into a Khokhloma fire-flower", "tiny people duck into cellars"], None),
 ("c36", 158.58, 162.34, ["sb17"], [], False, ["world"], ("zoom_out", "slow zoom out"),
  "Seen from above: fires spreading across a black land in the curling scarlet and gold ornament of Khokhloma folk lacquer, flame-leaves and berries everywhere, tiny houses and onion churches inside the pattern",
  None, "the whole land is one ornament of Khokhloma fire",
  ["the ornament spreads and curls outward", "new flame-leaves unfurl"], None),
 ("c37", 162.34, 168.46, ["sb19"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("truck_left", "slow side tracking"),
  "The war-trike crawls slowly through deep mud and ash, wheels sinking; the bears sway drunkenly with heavy eyelids, the mother's icon empty; rain",
  None, "the trike has nearly stopped; the father's head droops",
  ["the trike crawls", "the bears sway", "the father's head droops forward"], None),
 ("c38", 168.46, 172.34, ["sb18", "sb19"], ["cub"], False, ["family"], ("locked", "static medium"),
  "The CUB alone, sitting AWAKE in the mud, eyes open and glowing green, strumming the balalaika, rain on the strings; the other bears are not in this frame",
  None, "the cub has stopped playing; his eyes are shut and his chin rests on the balalaika",
  ["he strums slower", "his eyes close", "his paw stops on the strings"], None),
 ("c39", 172.34, 176.81, ["sb19"], ["big", "she", "cub", "cat"], True, ["family", "trike"], ("locked", "static wide"),
  "The three giant bears, drunk, slump down asleep SITTING in the mud and ash with their backs against the big wheels of the parked war-trike, side by side: the father in the middle with the bottle in his lap, the mother on the left with the icon in her lap, the cub on the right hugging his balalaika, all heads dropped onto their chests; the cat curls up backwards on the trike seat; smoke rises from burnt tiny houses",
  None, "all of them asleep in a heap",
  ["the father slumps down against the wheel", "the mother sinks down beside him", "the cub slides down and hugs his balalaika", "their heads drop onto their chests", "the cat curls up"], None),
 ("c40", 176.81, 186.0, ["sb19"], ["big", "she", "cub", "cat", "moth"], True, ["family", "trike", "moth"], ("locked", "static wide"),
  "The three bears asleep sitting side by side against the wheels of the war-trike in brown autumn mud, heads dropped on their chests; the small MOTH, shrunk back to its normal size, flutters down from above",
  (0.5, "the first wet snowflakes are falling and a thin dusting of snow lies on the bears; the small moth is creeping between the father's and the mother's fur"),
  "filthy cold WINTER: snow covers the sleeping bears' fur and ushankas, frost on the trike, grey sooty ice on the puddles; the small shy moth peeks out from between the two big sleeping bears",
  ["the moth flutters down", "snow begins to fall", "the moth creeps between the sleeping bears to hide", "snow settles on everything", "the moth peeks out shyly"], None),
 ("c41", 186.0, 197.96, ["sb20"], ["winged"], False, ["world"], ("pedestal", "slow tilt up into the sky"),
  "A grey stormy winter sky full of falling snow where several FLYING MEN with wings of single white feathers drift slowly like white angels; below, a snowy land of crude houses and snow-capped onion churches with smoke rising",
  None, None, ["the flying men glide slowly across the sky", "their feather tufts flutter", "snow falls"], None),
]
BEATS = {
 "sb01": "Three bears in the den; the moth icon on the wall", "sb02": "The moth starts to glow; the bears wake like zombies", "sb03": "The mother bear takes the moth icon like a relic",
 "sb04": "Hats with stars on; they go out, burp, fart", "sb05": "The trike and the cat with the Maxim gun; everyone rides", "sb06": "Bagel bandoliers as ammunition",
 "sb07": "Forest road: they wreck everything; animals flee", "sb08": "Reveal: giants; crushing houses; crossing rivers", "sb09": "The cub and the broken ballerina music box; the mother yanks him back",
 "sb10": "They stop, look around, laugh, smoke, drink, hug", "sb11": "Fire, flamethrowers, bombs, guns", "sb12": "The cat sits and walks backwards", "sb13": "Soviet toys: the spinning top drills the earth",
 "sb14": "Animals come and are driven off", "sb15": "The moth leaves the icon, grows to cover the sky; the bears worship it", "sb16": "Tiny people flee; women weep",
 "sb17": "The rain feeds the fire", "sb18": "Dancing, balalaikas, flamethrowers", "sb19": "Drunk sleep; snow, frost; the moth hides between the bears", "sb20": "Grey sky with white angels",
 "sb21": "User reference character: Rozh in the rye field", "sb22": "User reference character: the Jesus-airplane", "sb23": "User reference world: onion churches and little elephants",
}
# location continuity: every shot in a location gets that location's approved anchor frame as Image 1
LOC = {"den_in": ["c02", "c03", "c04", "c05"], "den_out": ["c01", "c06", "c07", "c08", "c09"],
       "forest_road": ["c10", "c11", "c12", "c13", "c14", "c17"], "rye": ["c15", "c16"],
       "village": ["c18", "c19", "c21", "c23", "c24", "c25", "c26", "c31", "c33", "c34", "c35"],
       "burning_hills": ["c27", "c28", "c29", "c32"], "sleep": ["c39", "c37", "c38", "c40"]}
LOC_NOTE = {"den_in": "the den interior: dark plank walls, the black rug with symmetrical Khokhloma ornament hanging on the LEFT wall, the MOTH ICON hanging on the dark plank wall ABOVE THE BED between the rug and the shelf of seven white porcelain elephants, a window with rain on the right, an old radiator, an enamel mug on a stool",
            "den_out": "the outside of the den: a mossy den mound with the small grey stairwell door and one warm window, a muddy clearing, tall dark flame-shaped trees",
            "forest_road": "the dark muddy forest road between tall dark flame-shaped trees", "rye": "the edge of the dark forest above a wide golden rye field",
            "village": "the tiny village of distorted houses and onion churches at the giant bears' feet", "burning_hills": "the burning hills under a red stormy sky",
            "sleep": "the muddy ash field where the bears fall asleep around the war-trike"}
LOC_OF = {sid: loc for loc, ids in LOC.items() for sid in ids}
TRIKE_RULE = (" TRIKE RULE: the war-trike is ALWAYS exactly the vehicle on the war-trike model sheet: heavy olive-green riveted motorcycle with the sidecar on its RIGHT, rust patches, small spikes on the mudguards, huge knobbly tyres, the Khokhloma samovar as fuel tank, ONE round worried-eye headlamp, tall curved handlebars with a small striped top hanging, exactly THREE tall rusty organ-pipe exhausts behind the seat, a crate of bagels and two plain bottles on the sidecar rear, a plain torn red banner on a pole; the SIDECAR's outer side panel and the front mudguard are painted with a Khokhloma ornament panel (black lacquer, scarlet berries, curling gold leaves, thin gold edge), the rest plain olive steel; NO stars painted anywhere on the body; never another vehicle shape.")
SAMOVAR_RULE = (" SAMOVAR RULE: there is exactly ONE samovar design, exactly as on the samovar props sheet: round brass belly painted with Khokhloma red berries and golden leaves on black, brass crown chimney, curled brass handles, brass tap, four curled legs; on the war-trike it is the fuel tank between handlebars and seat; as a flamethrower it is carried by its handles with a long straight brass spout on its tap. TOP-MORTAR: a short fat brass mortar on a Khokhloma-painted wooden base firing striped red-gold-black spinning-top shells that burst into flat Khokhloma fire-flowers; a shell always leaves the muzzle STRAIGHT ALONG THE AXIS OF THE BARREL, continuing the barrel line exactly (pointed tip first), never at an angle to it, with smoke puffing along the same line.")
MOTH_RULE = (" MOTH RULE: the moth (and the moth in the icon) is always EXACTLY the moth from the moth model sheet: pale grey-brown triangular wings with the same dark zig-zag bands, furry pale thorax, long segmented abdomen, two long feathery antennae, two tiny dark eyes, no mouth; never a butterfly, never a bat; the icon frame is ornate gold, red and green enamel.")
HANDOFF = {
 "c04": "the bears have just woken in bed under the blanket",
 "c05": "the bears have already climbed out of bed and stand on the floor near the den door",
 "c06": "the mother carries the glowing icon at her chest; the father wears crossed bagel bandoliers; they now leave the den through its door",
 "c08": "they stand outside the den beside the parked war-trike; the mother holds the icon",
 "c09": "everyone sits on the war-trike: father driving, mother pillion holding the icon, cub in the sidecar, cat backwards on the sidecar nose behind the Maxim gun",
 "c10": "all four riding the war-trike in their seats", "c11": "all four riding the war-trike in their seats", "c12": "all four riding the war-trike in their seats",
 "c13": "the trike is parked by the road; the bears sit beside it", "c14": "the bears stand beside the parked trike", "c15": "all four riding the war-trike in their seats",
 "c17": "the bears stand beside the parked trike", "c18": "all four riding the war-trike in their seats", "c19": "all four riding the war-trike in their seats",
 "c20": "all four riding the war-trike in their seats", "c23": "all four riding the war-trike in their seats",
 "c24": "the trike has stopped; the cub sits in the sidecar", "c25": "the cub has climbed out of the sidecar and crouches over the music box",
 "c26": "the cub crouches over the music box; the mother walks over to him", "c28": "the moth has just left the icon; the mother now holds an empty frame",
 "c29": "the moth covers the sky; the mother holds the empty icon frame", "c37": "all four riding the war-trike, slowing in the mud",
 "c38": "the cub sits alone in the mud near the stopped trike", "c39": "the trike has stopped in the mud", "c40": "the bears sit slumped asleep against the trike wheels",
}
shots, rs = [], []
for (sid, t0, t1, sb, cast, trike, sheets, cam, start, mid, end, act, vref) in S:
    d = round(t1 - t0, 3); who = "; ".join(CAST[c] for c in cast) + ("; " + PROPS_DESC if trike else "")
    who = who.strip("; ") or "no main characters; only tiny minimal figures if any"
    R = rules(t0, sid, cast, trike)
    loc = LOC_OF.get(sid); anchor = LOC[loc][0] if loc else None
    mothy = "moth" in cast or "icon" in (start + " ".join(act) + str(end) + str(mid)).lower() or "moth" in (start + " ".join(act)).lower()
    if mothy and "moth" not in sheets: sheets = sheets + ["moth"]
    txt = (start + " ".join(act) + str(end) + str(mid)).lower()
    samo = trike or any(k in txt for k in ("samovar", "flamethrower", "mortar", "top-shell"))
    if samo and "samovar" not in sheets: sheets = sheets + ["samovar"]
    refs = [SHEET[s] for s in sheets] + STYLE_REFS
    if anchor and anchor != sid: refs = [f"keyframes/{anchor}_start.jpg"] + refs
    locnote = (f" LOCATION CONTINUITY: the first attached image is the approved frame of this same place ({LOC_NOTE[loc]}); keep the same place: its geography, set dressing, colours and the placement of fixed objects, BUT compose a NEW camera framing as described in SCENE (do not copy the anchor's composition or character poses)." if anchor and anchor != sid else (f" LOCATION: {LOC_NOTE[loc]}." if loc else ""))
    R = R + (f" CONTINUITY FROM THE PREVIOUS SHOT: {HANDOFF[sid]}." if sid in HANDOFF else "") + locnote + (MOTH_RULE if mothy else "") + (SAMOVAR_RULE if samo else "") + (TRIKE_RULE if trike else "")
    kf = f"{STYLE} SCENE: {start}. CAST (closed): {who}. {R}"
    edit = lambda change: (f"Edit the FIRST attached image, which is the start frame of this shot. Keep the exact same composition, camera framing, background, lighting, oil painting style, and the design, size and position of every character and object, "
                           f"EXCEPT for this change only: {change}. The other attached images are the character sheets; keep every character exactly on-model. {R}")
    off = 1 if (anchor and anchor != sid) else 0
    refnames = ("Image 1 is the approved frame of this location; " if off else "") + "; ".join(f"Image {i+1+off} is {SHEET_DESC[s]}" for i, s in enumerate(sheets))
    motion = (f"A living naive OIL PAINTING on canvas in gentle motion: smooth glazed brushwork and canvas weave stay visible the whole time; characters move naturally but simply, like a painting coming to life; background layers drift in gentle parallax; nothing morphs, faces and designs stay exactly as painted. "
              f"References: {refnames}; keep every character exactly on-model and in scale (father 1.0, mother 0.85, cub 0.5). "
              
              + f"SHOT: {start}. CAMERA: {cam[1]}. ONE CONTINUOUS MAIN ACTION, performed fully and visibly over the whole clip (real movement, not a dissolve): " + "; then ".join((act if len(act) <= 2 else [act[0], act[-1]])) + ". "
              + (f"END STATE: {end}. " if end else "")
              + ("FIRE: all fire stays flat Khokhloma ornament for the whole clip; it grows and curls like a painted ornament and never becomes realistic flames. " if any(k in (start + ' '.join(act) + (end or '')).lower() for k in ("fire", "flame", "burn", "blaze", "bomb", "rocket", "tracer")) else "")
              + "NEVER: text, letters, signs with writing, extra characters, bare-headed bears, realistic fire, photorealism, 3D render, cartoon outlines, cut-out paper look, morphing faces.")
    rs.append({"id": sid, "loc": loc, "anchor": anchor, "t0": t0, "t1": t1, "dur": d, "req_dur": max(3, min(15, int(-(-d // 1)))), "refs": refs, "sheets": sheets, "vref": vref,
               "kf_start": kf, "kf_mid": edit(mid[1]) if mid else None, "mid_frac": mid[0] if mid else None, "kf_end": edit(end) if end else None, "motion": motion, "cast": cast, "trike": trike})
    shots.append({"id": sid, "source_beat_ids": sb, "provenance_class": "explicit_text", "purpose": start[:140], "duration_seconds": d, "duration_source": "lyric_aligned",
        "state_in": {"scene": sid, "season": "winter" if sid == "c41" else "autumn"}, "state_out": {"scene": sid, "season": "winter" if sid in ("c40", "c41") else "autumn"},
        "prompt": {"closed_cast": cast, "prop_ids": ["war_trike"] if trike else [], "start": start, "camera": {"operation": cam[0], "instruction": cam[1]}, "action": act, "end": end or act[-1],
                   "invariants": ["naive oil painting on canvas look", "characters on-model per sheets", "no text anywhere"], "forbid": ["text", "realistic fire", "bare-headed bears", "snow before c40"],
                   "keyframes": {"start": kf, "mid": edit(mid[1]) if mid else None, "end": edit(end) if end else None}, "motion_prompt": motion, "references": refs, "motion_reference_video": vref},
        "qa": {"criteria": [{"id": f"{sid}-c1", "target": "start", "expected": start[:200], "severity": "major"},
                            {"id": f"{sid}-c2", "target": "action", "expected": act[-1], "severity": "critical"},
                            {"id": f"{sid}-c3", "target": "style", "expected": "naive oil painting look; characters on-model", "severity": "critical"},
                            {"id": f"{sid}-c4", "target": "notext", "expected": "no text, letters or numbers anywhere", "severity": "critical"}], "verdict": "pending", "evidence": []}})
CHARS = {"big": "father bear", "she": "mother bear", "cub": "cub", "cat": "cat", "moth": "moth", "rozh": "Rozh", "jesus_plane": "Jesus-airplane", "winged": "flying men"}
project = {"schema_version": "1.1", "project_id": "berloga2", "title": "BERLOGA 2 (Лей, ливень, лей)", "mode": "author", "validation_stage": "draft",
 "source": {"kind": "script", "path": "source/scenario_ru_v2.txt", "sha256": sha("source/scenario_ru_v2.txt"), "rights_context": "The user's own scenario, song and reference paintings.", "selected_pages": "all"},
 "output": {"width": 1920, "height": 1080, "fps": 24, "container": "mp4", "video_codec": "h264", "pixel_format": "yuv420p", "sample_aspect_ratio": "1:1", "audio_codec": "aac"},
 "bibles": {"style": {"id": "style-v2", "text": STYLE, "sha256": hashlib.sha256(STYLE.encode()).hexdigest()},
   "characters": {k: {"id": k, "description": CAST[k], "reference": SHEET["family" if k in ("big", "she", "cub", "cat") else "moth" if k == "moth" else "world"],
                      "reference_sha256": sha(SHEET["family" if k in ("big", "she", "cub", "cat") else "moth" if k == "moth" else "world"])} for k in CHARS},
   "locations": {"forest": {"id": "forest", "description": "dark forest of flame-shaped trees, stage-like muddy road, den mound"}, "village": {"id": "village", "description": "tiny distorted houses, onion churches, ant-sized people"}},
   "props": {"war_trike": {"id": "war_trike", "description": PROPS_DESC, "reference": SHEET["trike"], "reference_sha256": sha(SHEET["trike"])}},
   "sound": {"music": {"id": "music", "description": "The user's song, unaltered; no lip-sync"}}},
 "source_beats": [{"id": k, "source": {"page": 1, "panel": k, "token_raw": k, "file": "source/scenario_ru_v2.txt"}, "summary": v} for k, v in BEATS.items()],
 "shots": shots,
 "assembly": {"shot_order": [s["id"] for s in shots], "expected_duration_seconds": 197.96, "continuity_keys": ["season"], "transition_policy": "mixed",
              "transition_policy_rationale": "Hard cuts; scene detection undercounts look-alike painted shots, so cuts are verified by editorial timeline.",
              "scene_boundaries_before": [{"shot_id": S[i][0], "from_scene": S[i - 1][0], "to_scene": S[i][0], "rationale": "Music-video cut on a lyric line.", "approved_by": "claude (director, author mode)", "preserve_keys": ["season"], "reset_keys": {}} for i in range(1, len(S))]},
 "sound": {"classes": {"dialogue": {"disposition": "not_applicable", "rationale": "Music video."}, "vo": {"disposition": "not_applicable", "rationale": "No narration."},
   "foley": {"disposition": "intentionally_absent", "rationale": "The song stays unaltered."}, "sfx": {"disposition": "intentionally_absent", "rationale": "The song stays unaltered."},
   "ambience": {"disposition": "intentionally_absent", "rationale": "The song stays unaltered."}, "music": {"disposition": "present"}},
   "cues": [], "assets": [{"id": "song", "class": "music", "path": "source/SONG_CANONICAL.mp3", "sha256": sha("source/SONG_CANONICAL.mp3")}], "voice_segments": [],
   "delivery_profile": {"sample_rate": 48000, "channels": 2, "integrated_lufs": -16.9, "lufs_tolerance": 1.0, "true_peak_dbtp": -2.0, "rationale": "Measured from the user's master; unaltered."},
   "mix": {"recipe": "song passed through unaltered"}},
 "artifacts": {"still": None, "canary": None}, "approvals": [], "deviations": [], "jobs": [], "verification": {"status": "pending", "evidence": []}}
P = ROOT / "project.json"
if P.exists():
    old = json.loads(P.read_text())
    for k in ("validation_stage", "approvals", "jobs", "artifacts", "verification"): project[k] = old.get(k, project[k])
    if "final_audit" in old.get("sound", {}): project["sound"]["final_audit"] = old["sound"]["final_audit"]
    for s in project["shots"]:
        o = next((x for x in old["shots"] if x["id"] == s["id"]), None)
        if o: s["qa"] = o["qa"]
P.write_text(json.dumps(project, indent=1, ensure_ascii=False))
(ROOT / "docs/shots.json").write_text(json.dumps(rs, indent=1, ensure_ascii=False))
print(len(shots), "shots; mids", sum(1 for r in rs if r["kf_mid"]), "ends", sum(1 for r in rs if r["kf_end"]), "vrefs", sum(1 for r in rs if r["vref"]), "; requested seconds", sum(r["req_dur"] for r in rs))
