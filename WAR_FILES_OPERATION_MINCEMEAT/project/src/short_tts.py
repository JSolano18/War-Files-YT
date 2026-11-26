import os, sys, json, re, difflib
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SPEED", "0.98")
import tts
from short_script import LINES, SPOKEN
B = os.path.join(os.path.dirname(__file__), "..", "build", "short"); os.makedirs(B, exist_ok=True)
out = {}
for lid, text, *_ in LINES:
    sp = text
    for a, b in SPOKEN: sp = sp.replace(a, b)
    fn = os.path.join(B, lid + ".wav")
    if not os.path.exists(fn):
        a, sr = tts.synth(sp); sf.write(fn, a, sr)
    a, sr = sf.read(fn, dtype="float32")
    words = tts.transcribe(a, sr)
    heard = " ".join(w for w, _, _ in words)
    r = difflib.SequenceMatcher(None, [tts.norm(x) for x in sp.split()], [tts.norm(x) for x in heard.split()]).ratio()
    out[lid] = dict(file=fn, dur=len(a) / sr, words=words)
    print(f"{lid} {len(a)/sr:5.2f}s match={r:.2f} | {heard}", flush=True)
json.dump(out, open(os.path.join(B, "voice.json"), "w"), indent=1)
