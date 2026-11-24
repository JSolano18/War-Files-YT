"""Original score + sound design + voice, mixed with ducking and strategic silence. No third-party audio."""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
from scipy import signal
B = os.path.join(os.path.dirname(__file__), "..", "build"); OUT = os.path.join(os.path.dirname(__file__), "..", "..")
SR = 48000; rng = np.random.default_rng(1943)
tl = json.load(open(os.path.join(B, "timeline.json"))); TOT = tl["total"] + 0.5; N = int(TOT * SR)
def sec(x): return int(x * SR)
def sos(kind, f, o=2): return signal.butter(o, f, kind, fs=SR, output="sos")
def lp(x, f, o=2): return signal.sosfilt(sos("low", f, o), x)
def hp(x, f, o=2): return signal.sosfilt(sos("high", f, o), x)
def bp(x, a, b, o=2): return signal.sosfilt(sos("band", [a, b], o), x)
def note(n): return 440 * 2 ** ((n - 69) / 12)
t = np.arange(N) / SR

# ---------- mood timeline (per chapter) ----------
CHMOOD = {"Cold open": "tension", "The dead man": "mystery", "Hitler's Fortress Europe": "strategy", "An impossible plan": "intrigue",
          "The man who never was": "elegy", "Into enemy hands": "suspense", "The Germans take the bait": "suspense2",
          "The invasion of Sicily": "resolve", "The forgotten man": "elegy2"}
#            strings pad, low drone, pizz ostinato, timpani pulse, piano, high shimmer
MOOD = {"tension": (0.7, 1.0, 0.0, 0.25, 0.0, 0.5), "mystery": (0.8, 0.7, 0.35, 0.0, 0.3, 0.3), "strategy": (0.8, 0.6, 0.55, 0.35, 0.0, 0.1),
        "intrigue": (0.8, 0.6, 0.6, 0.1, 0.25, 0.2), "elegy": (1.0, 0.5, 0.0, 0.0, 0.9, 0.3), "suspense": (0.8, 0.8, 0.7, 0.5, 0.0, 0.3),
        "suspense2": (0.8, 0.9, 0.8, 0.6, 0.0, 0.4), "resolve": (1.0, 0.6, 0.5, 0.4, 0.2, 0.2), "elegy2": (1.0, 0.4, 0.0, 0.0, 1.0, 0.4)}
chap_bounds = tl["chapters"] + [(TOT, None)]
G = np.zeros((6, int(TOT) + 2))
for (c0, name), (c1, _) in zip(chap_bounds[:-1], chap_bounds[1:]):
    G[:, int(c0):int(c1) + 1] = np.array(MOOD[CHMOOD[name]])[:, None]
G = signal.filtfilt(np.ones(5) / 5, [1], G, axis=1)
# strategic silence: before/through the cold-open reveal, and short dips before key revelations
paras = tl["paras"]
def para_with(txt): return next(p for p in paras if txt in p["text"])
p1, p2 = para_with("There was just one problem"), para_with("He was already dead")
sil = [(p1["start"] - 0.5, p2["start"] + p2["dur"] + 0.6, 0.0)]
for key in ("The man in the mortuary had a name", "Someone had read them", "Glyndwr Michael served as Major William Martin"):
    p = para_with(key); sil.append((p["start"] - 1.2, p["start"] + 0.4, 0.15))
mgain = np.ones(N, np.float32)
for a, b, lvl in sil:
    i0, i1 = sec(max(0, a)), sec(min(TOT, b)); ramp_n = sec(0.8)
    mgain[i0:i1] = np.minimum(mgain[i0:i1], lvl)
    mgain[max(0, i0 - ramp_n):i0] = np.minimum(mgain[max(0, i0 - ramp_n):i0], np.linspace(1, lvl, i0 - max(0, i0 - ramp_n)))
    mgain[i1:i1 + ramp_n] = np.minimum(mgain[i1:i1 + ramp_n], np.linspace(lvl, 1, len(mgain[i1:i1 + ramp_n])))
def env(k): return np.interp(t, np.arange(G.shape[1]), G[k]).astype(np.float32)

# ---------- score ----------
PROG = [[50, 57, 62, 65, 69], [46, 53, 58, 62, 65], [43, 50, 55, 58, 62], [45, 52, 57, 61, 64],   # Dm  Bb  Gm  A
        [50, 57, 60, 65, 69], [41, 48, 53, 57, 60], [43, 50, 58, 62, 65], [45, 52, 57, 61, 64]]
