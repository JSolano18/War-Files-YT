# Generate narration per sentence with Kokoro (local neural TTS), build timing map.
import json, os, sys, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCRIPT, SPOKEN, P
from kokoro_onnx import Kokoro
OUT = os.path.join(os.path.dirname(__file__), "..", "build", "tts"); os.makedirs(OUT, exist_ok=True)
k = Kokoro("/home/user/models/kokoro-v1.0.onnx", "/home/user/models/voices-v1.0.bin")
VOICE = 0.55 * k.get_voice_style("am_michael") + 0.45 * k.get_voice_style("am_onyx")
SPEED = 0.86
def spoken(s):
    for a, b in SPOKEN: s = s.replace(a, b)
    return s
def trim(a, sr, thr=0.008):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0: return a
    s = max(0, idx[0] - int(0.02 * sr)); e = min(len(a), idx[-1] + int(0.06 * sr))
    return a[s:e]
items = []
n = 0
for si, (chap, kind, params, sents) in enumerate(SCRIPT):
    for sj, s in enumerate(sents):
        text, pause = (s if isinstance(s, tuple) else (s, P))
        fn = os.path.join(OUT, f"s{si:02d}_{sj:02d}.wav")
        sp = spoken(text)
        cache = fn + ".txt"
        if not (os.path.exists(fn) and os.path.exists(cache) and open(cache).read() == sp):
            a, sr = k.create(sp, voice=VOICE, speed=SPEED, lang="en-us")
            a = trim(a, sr); sf.write(fn, a, sr); open(cache, "w").write(sp)
        info = sf.info(fn)
        items.append(dict(scene=si, idx=sj, text=text, spoken=sp, file=fn, dur=info.duration, pause=pause))
        n += 1
json.dump(items, open(os.path.join(OUT, "..", "tts_items.json"), "w"), indent=1)
tot = sum(i["dur"] + i["pause"] for i in items)
words = sum(len(i["text"].split()) for i in items)
print("sentences", n, "words", words, "speech+pauses %.1f s" % tot)
