"""Paragraph-level narration (Kokoro) + automatic Whisper review (pronunciation & word timestamps)."""
import json, os, sys, re, difflib, hashlib
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCRIPT, SPOKEN
B = os.path.join(os.path.dirname(__file__), "..", "build", "tts"); os.makedirs(B, exist_ok=True)
VOICE_MIX = (0.55, 0.45); SPEED = float(os.environ.get("SPEED", "0.9"))
def spoken(s):
    for a, b in SPOKEN: s = s.replace(a, b)
    return s.replace("—", ",")
def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower())
_k = _wm = None
def kok():
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro("/home/user/models/kokoro-v1.0.onnx", "/home/user/models/voices-v1.0.bin")
    return _k
def whisper():
    global _wm
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel("/home/user/models/whisper-small-ct2", device="cpu", compute_type="int8", cpu_threads=4)
    return _wm
def synth(text, seed_tag=""):
    k = kok(); v = VOICE_MIX[0] * k.get_voice_style("am_michael") + VOICE_MIX[1] * k.get_voice_style("am_onyx")
    a, sr = k.create(text, voice=v, speed=SPEED, lang="en-us")
    idx = np.where(np.abs(a) > 0.008)[0]; a = a[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.12 * sr)]
    return a, sr
def transcribe(a, sr):
    a16 = resample_poly(a, 16000, sr).astype(np.float32)
    segs, _ = whisper().transcribe(a16, language="en", word_timestamps=True, beam_size=5)
    return [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in s.words]
def run(only=None):
    report = []
    for i, p in enumerate(SCRIPT):
        if "text" not in p: continue
        if only is not None and i not in only: continue
        sp = spoken(p["text"]); h = hashlib.md5((sp + str(SPEED) + str(VOICE_MIX)).encode()).hexdigest()[:10]
        fn = os.path.join(B, f"p{i:03d}.wav"); meta = fn + ".json"
        if os.path.exists(meta) and json.load(open(meta)).get("hash") == h: 
            m = json.load(open(meta))
        else:
            a, sr = synth(sp); sf.write(fn, a, sr)
            words = transcribe(a, sr)
            m = dict(hash=h, text=p["text"], spoken=sp, sr=sr, dur=len(a) / sr, words=words)
            json.dump(m, open(meta, "w"), indent=0)
        hyp = [norm(w[0]) for w in m["words"]]; ref = [norm(w) for w in sp.split()]
        sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
        bad = [(" ".join(ref[i1:i2]), " ".join(hyp[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
        report.append(dict(i=i, dur=m["dur"], ratio=round(sm.ratio(), 3), diffs=bad))
        print(f"p{i:03d} {m['dur']:6.1f}s match={sm.ratio():.3f} {bad[:6]}", flush=True)
    json.dump(report, open(os.path.join(B, "..", "tts_report.json"), "w"), indent=1)
    tot = sum(r["dur"] for r in report); print("TOTAL speech %.1f s" % tot)
if __name__ == "__main__":
    run()
