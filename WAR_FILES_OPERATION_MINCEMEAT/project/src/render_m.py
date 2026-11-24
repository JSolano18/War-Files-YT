"""Parallel renderer with cross-dissolves. Writes build/chunks/kNN.mp4 and list.txt"""
import os, sys, json, time, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from multiprocessing import Pool
B = os.path.join(os.path.dirname(__file__), "..", "build"); CK = os.path.join(B, "chunks"); os.makedirs(CK, exist_ok=True)
FPS = 24; XF = 0.5; NW = int(os.environ.get("NW", "4"))
def load():
    tl = json.load(open(os.path.join(B, "timeline.json"))); tl["shots"].sort(key=lambda s: s["start"]); return tl
def work(args):
    ci, f0, f1 = args
    from scenes_m import REG
    from common import W, H
    tl = load(); shots = tl["shots"]; cache = {}
    out = os.path.join(CK, f"k{ci:02d}.mp4"); ok = out + ".ok"
    if os.path.exists(ok) and open(ok).read() == f"{f0}-{f1}": return ci, 0
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "13", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    def get(i):
        if i not in cache:
            s = shots[i]; cache[i] = REG[s["kind"]](s["end"] - s["start"], [], s["p"])
        return cache[i]
    j = 0; t0 = time.time()
    for f in range(f0, f1):
        t = f / FPS
        while j + 1 < len(shots) and shots[j + 1]["start"] <= t: j += 1
        s = shots[j]; fr = get(j).frame(t - s["start"]).convert("RGB"); a = np.asarray(fr)
        if j > 0 and t - s["start"] < XF and s["kind"] != "chapter" and shots[j - 1]["kind"] != "chapter":
            pv = shots[j - 1]; b = np.asarray(get(j - 1).frame(t - pv["start"]).convert("RGB"))
            k = (t - s["start"]) / XF; k = k * k * (3 - 2 * k)
            a = (a.astype(np.float32) * k + b.astype(np.float32) * (1 - k)).astype(np.uint8)
        for i in [i for i in cache if shots[i]["end"] < t - XF - 0.1]: del cache[i]
        p.stdin.write(a.tobytes())
    p.stdin.close(); p.wait(); open(ok, "w").write(f"{f0}-{f1}")
    return ci, time.time() - t0
if __name__ == "__main__":
    tl = load(); N = int(round(tl["total"] * FPS)); n_chunks = int(os.environ.get("NCH", "16"))
    bounds = [round(N * i / n_chunks) for i in range(n_chunks + 1)]
    jobs = [(i, bounds[i], bounds[i + 1]) for i in range(n_chunks)]
    t0 = time.time()
    with Pool(NW) as pool:
        for ci, dt in pool.imap_unordered(work, jobs): print(f"chunk {ci:02d} done {dt:.0f}s (elapsed {time.time() - t0:.0f}s)", flush=True)
    open(os.path.join(CK, "list.txt"), "w").write("".join(f"file 'k{i:02d}.mp4'\n" for i in range(n_chunks)))
    print("RENDER DONE", N, "frames", round(time.time() - t0), "s")
