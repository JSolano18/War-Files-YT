"""Original procedural score + sound design + voice assembly. No third-party audio."""
import os, sys, json, math
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.dirname(__file__))
from timeline import build_timeline, BUILD
SR = 48000
rng = np.random.default_rng(2003)
scenes, TOTAL = build_timeline()
N = int((TOTAL + 1.0) * SR)
def sec(x): return int(x * SR)
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, f1, f2, o=2): return signal.sosfilt(signal.butter(o, [f1, f2], "band", fs=SR, output="sos"), x)
def note(n): return 440.0 * 2 ** ((n - 69) / 12)   # midi

# ---------- mood per scene ----------
CH = {}  # chapter title -> mood
MOOD_OF_CHAP = {"The discovery": "open", "Antwerp: the diamond capital": "invest", "Leonardo Notarbartolo and the crew": "mystery",
                "The preparation and infiltration": "prep", "Inside the high-security vault": "vault", "The weekend of the robbery": "heist",
                "The discovery on Monday morning": "unsettle", "The evidence that exposed the thieves": "invest2",
                "Arrests, investigation, and competing accounts": "mystery", "The missing diamonds and final mystery": "reflect"}
# layer gains per mood: drone, pad, pulse, tick, ostinato, piano, shimmer
MOODS = {"open":    (1.0, 0.8, 0.0, 0.0, 0.0, 0.5, 0.3), "invest": (0.6, 0.7, 0.25, 0.0, 0.0, 0.35, 0.0),
         "mystery": (0.8, 0.7, 0.4, 0.0, 0.0, 0.3, 0.2), "prep":   (0.7, 0.5, 0.4, 0.55, 0.0, 0.0, 0.1),
         "vault":   (0.8, 0.5, 0.6, 0.5, 0.35, 0.0, 0.2), "heist":  (0.9, 0.5, 0.8, 0.3, 0.75, 0.0, 0.25),
         "unsettle":(1.0, 0.6, 0.0, 0.0, 0.0, 0.2, 0.6), "invest2":(0.7, 0.6, 0.45, 0.25, 0.2, 0.0, 0.2),
         "reflect": (0.8, 0.9, 0.0, 0.0, 0.0, 0.8, 0.3)}
NL = 7
gain = np.zeros((NL, int(TOTAL) + 3))
for s in scenes:
    g = MOODS[MOOD_OF_CHAP[s["chap"]]]
    if s["kind"] == "chapter": g = tuple(v * 0.35 for v in g)
    for k in range(int(s["start"]), int(s["start"] + s["dur"]) + 1):
        if k < gain.shape[1]: gain[:, k] = g
# end fade
endt = scenes[-1]["start"]
for k in range(int(endt), gain.shape[1]): gain[:, k] *= max(0, 1 - (k - endt) / 9.0)
gain = signal.filtfilt(np.ones(4) / 4, [1], gain, axis=1)  # ~smooth transitions
def genv(layer):
    x = np.arange(gain.shape[1]); return np.interp(np.arange(N) / SR, x, gain[layer]).astype(np.float32)

t = np.arange(N) / SR
music = np.zeros(N, np.float32)
# chords (D minor world): list of midi note sets, 8 s each
PROG = [[38, 50, 57, 62, 65], [34, 46, 53, 58, 62], [31, 43, 50, 55, 58], [33, 45, 52, 57, 61],
        [38, 50, 57, 60, 65], [36, 48, 55, 58, 63], [34, 46, 53, 57, 62], [33, 45, 52, 55, 61]]
CL = 8.0
# 1 drone
dr = (np.sin(2 * np.pi * note(26) * t) * 0.5 + np.sin(2 * np.pi * note(38) * t + 0.3) * 0.35 + np.sin(2 * np.pi * note(45) * t * 1.0005) * 0.18)
dr *= 0.7 + 0.3 * np.sin(2 * np.pi * t / 23.0)
air = lp(rng.standard_normal(N), 380, 2) * 0.6
music += (dr * 0.16 + air * 0.05).astype(np.float32) * genv(0)
# 2 pad: detuned saw stack per chord with slow attack
pad = np.zeros(N, np.float32)
seglen = sec(CL); env = np.ones(seglen + sec(3), np.float32)
a = sec(2.5); r = sec(3.0); env[:a] = np.linspace(0, 1, a) ** 2; env[-r:] = np.linspace(1, 0, r) ** 2
for ci, st in enumerate(range(0, N, seglen)):
    ch = PROG[ci % len(PROG)]; L = min(len(env), N - st); tt = np.arange(L) / SR
    seg = np.zeros(L)
    for n_ in ch[1:]:
        f = note(n_)
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12 / 4)
            for h in range(1, 7): seg += np.sin(2 * np.pi * ff * h * tt + h) / h * 0.08
    pad[st:st + L] += (seg * env[:L]).astype(np.float32)
