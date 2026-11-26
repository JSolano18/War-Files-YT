"""Original music + SFX for the Short, mixed with the narration."""
import os, sys, json
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.dirname(__file__))
from short_render import SEGS, TOT, B, V
SR = 48000; N = int(TOT * SR); rng = np.random.default_rng(11)
t = np.arange(N) / SR
def sos(k, f, o=2): return signal.butter(o, f, k, fs=SR, output="sos")
def lp(x, f): return signal.sosfilt(sos("low", f), x)
def hp(x, f): return signal.sosfilt(sos("high", f), x)
def add(buf, x, at, g=1.0):
    i = int(at * SR); x = x[: max(0, len(buf) - i)]; buf[i:i + len(x)] += g * x

voice = np.zeros(N, np.float32)
for s in SEGS:
    a, sr = sf.read(V[s["id"]]["file"], dtype="float32")
    a = signal.resample_poly(a, SR, sr).astype(np.float32); add(voice, a, s["t0"])

mus = np.zeros(N, np.float32)
# drone: A1 + E2 with slow swell, detuned
for f, g in ((55, 0.22), (82.4, 0.12), (110.3, 0.06), (54.7, 0.15)):
    mus += g * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.07 * t))
mus = lp(mus, 400) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 14) ** 2)
# dark string pad (saw-ish, low-passed) — minor chords, changes every 8 s
chords = [(57, 60, 64), (53, 57, 60), (55, 58, 62), (52, 56, 59)]
pad = np.zeros(N)
for k in range(int(TOT // 8) + 1):
    ch = chords[k % 4]; i0, i1 = int(k * 8 * SR), min(N, int((k + 1) * 8 * SR) + SR)
    tt = t[i0:i1] - k * 8; env = np.clip(tt / 1.5, 0, 1) * np.clip((9 - tt) / 1.5, 0, 1)
    for n in ch:
        f = 440 * 2 ** ((n - 12 - 69) / 12)
        for dt in (-0.15, 0.15): pad[i0:i1] += env * 0.05 * signal.sawtooth(2 * np.pi * f * (1 + dt / 100) * tt)
mus += lp(pad, 1400)
# heartbeat pulse, accelerating toward the reveal
L10 = next(s for s in SEGS if s["id"] == "L10")["t0"]
bt = 0.6; beats = []
while bt < TOT - 4:
    beats.append(bt); bpm = 66 + 40 * np.clip(bt / L10, 0, 1) if bt < L10 else 70; bt += 60 / bpm
kick = np.sin(2 * np.pi * (48 * np.exp(-np.arange(int(0.35 * SR)) / SR * 9) + 40) * np.arange(int(0.35 * SR)) / SR) * np.exp(-np.arange(int(0.35 * SR)) / SR * 11)
for b in beats:
    if abs(b - L10) < 1.2: continue
    add(mus, kick, b, 0.5); add(mus, kick, b + 0.22, 0.3)
# ticking clock (high clicks) in the middle act
click = hp(rng.normal(0, 1, int(0.012 * SR)), 3000) * np.exp(-np.arange(int(0.012 * SR)) / SR * 400)
for x in np.arange(9.6, L10 - 0.6, 0.5): add(mus, click, x, 0.12)
# riser before Sicily + silence gap + hit
rl = 2.2; rr = np.arange(int(rl * SR)) / SR
riser = hp(rng.normal(0, 1, len(rr)), 800) * (rr / rl) ** 2 * 0.25 + 0.12 * np.sin(2 * np.pi * (200 + 600 * (rr / rl) ** 2) * rr) * (rr / rl) ** 2
add(mus, riser.astype(np.float32), L10 - rl - 0.05)
i0, i1 = int((L10 - 0.6) * SR), int((L10 + 0.05) * SR); mus[i0:i1] *= np.linspace(1, 0.05, i1 - i0)
hitl = int(2.5 * SR); hr = np.arange(hitl) / SR
hit = (np.sin(2 * np.pi * 42 * hr) * 0.9 + lp(rng.normal(0, 1, hitl), 900) * 0.5) * np.exp(-hr * 2.2)
add(mus, hit.astype(np.float32), L10, 0.9)
# slams / stamps
boom = (np.sin(2 * np.pi * 60 * hr[: SR]) * np.exp(-hr[: SR] * 7) + hp(rng.normal(0, 1, SR), 2000) * np.exp(-hr[: SR] * 30) * 0.35)
whoosh = hp(lp(rng.normal(0, 1, int(0.5 * SR)), 3000), 300) * np.hanning(int(0.5 * SR)) * 0.25
for s in SEGS:
    if s["kind"] in ("photo", "letter", "word", "list", "end") and s["start"] > 0: add(mus, whoosh.astype(np.float32), s["start"] - 0.25)
    if s["kind"] == "photo": add(mus, boom.astype(np.float32), s["start"], 0.35)
    if s["args"].get("stamp"): add(mus, boom.astype(np.float32), s["start"] + (s["end"] - s["start"]) * 0.52, 0.7)
    if s["kind"] == "letter" and s["args"].get("part") == "top": add(mus, boom.astype(np.float32), s["start"] + (s["end"] - s["start"]) * 0.55, 0.6)
    if s["kind"] == "list":
        for w, a, b in V[s["id"]]["words"]:
            if w.lower().startswith(("fianc", "love", "theat")): add(mus, boom.astype(np.float32), s["t0"] + a + 0.35, 0.45)
# ducking
envv = np.abs(voice); envv = lp(envv, 6) * 4; duck = 1 - 0.55 * np.clip(envv / (envv.max() * 0.15 + 1e-9), 0, 1)
mus = mus / (np.abs(mus).max() + 1e-9) * 0.5 * duck
# fade in/out
mus *= np.clip(t / 0.4, 0, 1) * np.clip((TOT - t) / 1.2, 0, 1)
mix = voice * 1.0 + mus
st = np.stack([mix, mix], 1).astype(np.float32)
sf.write(os.path.join(B, "mix_raw.wav"), st, SR); print("audio ok", TOT)
