"""Vertical Short (1080x1920) cut from the documentary's narration and scene renders."""
import os, sys, json, subprocess, math, re
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
from scipy import signal
from PIL import Image, ImageDraw, ImageFilter
from timeline import build_timeline, BUILD
from common import font, text_img, paste, glow, radial, F_BEBAS, F_OSW, F_OSW_B, GOLD, WHITE, DIM, ROOT
SW, SH, FPS, SR = 1080, 1920, 24, 48000
SB = os.path.join(BUILD, "short"); os.makedirs(SB, exist_ok=True)
OUT = os.path.join(ROOT, "..", "SHORT")
TEMPO = 1.07
scenes, _ = build_timeline()
items = json.load(open(os.path.join(BUILD, "tts_items.json")))
# (sentence id or new-line text, source scene, offset-in-scene or None=use sentence's own, crop-x)
NEW = {"N1": "In 2003, thieves emptied one of the most secure vaults on Earth.",
       "N2": "Infrared heat sensors. Doppler radar. A seismic sensor. A magnetic field on the door.",
       "N3": "How did they do it, and where did the diamonds go? Watch the full documentary on WAR FILES. It's linked right below."}
PLAN = [("N1", 33, 0.5), (5, 2, None), (6, 1, 3.0), ("N2", 26, 1.0), (24, 20, 0.5), (26, 13, None), (29, 13, None),
        (61, 26, None), (62, 26, None), (75, 32, None), (76, 34, 0.0), (84, 37, None), (92, 43, None), (97, 46, 9.0),
        (98, 46, 9.0), (99, 13, 4.0), (105, 57, 0.0), (118, 55, None), ("N3", 33, 3.0)]
PAUSE = 0.22
# ---------- voice ----------
from kokoro_onnx import Kokoro
k = None
segs = []
for key, sc, off in PLAN:
    if isinstance(key, str):
        fn = os.path.join(SB, f"{key}.wav")
        if not os.path.exists(fn):
            k = k or Kokoro("/home/user/models/kokoro-v1.0.onnx", "/home/user/models/voices-v1.0.bin")
            v = 0.55 * k.get_voice_style("am_michael") + 0.45 * k.get_voice_style("am_onyx")
            sp = NEW[key].replace("WAR FILES", "War Files").replace("2003", "two thousand three")
            a, sr = k.create(sp, voice=v, speed=0.86, lang="en-us")
            idx = np.where(np.abs(a) > 0.008)[0]; a = a[max(0, idx[0] - 480): idx[-1] + 1440]; sf.write(fn, a, sr)
        text, src, own = NEW[key], fn, 0.0
    else:
        it = items[key]; text, src = it["text"], it["file"]
        sc_obj = scenes[it["scene"]]; c = sc_obj["cues"][it["idx"]]; own = c["s"]
    a, sr = sf.read(src, dtype="float32")
    a = signal.resample_poly(a, SR, sr).astype(np.float32)
    segs.append(dict(text=text, audio=a, scene=sc, off=own if off is None else off))
# tempo via ffmpeg atempo on the concatenated voice later: compute timeline in pre-tempo time, then scale
t = 0.35; voice = []
for s in segs:
    s["t0"] = t; s["d"] = len(s["audio"]) / SR; t += s["d"] + PAUSE
TOT_PRE = t + 3.2  # tail for end card
vo = np.zeros(int(TOT_PRE * SR), np.float32)
for s in segs:
    i = int(s["t0"] * SR); vo[i:i + len(s["audio"])] += s["audio"]
sf.write(os.path.join(SB, "voice_pre.wav"), vo, SR)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(SB, "voice_pre.wav"), "-af", f"atempo={TEMPO}", os.path.join(SB, "voice.wav")], check=True)
voice, _ = sf.read(os.path.join(SB, "voice.wav"), dtype="float32")
TOT = len(voice) / SR
for s in segs: s["t0"] /= TEMPO; s["d"] /= TEMPO
# ---------- video segments ----------
lst = []
for i, s in enumerate(segs):
    start = s["t0"] if i else 0.0
    end = segs[i + 1]["t0"] if i + 1 < len(segs) else TOT
    need = end - start + (1.0 if i + 1 == len(segs) else 0.0)
    sc = scenes[s["scene"]]; off = max(0.0, s["off"]); avail = sc["dur"] - off - 0.05
    stretch = need / avail if need > avail and avail > need * 0.4 else 1.0
    if stretch == 1.0: off = min(off, max(0.0, sc["dur"] - need - 0.05))
    fn = os.path.join(SB, f"v{i:02d}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{off:.3f}", "-t", f"{need / stretch:.3f}", "-i", os.path.join(BUILD, "clips", f"c{s['scene']:02d}.mp4"),
                    "-vf", f"setpts=PTS*{stretch:.4f},crop=608:1080:(iw-608)/2:0,scale=1080:1920:flags=lanczos,unsharp=5:5:0.5,fps=24,tpad=stop_mode=clone:stop_duration=2",
                    "-t", f"{need:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", fn], check=True)
    lst.append(f"file 'v{i:02d}.mp4'")