pad = lp(pad, 1400, 2) * 0.55
music += pad.astype(np.float32) * genv(1)
# 3 heartbeat pulse (low kick ~ 62 bpm)
pulse = np.zeros(N, np.float32); kl = sec(0.5); kt = np.arange(kl) / SR
kick = np.sin(2 * np.pi * (45 + 40 * np.exp(-kt * 25)) * kt) * np.exp(-kt * 9)
for b in np.arange(0, TOTAL, 60 / 62):
    for off, amp in ((0, 1.0), (0.22, 0.6)):
        i = sec(b + off)
        if i + kl < N: pulse[i:i + kl] += kick * amp
music += pulse * 0.35 * genv(2)
# 4 tick (soft clock)
tick = np.zeros(N, np.float32); tl = sec(0.03)
click = hp(rng.standard_normal(tl), 3000) * np.exp(-np.arange(tl) / SR * 220)
for k, b in enumerate(np.arange(0, TOTAL, 0.5)):
    i = sec(b)
    if i + tl < N: tick[i:i + tl] += click * (1.0 if k % 2 == 0 else 0.6)
music += tick * 0.05 * genv(3)
# 5 ostinato: low staccato strings on chord root, eighths at 124 bpm
ost = np.zeros(N, np.float32); el = 60 / 124 / 2; nl = sec(el * 0.9); nt = np.arange(nl) / SR
for k, b in enumerate(np.arange(0, TOTAL, el)):
    ci = int(b // CL) % len(PROG); root = PROG[ci][0] + 12 + (7 if k % 8 == 6 else 0)
    f = note(root); wav = sum(np.sin(2 * np.pi * f * h * nt) / h for h in range(1, 6)) * np.exp(-nt * 9) * (1.0 if k % 2 == 0 else 0.7)
    i = sec(b)
    if i + nl < N: ost[i:i + nl] += wav
ost = lp(ost, 900, 2) * 0.10
music += ost.astype(np.float32) * genv(4)
# 6 piano motif (sparse, reverberant)
pia = np.zeros(N, np.float32); pl = sec(4.0); ptt = np.arange(pl) / SR
MOTIF = [74, 69, 72, 70, None, 69, 65, 67, None, None]
for k, b in enumerate(np.arange(1.0, TOTAL, 1.6)):
    n_ = MOTIF[k % len(MOTIF)]
    if n_ is None: continue
    ci = int(b // CL) % len(PROG)
    f = note(n_)
    wav = (np.sin(2 * np.pi * f * ptt) + 0.35 * np.sin(2 * np.pi * 2 * f * ptt) * np.exp(-ptt * 2) + 0.12 * np.sin(2 * np.pi * 3.01 * f * ptt) * np.exp(-ptt * 4)) * np.exp(-ptt * 1.3) * (1 - np.exp(-ptt * 300))
    i = sec(b)
    if i + pl < N: pia[i:i + pl] += wav * 0.09
music += pia * genv(5)
# 7 shimmer: high detuned sines, slow
sh = (np.sin(2 * np.pi * note(86) * t) + np.sin(2 * np.pi * note(86) * 1.004 * t) + 0.6 * np.sin(2 * np.pi * note(93) * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 11))
music += (sh * 0.012).astype(np.float32) * genv(6)
# reverb (synthetic IR)
irl = sec(3.2); ir = rng.standard_normal(irl) * np.exp(-np.arange(irl) / SR * 2.2); ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
wet = signal.oaconvolve(music, ir)[:N].astype(np.float32)
music = music * 0.75 + wet * 0.45
music = hp(music, 30).astype(np.float32)

# ---------- SFX ----------
sfx = np.zeros(N, np.float32)
def add(x, at, g=1.0):
    i = sec(at); L = min(len(x), N - i)
    if L > 0 and i >= 0: sfx[i:i + L] += (x[:L] * g).astype(np.float32)
def boom(d=3.0):
    tt = np.arange(sec(d)) / SR
    return np.sin(2 * np.pi * (32 + 60 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 1.6) + lp(rng.standard_normal(len(tt)), 300) * np.exp(-tt * 5) * 0.5
def whoosh(d=1.6):
    L = sec(d); tt = np.arange(L) / SR; n = rng.standard_normal(L)
    e = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
    return bp(n, 300, 3000) * e * 0.5
def metal(d=2.5):
    tt = np.arange(sec(d)) / SR
    return sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * dk) * a for f, dk, a in ((212, 2.0, 0.5), (563, 3.0, 0.35), (1141, 4.5, 0.25), (1873, 6, 0.15), (2911, 9, 0.1))) * (1 - np.exp(-tt * 400))
def thunk(d=1.5):
    tt = np.arange(sec(d)) / SR
    return np.sin(2 * np.pi * (60 + 30 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 5) + lp(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 18) * 0.6
def creak(d=3.0):
    L = sec(d); tt = np.arange(L) / SR
    f = 90 + 25 * np.sin(2 * np.pi * 0.7 * tt) + 10 * rng.standard_normal(L).cumsum() / SR
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = signal.sawtooth(ph) * (0.5 + 0.5 * np.sin(np.pi * tt / d))
    return bp(saw, 150, 1800) * 0.25
def footsteps(d=6.0, step=0.62):
    out = np.zeros(sec(d)); sl = sec(0.25); st = np.arange(sl) / SR
    s = lp(rng.standard_normal(sl), 700) * np.exp(-st * 30) + np.sin(2 * np.pi * 80 * st) * np.exp(-st * 40) * 0.6
    for k, b in enumerate(np.arange(0.2, d - 0.3, step)):
        i = sec(b); out[i:i + sl] += s * (0.8 + 0.2 * rng.random())
    return out
def hum(d):
    tt = np.arange(sec(d)) / SR
    e = np.minimum(1, np.minimum(tt / 1.5, (d - tt) / 1.5))
    return (np.sin(2 * np.pi * 50 * tt) + 0.5 * np.sin(2 * np.pi * 100 * tt) + 0.25 * np.sin(2 * np.pi * 150 * tt)) * e * 0.25
def wind(d):
    L = sec(d); tt = np.arange(L) / SR
    e = np.minimum(1, np.minimum(tt / 2, (d - tt) / 2)) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 5.3))
    return bp(rng.standard_normal(L), 150, 1200) * e * 0.5
