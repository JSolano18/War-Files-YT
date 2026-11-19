import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from timeline import build_timeline
from script_data import SCRIPT
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
scenes, T = build_timeline()
def mmss(x): return f"{int(x // 60):02d}:{int(x % 60):02d}"
# ---------- narration script ----------
L = ["WAR FILES — THE $100 MILLION ANTWERP DIAMOND HEIST (BELGIUM, 2003)", "FULL NARRATION SCRIPT (final, as recorded)", f"Runtime: {mmss(T)}  ·  Words: {sum(len(c['text'].split()) for s in scenes for c in s['cues'])}", "",
     "Conventions: [CHAPTER] = on-screen chapter card, no narration. Timecodes are the start of each line in FINAL_DOCUMENTARY.mp4.",
     "Lines attributed to Notarbartolo's account are claims he made to WIRED (2009) and are not confirmed by Belgian investigators.", ""]
for s in scenes:
    if s["kind"] == "chapter":
        L += ["", f"[{mmss(s['start'])}]  ══ CHAPTER {s['p']['num']} — {s['p']['title']} ══", ""]; continue
    L.append(f"   (visual: {s['kind']}{' — ' + s['p']['tag'] if s['p'].get('tag') else ''})")
    for c in s["cues"]: L.append(f"[{mmss(s['start'] + c['s'])}]  {c['text']}")
    L.append("")
L += ["", "PRONUNCIATION GUIDE (used for the synthetic voice)",
      "Notarbartolo — noh-tar-bar-TOH-loh   ·   D'Onorio — doh-NOR-ee-oh   ·   Finotto — fee-NOT-toh   ·   Tavano — tah-VAH-noh",
      "Pietro — PYEH-troh   ·   Hoveniersstraat — HOH-vuh-neers-straht   ·   Schupstraat — SKHUUP-straht   ·   Rijfstraat — RAYF-straht",
      "Scheldt — SKELT   ·   Vilvoorde — vil-VOR-duh   ·   mazal — MAH-zel"]
open(os.path.join(OUT, "FULL_NARRATION_SCRIPT.txt"), "w").write("\n".join(L) + "\n")
# ---------- chapters ----------
chaps = []; seen = set()
for s in scenes:
    if s["chap"] not in seen: seen.add(s["chap"]); chaps.append((s["start"], s["chap"]))