open(os.path.join(SB, "list.txt"), "w").write("\n".join(lst) + "\n")
# ---------- overlay (title band, logo, label) ----------
ov = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
for y in range(560):
    d.line([(0, y), (SW, y)], fill=(0, 0, 0, int(215 * (1 - y / 560) ** 1.4)))
for y in range(SH - 700, SH):
    d.line([(0, y), (SW, y)], fill=(0, 0, 0, int(170 * ((y - (SH - 700)) / 700) ** 1.6)))
logo = Image.open(os.path.join(ROOT, "assets", "war_files_logo_transparent.png")).convert("RGBA").resize((150, 150), Image.LANCZOS)
paste(ov, logo, SW / 2, 175, "cm", 0.92)
paste(ov, text_img("THE ANTWERP DIAMOND HEIST", font(F_BEBAS, 84), WHITE, tracking=6), SW / 2, 315, "cm")
paste(ov, text_img("BELGIUM · 2003", font(F_OSW, 30), GOLD, tracking=10), SW / 2, 385, "cm")
paste(ov, text_img("ILLUSTRATED RECONSTRUCTION", font(F_OSW, 22), (200, 198, 190), tracking=5), SW / 2, 432, "cm", 0.75)
ov.save(os.path.join(SB, "overlay.png"))
# ---------- end card (last ~3 s, drawn over video) ----------
ec = Image.new("RGBA", (SW, SH), (6, 6, 8, 235)); d = ImageDraw.Draw(ec)
g = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([140, 620, 940, 1420], fill=GOLD + (55,)); ec.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
paste(ec, text_img("FULL DOCUMENTARY", font(F_OSW_B, 48), GOLD, tracking=12), SW / 2, 760, "cm")
paste(ec, glow(text_img("$100,000,000", font(F_BEBAS, 190), GOLD, tracking=4), 22, 0.5), SW / 2, 900, "cm")
paste(ec, text_img("HOW DID THEY DO IT?", font(F_BEBAS, 104), WHITE, tracking=6), SW / 2, 1040, "cm")
paste(ec, text_img("WATCH NOW — LINK BELOW", font(F_OSW_B, 46), WHITE, tracking=8), SW / 2, 1180, "cm")
d.polygon([(SW / 2 - 34, 1250), (SW / 2 + 34, 1250), (SW / 2, 1300)], fill=GOLD + (255,))
ec.save(os.path.join(SB, "endcard.png"))
END0 = segs[-1]["t0"] + segs[-1]["d"] * 0.55
# ---------- captions (ASS, 2–3 word chunks) ----------
HL = {"$100,000,000", "HUNDRED", "MILLION", "DOLLARS", "DIAMONDS", "DIAMONDS?", "VAULT", "VAULTS", "NOTARBARTOLO.", "NOTARBARTOLO", "HAIRSPRAY", "SANDWICH.", "DNA.", "ARRESTED.", "NEVER", "RECOVERED.", "EXPLOSION.", "ALARM.", "WITNESSES.", "TAPE.", "WAR", "FILES.", "EVERYTHING.", "ROBBERY.", "TENANT", "GONE."}
def ts(x): return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
ev = []
for s in segs:
    words = s["text"].replace("—", "").split(); chunks = []; cur = []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) >= 13 or re.search(r"[.,?!:]$", w): chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    wts = [sum(len(w) for w in c) + 2 for c in chunks]; tot = sum(wts); acc = 0
    for c, wt in zip(chunks, wts):
        a = s["t0"] + s["d"] * acc / tot; acc += wt; b = s["t0"] + s["d"] * acc / tot
        txt = " ".join(("{\\c&H004CA5C9&}" + w.upper() + "{\\c&H00F4F4F4&}") if w.upper() in HL else w.upper() for w in c)
        if a < END0: ev.append((a, min(b, END0), txt))
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {SW}", f"PlayResY: {SH}", "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
       "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Bebas Neue,118,&H00F4F4F4,&H000000FF,&H00000000,&H96000000,0,0,0,0,100,100,3,0,1,6,3,5,120,170,0,1",
       "Style: Hook,Bebas Neue,190,&H004CA5C9,&H000000FF,&H00000000,&H96000000,0,0,0,0,100,100,4,0,1,7,4,5,60,60,0,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, b, txt in ev: ass.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos(525,1190)\\fad(60,0)}}{txt}")
hook_end = segs[2]["t0"]
ass.append(f"Dialogue: 0,{ts(0.05)},{ts(hook_end)},Hook,,0,0,0,,{{\\pos(540,700)\\fad(150,200)}}$100,000,000")
open(os.path.join(SB, "captions.ass"), "w").write("\n".join(ass) + "\n")
srt = []
for i, (a, b, txt) in enumerate(ev, 1):
    clean = re.sub(r"\{[^}]*\}", "", txt)
    srt += [str(i), f"{ts(a).replace('.', ',')}0 --> {ts(b).replace('.', ',')}0".replace(":0", ":0"), clean, ""]
