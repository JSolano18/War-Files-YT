import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
from timeline import build_timeline, BUILD
from script_data import HIGHLIGHT
MAXL = 42
def chunks(text):
    """split sentence into subtitle events of <=2 lines x 42 chars"""
    words = text.split(); out = []; cur = []
    for w in words:
        trial = " ".join(cur + [w])
        if len(trial) > 2 * MAXL - 4 and cur:
            out.append(" ".join(cur)); cur = [w]
        else:
            cur.append(w)
            # prefer breaking after punctuation once reasonably long
            if len(trial) > 48 and re.search(r"[.,;:?!—]$", w): out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    # merge tiny tail
    if len(out) > 1 and len(out[-1]) < 14: tail = out.pop(); out[-1] += " " + tail
    return out
def two_lines(s):
    if len(s) <= MAXL: return [s]
    words = s.split(); best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) <= MAXL + 6 and len(b) <= MAXL + 6:
            sc = abs(len(a) - len(b))
            if best is None or sc < best[0]: best = (sc, a, b)
    return [best[1], best[2]] if best else [s]
def ts_srt(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"
def ts_ass(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f"{h}:{m:02d}:{s:05.2f}"
def weight(s): return len(re.sub(r"[^A-Za-z0-9$]", "", s)) + 6 * len(re.findall(r"[,;:—]", s)) + 1
events = []
scenes, T = build_timeline()
for sc in scenes:
    for c in sc["cues"]:
        st = sc["start"] + c["s"]; d = c["d"]
        parts = chunks(c["text"]); ws = [weight(p) for p in parts]; tot = sum(ws); acc = 0
        for p, w in zip(parts, ws):
            a = st + d * acc / tot; acc += w; b = st + d * acc / tot
            events.append([a, b, p])
# extend each event slightly (min 1.0 s, up to next start - 0.05)
for i, e in enumerate(events):
    nxt = events[i + 1][0] if i + 1 < len(events) else e[1] + 2
    e[1] = min(max(e[1] + 0.25, e[0] + 1.0), nxt - 0.04)
with open(os.path.join(BUILD, "subtitles.srt"), "w") as f:
    for i, (a, b, p) in enumerate(events, 1):
        f.write(f"{i}\n{ts_srt(a)} --> {ts_srt(b)}\n" + "\n".join(two_lines(p)) + "\n\n")
GOLD = "&H004CA5C9&"
def hl(line):
    for h in sorted(HIGHLIGHT, key=len, reverse=True):
        line = line.replace(h, "\x01" + h + "\x02")
    return line.replace("\x01", "{\\c" + GOLD + "}").replace("\x02", "{\\c&H00F0F2F4&}")
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Doc,Inter SemiBold,44,&H00F0F2F4,&H000000FF,&H00101010,&H90000000,0,0,0,0,100,100,0.4,0,1,2.2,1.4,2,200,200,62,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(os.path.join(BUILD, "subtitles.ass"), "w") as f:
    f.write(hdr)
    for a, b, p in events:
        txt = "\\N".join(hl(l) for l in two_lines(p))
        f.write(f"Dialogue: 0,{ts_ass(a)},{ts_ass(b)},Doc,,0,0,0,{{\\fad(120,120)}}{txt}\n")
print(len(events), "subtitle events")