chaps[0] = (0.0, chaps[0][1])
open(os.path.join(os.path.dirname(__file__), "..", "build", "chapters.txt"), "w").write("\n".join(f"{mmss(t)} {c[0].upper() + c[1:]}" for t, c in chaps) + "\n")
# ---------- AI prompts / shot list ----------
STYLE = "Photorealistic cinematic documentary footage, early-2000s (2003) Belgium, dark sophisticated color grade (teal shadows, muted gold highlights), selective fine film grain, shallow depth of field, natural motion, no text, no logos, no recognizable real people."
P = {
 ("vault_door", "closed"): "A massive circular steel vault door, polished but worn, with a five-spoke handle wheel and a numbered combination dial, set into a concrete wall in an underground vault anteroom. Camera: very slow push-in (dolly) from medium-wide to close. Lighting: cold blue fluorescent spill from the right, a slow specular highlight sliding across the steel.",
 ("vault_door", "open"): "The same circular vault door swung fully open, revealing a narrow room lined floor-to-ceiling with steel safe-deposit boxes, several forced open. Warm red-amber light inside, cold blue light outside. Camera: slow dolly forward through the doorway. Faint dust in the air.",
 ("vault_door", "red"): "Close view of the closed circular vault door bathed in deep red side light, slowly pulling back to reveal the dark concrete room. Camera: slow dolly-out. Mood: unresolved, reflective.",
 ("boxes_wall", "aftermath"): "Interior of a bank-style safe-deposit vault after a burglary: walls of numbered steel boxes, many doors bent open and hanging, floor covered in scattered papers, torn envelopes and empty jewelry cases. A single flashlight beam sweeps across the wall. Camera: slow lateral tracking shot, slight perspective.",
 ("boxes_wall", "aftermath2"): "Morning discovery: investigators' flashlights moving over forced-open safe-deposit boxes; papers and envelopes on the floor. Figures only as out-of-focus silhouettes. Camera: handheld-steady slow pan.",
 ("boxes_wall", "opening"): "Dramatization: gloved hands in dark sleeves working on the lock of a steel safe-deposit box with a hand tool; the small door springs open. Cut-in to more boxes opening along a wall. Camera: tight close-ups, slow push. Low tungsten work light.",
 ("diamonds", "fall"): "Macro cinematography: brilliant-cut diamonds falling in slow motion through darkness, catching sharp white glints and faint spectral fire, against soft bokeh. Camera: locked-off macro, 120 fps slow motion.",
 ("diamonds", "velvet"): "Macro: loose brilliant-cut diamonds scattered on dark navy velvet, a slow light sweep makes facets sparkle. Camera: slow slider move across the stones, very shallow depth of field.",
 ("diamonds", "dark"): "Macro: a single large brilliant-cut diamond resting on dark fabric under a narrow beam of light, smaller stones out of focus around it; faint red ambient light. Camera: extremely slow push-in.",
 ("city_night", ""): "Aerial establishing shot of Antwerp, Belgium at night in winter, 2003: the Gothic spire of the Cathedral of Our Lady above dense stepped-gable rooftops, low fog drifting. Camera: slow aerial drift left to right.",
 ("city_night", "late"): "Antwerp at night, 2003, near the Central Station area: empty wet streets, closed shutters, a few lit windows, light fog. Camera: slow high-angle drift. No people.",
 ("corridor", ""): "POV walk down a narrow underground service corridor with concrete walls and flickering ceiling fluorescent panels, early-2000s building basement. Camera: slow steady forward dolly at walking pace.",
 ("corridor", "door"): "POV descending into a basement corridor that ends at a large round steel vault door; fluorescent lights; footsteps implied. Camera: forward dolly that slows and stops before the door.",
 ("highway", ""): "Night drive POV on a Belgian motorway in 2003: lane markings streaming past, sodium streetlights, red tail lights of a car far ahead, bare winter trees on the horizon. Camera: car-mounted, forward-facing, steady.",
 ("highway", "escape"): "Night drive POV on an unlit stretch of motorway between Antwerp and Brussels, February 2003; tail lights ahead; dark tree line. Camera: car-mounted, slightly faster.",
 ("forest", "plain"): "A small patch of bare winter woodland beside a motorway near Vilvoorde, Belgium, early grey morning, mist between the trunks, distant traffic. Camera: slow lateral tracking through trees.",
 ("forest", "trash"): "The same misty roadside woodland: black garbage bags and scattered torn envelopes and papers among dead leaves. Camera: slow push-in at ground level. Grey morning light.",
 ("forest", "night"): "Dramatization at night: car headlights sweeping through bare trees at the edge of a road; dark figures out of focus scattering rubbish bags. Faces never visible. Camera: slow pan following the light.",
 ("key", ""): "Macro of an old, long, heavy brass vault key (about a foot long) resting on a dark wooden surface; a slow streak of light runs along its shaft. Camera: slow rotating slider move.",
 ("sensors", ""): "Inside a dark vault antechamber: faint red infrared beam lines, a small ceiling light sensor and a door-mounted magnetic contact sensor, the round vault door in the background. Camera: slow push-in. Visual-effects beams subtle, not sci-fi.",
}
rows = []; prom = [f"AI VIDEO PROMPTS — WAR FILES: THE ANTWERP DIAMOND HEIST", "", "Global style suffix (append to every prompt):", STYLE, "",
                   "STATUS: These prompts were NOT rendered — no video-generation API was available in the production environment.",
                   "The current cut uses original procedural illustrations for these shots. Generated clips can be swapped in 1:1 using the timecodes below.",
                   "Label every generated clip on screen 'AI RECONSTRUCTION' or 'DRAMATIZATION'.", ""]
n = 0
for s in scenes:
    k = s["kind"]; v = s["p"].get("state") or s["p"].get("variant") or s["p"].get("mode") or ""
    if k == "vault_door" and s["p"].get("light") == "red": v = "red"
    if k == "corridor": v = "door" if s["p"].get("door") else ""
    if k == "city_night": v = s["p"].get("variant", "")
    key = (k, v) if (k, v) in P else ((k, "") if (k, "") in P else None)
    narr = " ".join(c["text"] for c in s["cues"])
    rows.append([s["i"], mmss(s["start"]), mmss(s["start"] + s["dur"]), f"{s['dur']:.1f}", s["chap"], k, v, s["p"].get("tag", ""), narr[:300], "AI prompt #" + str(n + 1) if key else "procedural graphic"])
    if key:
        n += 1
        prom += [f"#{n:02d}  [{mmss(s['start'])}–{mmss(s['start'] + s['dur'])}]  duration {s['dur']:.1f}s  ·  chapter: {s['chap']}  ·  label: {s['p'].get('tag', 'DRAMATIZATION')}",
                 "Narration over shot: " + narr, "PROMPT: " + P[key] + " Historical period: February 2003. Duration: " + f"{min(10, s['dur']):.0f}s per generation (generate {max(1, round(s['dur'] / 8))} variations with different angles to avoid repetition).", ""]
with open(os.path.join(OUT, "SHOT_LIST.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["scene", "start", "end", "duration_s", "chapter", "visual_type", "variant", "on_screen_label", "narration", "source"]); w.writerows(rows)
open(os.path.join(OUT, "AI_VIDEO_PROMPTS.txt"), "w").write("\n".join(prom) + "\n")
print(open(os.path.join(os.path.dirname(__file__), "..", "build", "chapters.txt")).read(), n, "prompts")