CL = 9.0
mus = np.zeros(N, np.float32)
# 1 strings: detuned saw ensemble with slow vibrato, swelling
strings = np.zeros(N, np.float32); seg = sec(CL); E = np.ones(seg + sec(3), np.float32); a_ = sec(3); r_ = sec(3)
E[:a_] = np.linspace(0, 1, a_) ** 1.5; E[-r_:] = np.linspace(1, 0, r_) ** 1.5
for ci, st in enumerate(range(0, N, seg)):
    ch = PROG[ci % len(PROG)]; L = min(len(E), N - st); tt = np.arange(L) / SR; acc = np.zeros(L)
    for n_ in ch:
        for det in (-7, 0, 6):
            f = note(n_) * 2 ** (det / 1200); vib = 1 + 0.003 * np.sin(2 * np.pi * 5.2 * tt + det)
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            acc += signal.sawtooth(ph) * (0.05 if n_ > 55 else 0.07)
    strings[st:st + L] += (acc * E[:L]).astype(np.float32)
strings = lp(strings, 1800, 2) * 0.55
mus += strings * env(0)
# 2 low drone (cellos/basses on root)
dr = np.zeros(N, np.float32)
for ci, st in enumerate(range(0, N, seg)):
    L = min(len(E), N - st); tt = np.arange(L) / SR; f = note(PROG[ci % len(PROG)][0] - 12)
    dr[st:st + L] += ((np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(4 * np.pi * f * tt) + 0.25 * np.sin(6 * np.pi * f * tt)) * E[:L] * 0.16).astype(np.float32)
