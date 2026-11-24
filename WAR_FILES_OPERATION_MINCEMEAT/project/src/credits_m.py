import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
P = os.path.join(os.path.dirname(__file__), ".."); OUT = os.path.join(P, "..")
cr = json.load(open(os.path.join(P, "assets", "archival", "credits.json"))); tl = json.load(open(os.path.join(P, "build", "timeline.json")))
used = {}
for s in tl["shots"]:
    if s["kind"] == "photo": used.setdefault(s["p"]["key"], []).append(s["start"])
L = ["WAR FILES — THE DEAD MAN WHO FOOLED HITLER — IMAGE, AUDIO & ASSET CREDITS", "",
     "ARCHIVAL PHOTOGRAPHS USED IN THE FILM (each credited on screen, top-right)", ""]
for k in sorted(used, key=lambda k: used[k][0]):
    c = cr[k]; ts = ", ".join("%02d:%02d" % (t // 60, t % 60) for t in used[k])
    L += [f"- {c['title'][5:]}", f"    Author/holder: {c['artist'] or 'Unknown'}", f"    License: {c['license']}", f"    Source: {c['source']}", f"    Used at: {ts}", ""]
L += ["ARCHIVAL CREDIT LINES (paste into the YouTube description)"]
L += [f"  {cr[k]['credit']}" for k in sorted(used, key=lambda k: used[k][0])]
L += ["", "LICENSE NOTES",
 "- 'Public domain' items are UK Crown-copyright (expired) or National Archives images as tagged on Wikimedia Commons.",
 "- Ronnie Reed photo: CC BY-SA 3.0 (the Reed family collection) — attribution is shown on screen and must stay in the description.",
 "- No image of the deceased Glyndwr Michael is used, by design.", "",
 "IMAGES RESEARCHED BUT NOT YET DOWNLOADED (Wikimedia rate-limited this session; illustrated substitutes used instead)"]
W = json.load(open(os.path.join(P, "research", "wanted.json")))
for k, t in list(W["old"].items()) + list(W["new"].items()):
    if k not in used: L.append(f"  - {k}: {t[5:]}")
L += ["  These can be swapped in later: run src/slow_fetch.py, then rebuild the timeline and re-render.", "",
 "ORIGINAL VISUALS", "All maps, sea/submarine/coastline scenes, London, Welsh valley, office, document recreations, briefcase, canister,",
 "evidence objects and thumbnails were procedurally rendered for this production (Python/Pillow/NumPy).",
 "Map geography: Natural Earth (public domain) via the world-atlas package (ISC licence).",
 "Document recreations quote only documented wording (Trout memo item 28, Nye letter key passage, 'Mincemeat completed');",
 "other text on recreated documents is illegible placeholder or redacted — no wording was invented.", "",
 "NARRATION", "Synthetic voice: Kokoro-82M (open-source TTS, Apache-2.0), voice blend am_michael/am_onyx. Disclose as AI-generated voice if required.",
 "Pronunciation and intelligibility were checked by automatic transcription (Whisper small, MIT licence).", "",
 "MUSIC & SOUND DESIGN", "Original, procedurally composed and synthesized for this film (strings, low drones, pizzicato, timpani, piano,",
 "ocean, rain, wind, submarine engine, typewriter, paper, Morse, impacts). No samples or third-party recordings. Rights: WAR FILES.", "",
 "FONTS", "Bebas Neue, Oswald, Inter, EB Garamond — SIL Open Font License 1.1; Special Elite — Apache 2.0 (via @fontsource).", "",
 "CHANNEL LOGO", "WAR FILES logo (provided by the channel) — used only on the closing card; no permanent watermark, per brief."]
open(os.path.join(OUT, "IMAGE_AND_MUSIC_CREDITS.txt"), "w").write("\n".join(L) + "\n"); print("\n".join(L[:40]))
