import os, sys, subprocess, time
sys.path.insert(0, os.path.dirname(__file__))
from multiprocessing import Pool
from timeline import build_timeline, BUILD
from common import W, H, FPS
CL = os.path.join(BUILD, "clips"); os.makedirs(CL, exist_ok=True)
def render(idx):
    from scenes import REG
    scenes, T = build_timeline(); s = scenes[idx]
    f0 = round(s["start"] * FPS); f1 = round((s["start"] + s["dur"]) * FPS); n = f1 - f0
    out = os.path.join(CL, f"c{idx:02d}.mp4")
    if os.path.exists(out) and os.path.exists(out + ".ok") and open(out + ".ok").read() == str(n): return idx, n, 0
    t0 = time.time()
    obj = REG[s["kind"]](s["dur"], s["cues"], s["p"])
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    prev_fade = s["kind"] != "chapter" and idx > 0 and scenes[idx - 1]["kind"] == "chapter"
    for k in range(n):
        fr = obj.frame(k / FPS)
        if prev_fade and k < 10: fr = (fr * ((k + 1) / 10)).astype("uint8")
        if idx == len(scenes) - 1 and k > n - 24: fr = (fr * max(0, (n - k) / 24)).astype("uint8")
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    open(out + ".ok", "w").write(str(n))
    return idx, n, time.time() - t0
if __name__ == "__main__":
    scenes, T = build_timeline()
    order = sorted(range(len(scenes)), key=lambda i: -scenes[i]["dur"])
    t0 = time.time()
    with Pool(4) as pool:
        for idx, n, dt in pool.imap_unordered(render, order):
            print(f"scene {idx:02d} {n} frames {dt:.0f}s  (elapsed {time.time()-t0:.0f}s)", flush=True)
    with open(os.path.join(CL, "list.txt"), "w") as f:
        for i in range(len(scenes)): f.write(f"file 'c{i:02d}.mp4'\n")
    print("ALL DONE", time.time() - t0)