mus += lp(dr, 700) * env(1)
# 3 pizzicato ostinato (eighths at 104 bpm)
pz = np.zeros(N, np.float32); el = 60 / 104 / 2; nl = sec(0.35); nt = np.arange(nl) / SR
PAT = [0, 7, 12, 7, 3, 7, 12, 15]
for k, b in enumerate(np.arange(0, TOT, el)):
    ch = PROG[int(b // CL) % len(PROG)]; f = note(ch[0] + PAT[k % 8])
    w = (np.sin(2 * np.pi * f * nt) + 0.3 * np.sin(4 * np.pi * f * nt)) * np.exp(-nt * 22) * (1 - np.exp(-nt * 900))
    i = sec(b)
    if i + nl < N: pz[i:i + nl] += w * (0.09 if k % 2 == 0 else 0.06)
mus += pz * env(2)
# 4 timpani pulse (low hits on beats 1 & 3, 52 bpm)
tp = np.zeros(N, np.float32); kl = sec(1.2); kt = np.arange(kl) / SR
hit = (np.sin(2 * np.pi * (58 + 18 * np.exp(-kt * 14)) * kt) * np.exp(-kt * 3.5) + lp(rng.standard_normal(kl), 400) * np.exp(-kt * 20) * 0.4)
for b in np.arange(0.5, TOT, 60 / 52):
    i = sec(b)
    if i + kl < N: tp[i:i + kl] += hit * 0.22
mus += tp * env(3)
# 5 piano motif (sparse, D minor)
pn = np.zeros(N, np.float32); pl = sec(5.0); pt = np.arange(pl) / SR
MOT = [74, 72, 69, None, 70, 69, 65, None, 67, 65, 62, None, None]
for k, b in enumerate(np.arange(1.0, TOT, 1.5)):
    n_ = MOT[k % len(MOT)]
    if n_ is None: continue
    f = note(n_); w = (np.sin(2 * np.pi * f * pt) + 0.4 * np.sin(4 * np.pi * f * pt) * np.exp(-pt * 2) + 0.15 * np.sin(6.02 * np.pi * f * pt) * np.exp(-pt * 4)) * np.exp(-pt * 1.1) * (1 - np.exp(-pt * 400))
    i = sec(b)
    if i + pl < N: pn[i:i + pl] += w * 0.075
mus += pn * env(4)
# 6 shimmer (high harmonics)
sh = (np.sin(2 * np.pi * note(86) * t) + np.sin(2 * np.pi * note(86) * 1.003 * t) + 0.5 * np.sin(2 * np.pi * note(93) * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 13))
mus += (sh * 0.010).astype(np.float32) * env(5)
# reverb
irl = sec(3.5); ir = rng.standard_normal(irl) * np.exp(-np.arange(irl) / SR * 1.9); ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
mus = mus * 0.7 + signal.oaconvolve(mus, ir)[:N].astype(np.float32) * 0.5
mus = hp(mus, 35).astype(np.float32) * mgain
# end fade
end0 = tl["shots"][-1]["start"]; fade = np.clip(1 - (t - (TOT - 8)) / 7.5, 0, 1).astype(np.float32); mus *= fade

# ---------- sound design ----------
sfx = np.zeros(N, np.float32)
def add(x, at, g=1.0):
    i = sec(max(0, at)); L = min(len(x), N - i)
    if L > 0: sfx[i:i + L] += (x[:L] * g).astype(np.float32)
def edge(L, a=1.0, r=1.0):
    e = np.ones(L, np.float32); na, nr = min(L // 2, sec(a)), min(L // 2, sec(r)); e[:na] = np.linspace(0, 1, na); e[L - nr:] = np.linspace(1, 0, nr); return e
def waves(d, calm=1.0):
    L = sec(d); tt = np.arange(L) / SR; n = rng.standard_normal(L)
    swell = 0.45 + 0.55 * (0.5 + 0.5 * np.sin(2 * np.pi * tt / (7.5 / calm) + rng.uniform(0, 6))) ** 2
    return (lp(n, 900) * 0.5 + bp(n, 900, 4000) * 0.12) * swell * edge(L, 1.2, 1.2)
def rain(d):
    L = sec(d); n = rng.standard_normal(L); drops = (rng.random(L) > 0.9994) * rng.uniform(0.3, 1, L)
    return (bp(n, 1500, 8000) * 0.25 + lp(drops, 3000) * 2.0) * edge(L)
def wind(d):
    L = sec(d); tt = np.arange(L) / SR; return bp(rng.standard_normal(L), 200, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 6.1)) * 0.5 * edge(L)
def hum(d, f=48):
    L = sec(d); tt = np.arange(L) / SR; return (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(4 * np.pi * f * tt) + lp(rng.standard_normal(L), 200) * 0.6) * 0.25 * edge(L)
def whoosh(d=1.6):
    L = sec(d); tt = np.arange(L) / SR; return bp(rng.standard_normal(L), 300, 2500) * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2 * 0.5
def boom(d=3.0):
    tt = np.arange(sec(d)) / SR; return np.sin(2 * np.pi * (30 + 55 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 1.5) + lp(rng.standard_normal(len(tt)), 300) * np.exp(-tt * 5) * 0.5
def tick(d, rate=1.0):
    L = sec(d); out = np.zeros(L); cl = sec(0.02); c = hp(rng.standard_normal(cl), 2500) * np.exp(-np.arange(cl) / SR * 250)
    for b in np.arange(0.3, d - 0.1, rate): i = sec(b); out[i:i + cl] += c
    return out * 0.6
def typewriter(d, rate=7.0):
    L = sec(d); out = np.zeros(L); cl = sec(0.045); base = np.arange(cl) / SR
    for b in np.cumsum(rng.uniform(0.6, 1.6, int(d * rate)) / rate):
        if b >= d - 0.1: break
        c = (bp(rng.standard_normal(cl), 1200, 6000) * np.exp(-base * 110) + np.sin(2 * np.pi * 180 * base) * np.exp(-base * 90) * 0.4)
        i = sec(b); out[i:i + cl] += c * rng.uniform(0.6, 1.0)
    return out * 0.5
def paper(d=0.8):
    L = sec(d); tt = np.arange(L) / SR; return bp(rng.standard_normal(L), 800, 6000) * (np.sin(np.pi * tt / d) ** 3) * 0.35
def stamp_snd():
    tt = np.arange(sec(0.5)) / SR; return lp(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 30) + np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 25)
def engine(d):
    L = sec(d); tt = np.arange(L) / SR; f = 34 + 3 * np.sin(2 * np.pi * tt / 3)
    return (signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.3 + lp(rng.standard_normal(L), 300)) * 0.4 * edge(L)
def surface(d):
    L = sec(d); tt = np.arange(L) / SR; return (lp(rng.standard_normal(L), 1500) * np.exp(-tt * 0.7) * 0.8 + bp(rng.standard_normal(L), 200, 900) * 0.3) * edge(L, 0.2, 1.5)
def morse(d):
    L = sec(d); out = np.zeros(L); tt = np.arange(L) / SR; on = np.zeros(L)
    b = 0.3
    while b < d - 0.3:
        ln = rng.choice([0.07, 0.07, 0.2]); i0, i1 = sec(b), sec(b + ln); on[i0:i1] = 1; b += ln + rng.choice([0.07, 0.07, 0.22])
    return np.sin(2 * np.pi * 700 * tt) * lp(on, 60) * 0.25
for s in tl["shots"]:
    k, p, st, d = s["kind"], s["p"], s["start"], s["end"] - s["start"]
    if k == "ocean" or k == "fleet" or k == "end" or k == "title":
        v = p.get("variant", "predawn" if k == "title" else "dawn")
        add(waves(d + 0.6, 0.7 if v in ("night", "predawn") else 1.0), st - 0.3, 0.30 if k != "title" else 0.2)
        if p.get("sub") == "surface": add(surface(5), st + 0.2, 0.35)
        if p.get("sub") in ("wake", "close", "deck"): add(engine(d), st, 0.18)
        if p.get("sub") == "deck" or v == "overcast": add(wind(d), st, 0.18)
        if p.get("plane"): add(hum(d, 72) * 0.6, st, 0.12)
    elif k == "london": add(rain(d) if p.get("variant", "").startswith("night") else wind(d) * 0.4, st, 0.22)
    elif k in ("office", "archive"): add(tick(d), st, 0.10)
    elif k == "doc":
        add(paper(), st + 0.1, 0.35)
        if p.get("kind") in ("trout28", "nye", "ring", "bank", "signal", "decrypt"): add(typewriter(min(d - 0.5, 6)), st + 0.5, 0.20)
        if p.get("kind") in ("signal", "cable", "cable2", "decrypt"): add(morse(min(d, 5)), st + 0.3, 0.12)
    elif k in ("envelope", "litter", "calendar", "dossier", "books"): add(paper(), st + 0.15, 0.3)
    elif k == "stamp": add(stamp_snd(), st + 0.36, 0.5)
    elif k == "chapter": add(whoosh(1.8), st - 0.5, 0.16); add(boom(2.5), st + 0.2, 0.10)
    elif k == "map": add(whoosh(1.2), st - 0.2, 0.06)
    elif k == "road": add(engine(d), st, 0.25)
    elif k == "canister": add(bp(rng.standard_normal(sec(d)), 2000, 9000) * edge(sec(d)) * 0.2, st, 0.5)
    elif k == "huelva_day": add(wind(d) * 0.5, st, 0.15)
    if p.get("sfx") in ("impact", "boom"): add(boom(3.0), st + 0.05, 0.28)
sfx = sfx * 0.85 + signal.oaconvolve(sfx, ir)[:N].astype(np.float32) * 0.25

# ---------- voice ----------
voice = np.zeros(N, np.float32)
for p in paras:
    a, sr = sf.read(p["file"], dtype="float32"); a = signal.resample_poly(a, SR, sr).astype(np.float32)
    i = sec(p["start"]); L = min(len(a), N - i); voice[i:i + L] += a[:L]
voice = hp(voice, 70).astype(np.float32); voice = voice + 0.22 * bp(voice, 2500, 5500).astype(np.float32)
voice /= np.percentile(np.abs(voice[np.abs(voice) > 1e-3]), 99.5) / 0.6
# ---------- mix ----------
envv = signal.filtfilt(*signal.butter(2, 3, fs=SR), np.abs(voice)); act = np.clip(envv / 0.05, 0, 1)
bus = mus * 0.38 * (1 - 0.5 * act) + sfx * 0.9 * (1 - 0.35 * act)
mix = voice + bus; pk = np.abs(mix).max(); mix /= pk / 0.89
os.makedirs(os.path.join(B, "audio"), exist_ok=True)
width = signal.oaconvolve(bus, rng.standard_normal(sec(0.02)) * np.exp(-np.arange(sec(0.02)) / SR * 200) * 0.05)[:N] / pk
sf.write(os.path.join(B, "audio", "mix.wav"), np.stack([mix + width, mix - width], 1), SR, subtype="PCM_24")
sf.write(os.path.join(OUT, "NARRATION.wav"), (voice / np.abs(voice).max() * 0.89), SR, subtype="PCM_24")
sf.write(os.path.join(B, "audio", "music_sfx.wav"), bus / np.abs(bus).max() * 0.89, SR, subtype="PCM_24")
# balance report
w = SR // 2; on = []
for i in range(0, N - w, w):
    rv = np.sqrt((voice[i:i + w] ** 2).mean()); rb = np.sqrt((bus[i:i + w] ** 2).mean())
    if rv > 0.02: on.append((rv, rb))
on = np.array(on); print("voice/bus during speech: %.1f dB" % (20 * np.log10(on[:, 0].mean() / on[:, 1].mean())), " total %.1f s" % TOT)
