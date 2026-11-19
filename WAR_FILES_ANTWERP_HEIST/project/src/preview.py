import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from timeline import build_timeline
from scenes import REG
from PIL import Image
sc, T = build_timeline()
SP = sys.argv[1]; which = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else range(len(sc))
fracs = [float(x) for x in (sys.argv[3].split(",") if len(sys.argv) > 3 else ["0.75"])]
for i in which:
    s = sc[i]; t0 = time.time(); obj = REG[s["kind"]](s["dur"], s["cues"], s["p"]); ts = time.time() - t0
    ims = []
    for f in fracs:
        t1 = time.time(); a = obj.frame(f * s["dur"]); tf = time.time() - t1
        ims.append(Image.fromarray(a).resize((960, 540)))
    sheet = Image.new("RGB", (960 * len(ims), 540))
    for k, im in enumerate(ims): sheet.paste(im, (960 * k, 0))
    sheet.save(os.path.join(SP, f"pv_{i:02d}.jpg"), quality=80)
    print(i, s["kind"], "setup %.2fs frame %.3fs" % (ts, tf), flush=True)