# proper SRT timestamps
def tsr(x): return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}"
srt = []
for i, (a, b, txt) in enumerate(ev, 1): srt += [str(i), f"{tsr(a)} --> {tsr(b)}", re.sub(r"\{[^}]*\}", "", txt), ""]
os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, "SHORT_SUBTITLES.srt"), "w").write("\n".join(srt))
# ---------- music + sfx ----------
N = len(voice); tt = np.arange(N) / SR; rng = np.random.default_rng(7)
def note(n): return 440 * 2 ** ((n - 69) / 12)
def lp(x, f): return signal.sosfilt(signal.butter(2, f, "low", fs=SR, output="sos"), x)
build = np.clip(tt / (TOT * 0.8), 0, 1)
mus = (np.sin(2 * np.pi * note(26) * tt) * 0.5 + np.sin(2 * np.pi * note(38) * tt) * 0.3) * 0.16
mus += lp(rng.standard_normal(N), 380) * 0.04
PROG = [[50, 57, 62, 65], [46, 53, 58, 62], [43, 50, 55, 58], [45, 52, 57, 61]]
pad = np.zeros(N)
for ci, st in enumerate(range(0, N, SR * 6)):
    L = min(SR * 7, N - st); x = np.arange(L) / SR; env = np.minimum(1, np.minimum(x / 1.5, (7 - x) / 1.5)).clip(0)
    for n_ in PROG[ci % 4]:
        for h in range(1, 6): pad[st:st + L] += np.sin(2 * np.pi * note(n_) * h * x) / h * 0.05 * env
mus += lp(pad, 1300) * 0.5
kl = int(0.45 * SR); kt = np.arange(kl) / SR; kick = np.sin(2 * np.pi * (45 + 40 * np.exp(-kt * 25)) * kt) * np.exp(-kt * 9)
for b in np.arange(2.0, TOT - 3, 60 / 70):
    i = int(b * SR); g_ = 0.25 + 0.5 * build[i]
    for o, am in ((0, 1), (0.2, 0.55)):
        j = i + int(o * SR)
        if j + kl < N: mus[j:j + kl] += kick * am * g_ * 0.35
el = 60 / 128 / 2; nl = int(el * 0.9 * SR); nt = np.arange(nl) / SR
for kk, b in enumerate(np.arange(TOT * 0.35, TOT - 3, el)):
    i = int(b * SR); f = note(PROG[int(b // 6) % 4][0] - 12)
    w = sum(np.sin(2 * np.pi * f * h * nt) / h for h in range(1, 5)) * np.exp(-nt * 9) * (1 if kk % 2 == 0 else 0.7)
    if i + nl < N: mus[i:i + nl] += w * 0.05 * build[i]
def boom(dur=3.0):
    x = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * (32 + 60 * np.exp(-x * 6)) * x) * np.exp(-x * 1.6) + lp(rng.standard_normal(len(x)), 300) * np.exp(-x * 5) * 0.5
def add(x, at, g):
    i = int(at * SR); L = min(len(x), N - i)
    if L > 0: mus[i:i + L] += x[:L] * g
add(boom(4), 0.0, 0.35); add(boom(3), segs[16]["t0"] + segs[16]["d"] * 0.6, 0.28); add(boom(4), END0, 0.3)
mus[int(END0 * SR):] *= np.linspace(1, 0.4, N - int(END0 * SR))
irl = int(2.5 * SR); ir = rng.standard_normal(irl) * np.exp(-np.arange(irl) / SR * 2.4); ir /= np.sqrt((ir ** 2).sum())
mus = mus * 0.8 + signal.oaconvolve(mus, ir)[:N] * 0.35
env = signal.filtfilt(*signal.butter(2, 3, fs=SR), np.abs(voice)); act = np.clip(env / 0.05, 0, 1)
v = voice / np.percentile(np.abs(voice[np.abs(voice) > 1e-3]), 99.5) * 0.6
mix = v + mus / np.abs(mus).max() * 0.32 * (1 - 0.5 * act)
mix = mix / np.abs(mix).max() * 0.89
sf.write(os.path.join(SB, "mix.wav"), np.stack([mix, mix], 1), SR, subtype="PCM_24")
# ---------- final ----------
F = os.path.join(SB, "")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-stats", "-f", "concat", "-safe", "0", "-i", F + "list.txt",
    "-loop", "1", "-framerate", "24", "-i", F + "overlay.png", "-loop", "1", "-framerate", "24", "-i", F + "endcard.png", "-i", F + "mix.wav",
    "-filter_complex",
    f"[0:v]noise=alls=4:allf=t+u[b];[b][1:v]overlay=0:0:shortest=1[o];[2:v]format=rgba,fade=in:st={END0:.2f}:d=0.5:alpha=1[e];[o][e]overlay=0:0:shortest=1[o2];"
    f"[o2]ass={F}captions.ass:fontsdir={os.path.join(ROOT, 'fonts')}[v];[3:a]acompressor=threshold=-24dB:ratio=2.2:makeup=1.5,loudnorm=I=-14:TP=-1.5:LRA=9[a]",
    "-map", "[v]", "-map", "[a]", "-t", f"{TOT:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24",
    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", os.path.join(OUT, "SHORT_ANTWERP_HEIST.mp4")], check=True)
print("SHORT DONE", round(TOT, 2), "s")
