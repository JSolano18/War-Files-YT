import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCRIPT
BUILD = os.path.join(os.path.dirname(__file__), "..", "build")
LEAD = 0.35
def build_timeline():
    items = json.load(open(os.path.join(BUILD, "tts_items.json")))
    by = {}
    for it in items: by.setdefault(it["scene"], []).append(it)
    scenes = []; T = 0.0
    for si, (chap, kind, params, sents) in enumerate(SCRIPT):
        if kind == "chapter":
            d = params["dur"]; scenes.append(dict(i=si, chap=chap, kind=kind, p=params, start=T, dur=d, cues=[])); T += d; continue
        lead = 0.8 if si == 0 else LEAD
        cues = []; t = lead
        for it in by[si]:
            cues.append(dict(s=t, d=it["dur"], text=it["text"], file=it["file"], abs=T + t)); t += it["dur"] + it["pause"]
        d = max(t, params.get("dur_min", 0))
        scenes.append(dict(i=si, chap=chap, kind=kind, p=params, start=T, dur=d, cues=cues)); T += d
    return scenes, T
if __name__ == "__main__":
    sc, T = build_timeline()
    print("total %.1f s = %d:%05.2f" % (T, T // 60, T % 60), "scenes", len(sc))
    for s in sc: print(f'{s["i"]:2d} {s["kind"]:11s} {s["start"]:7.1f} {s["dur"]:5.1f}')
