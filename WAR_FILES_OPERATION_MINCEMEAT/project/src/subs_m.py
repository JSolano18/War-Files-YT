import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
from script_data import HIGHLIGHT
B = os.path.join(os.path.dirname(__file__), "..", "build"); OUT = os.path.join(os.path.dirname(__file__), "..", "..")
tl = json.load(open(os.path.join(B, "timeline.json")))
MAXL = 42
def two(s):
    if len(s) <= MAXL: return [s]
    w = s.split(); best = None
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        sc = max(len(a), len(b)) + (0 if len(a) <= len(b) + 8 else 3)
        if best is None or sc < best[0]: best = (sc, a, b)
    return [best[1], best[2]]
def tsr(x): return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}"
def tsa(x): return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
srt = []; ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
       "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Doc,Inter SemiBold,42,&H00F2F2F2,&H000000FF,&H00141414,&H8C000000,0,0,0,0,100,100,0.3,0,1,2.0,1.2,2,220,220,58,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
GOLD = "{\\c&H004CA5C9&}"; WH = "{\\c&H00F2F2F2&}"
for i, (a, b, txt) in enumerate(tl["subs"], 1):
    lines = two(txt)
    srt += [str(i), f"{tsr(a)} --> {tsr(b)}", *lines, ""]
    hl = []
    for l in lines:
        for h in sorted(HIGHLIGHT, key=len, reverse=True):
            if h in l: l = l.replace(h, "\x01" + h + "\x02")
        hl.append(l.replace("\x01", GOLD).replace("\x02", WH))
    ass.append(f"Dialogue: 0,{tsa(a)},{tsa(b)},Doc,,0,0,0,,{{\\fad(100,80)}}" + "\\N".join(hl))
open(os.path.join(OUT, "SUBTITLES.srt"), "w").write("\n".join(srt)); open(os.path.join(B, "subtitles.ass"), "w").write("\n".join(ass) + "\n")
print(len(tl["subs"]), "subtitle events; longest line", max(len(l) for a, b, t in tl["subs"] for l in two(t)))