def rumble(d):
    L = sec(d); tt = np.arange(L) / SR; e = np.minimum(1, np.minimum(tt / 2, (d - tt) / 2))
    return lp(rng.standard_normal(L), 180) * e * 0.7

for s in scenes:
    st, d, k, fx = s["start"], s["dur"], s["kind"], s["p"].get("sfx")
    if k == "chapter": add(whoosh(1.8), st - 0.6, 0.18); add(boom(2.5), st + 0.15, 0.10)
    if fx in ("drone_hit", "boom"): add(boom(4.0), st + 0.05, 0.30)
    if fx == "impact": add(boom(2.5), st + 0.1, 0.22); add(metal(1.5), st + 0.1, 0.03)
    if fx == "metal": add(metal(2.5), st + 0.2, 0.06)
    if fx == "door": add(creak(3.0), st + 0.1, 0.18); add(thunk(1.5), st + 2.9, 0.4)
    if fx == "footsteps": add(footsteps(min(d - 1, 9)), st + 0.3, 0.16)
    if fx == "hum": add(hum(d), st, 0.035)
    if fx == "wind" or k == "forest": add(wind(d), st, 0.07)
    if k == "city_night": add(rumble(d), st, 0.10)
    if k == "highway": add(rumble(d), st, 0.22)
    if k == "boxes_wall" and s["p"]["mode"] == "opening":
        for b in np.arange(0.5, d - 0.5, 0.45): add(metal(0.6), st + b + 0.1 * rng.random(), 0.02)
    if k == "dossier" or (k == "crew" and s["p"].get("verdict")):
        pass
    if k == "crew" and s["p"].get("verdict"):
        for c in s["cues"]: add(thunk(0.8), st + c["s"] + c["d"] * 0.75, 0.25)
    if k == "end": add(boom(5), st + 0.2, 0.2)
sfx = (sfx * 0.9 + signal.oaconvolve(sfx, ir)[:N].astype(np.float32) * 0.3)

# ---------- VOICE ----------
voice = np.zeros(N, np.float32)
for s in scenes:
    for c in s["cues"]:
        a, sr = sf.read(c["file"], dtype="float32")
        a = signal.resample_poly(a, SR, sr).astype(np.float32)
        i = sec(s["start"] + c["s"]); L = min(len(a), N - i); voice[i:i + L] += a[:L]
voice = hp(voice, 70).astype(np.float32)
# gentle presence boost
voice = voice + 0.25 * bp(voice, 2500, 5000).astype(np.float32)
voice /= np.percentile(np.abs(voice[np.abs(voice) > 1e-3]), 99.5) / 0.6

# ---------- MIX with ducking ----------
envv = signal.filtfilt(*signal.butter(2, 3, fs=SR), np.abs(voice))
act = np.clip(envv / 0.05, 0, 1)
duck = 1.0 - 0.55 * act
mus_bus = music * duck * 0.42 + sfx * (1.0 - 0.3 * act)
mix = voice + mus_bus
pk = np.abs(mix).max(); mix = mix / pk * 0.89
os.makedirs(os.path.join(BUILD, "audio"), exist_ok=True)
sf.write(os.path.join(BUILD, "audio", "mix_raw.wav"), np.stack([mix, mix], 1) * 1.0 + np.stack([mus_bus * 0.03, -mus_bus * 0.03], 1) / pk, SR, subtype="PCM_24")
sf.write(os.path.join(BUILD, "audio", "voice.wav"), voice / np.abs(voice).max() * 0.89, SR, subtype="PCM_24")
sf.write(os.path.join(BUILD, "audio", "music_sfx.wav"), mus_bus / np.abs(mus_bus).max() * 0.89, SR, subtype="PCM_24")
print("audio done", TOTAL)
