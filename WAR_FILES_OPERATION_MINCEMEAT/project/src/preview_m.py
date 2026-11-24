import sys, os, json, time, traceback
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from scenes_m import REG
B = os.path.join(os.path.dirname(__file__), "..", "build"); tl = json.load(open(os.path.join(B, "timeline.json")))
out = sys.argv[1]; kinds = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None
frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.65
seen = set(); ims = []
for i, s in enumerate(tl["shots"]):
    key = (s["kind"], json.dumps({k: v for k, v in s["p"].items() if k in ("variant", "mode", "kind", "key", "sub", "focus", "style", "stage", "hl")}, sort_keys=True))
    if key in seen or (kinds and s["kind"] not in kinds): continue
    seen.add(key)
    try:
        t0 = time.time(); o = REG[s["kind"]](s["end"] - s["start"], [], s["p"]); f = o.frame((s["end"] - s["start"]) * frac); dt = time.time() - t0
        im = f.convert("RGB").resize((640, 360)); ImageDraw.Draw(im).text((6, 340), f"{i} {s['kind']} {key[1][:70]} {dt:.2f}s", fill=(255, 255, 0)); ims.append(im)
    except Exception as e:
        print("ERR", i, s["kind"], s["p"], repr(e)); traceback.print_exc(limit=3)
for k in range(0, len(ims), 9):
    sh = Image.new("RGB", (1920, 1080))
    for j, im in enumerate(ims[k:k + 9]): sh.paste(im, ((j % 3) * 640, (j // 3) * 360))
    sh.save(os.path.join(out, f"m_sheet_{k // 9:02d}.jpg"), quality=82)
print("sheets", (len(ims) + 8) // 9)
