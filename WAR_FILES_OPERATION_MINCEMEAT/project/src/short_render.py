"""WAR FILES — vertical Short renderer (1080x1920, 30 fps). Own visual language: evidence prints, stamps,
marker circles, kinetic type. Nothing reused from the long video's scenes."""
import os, sys, json, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
sys.path.insert(0, os.path.dirname(__file__))
from common import font, text_img, paste, glow, smooth, ease_out, clamp, ROOT, F_BEBAS, F_OSW, F_OSW_B, F_TYPE, F_INTER_M
from short_script import LINES

SW, SH, FPS = 1080, 1920, 30
B = os.path.join(ROOT, "build", "short"); A = os.path.join(ROOT, "assets", "short")
BRAND = os.path.join(ROOT, "..", "..", "WAR_FILES_PLAYBOOK", "brand", "LOGO_WAR_FILES_transparent_1000.png")
GOLD = (201, 165, 76); OFF = (242, 239, 232); RED = (232, 52, 42); BLACK = (10, 11, 14); STEEL = (118, 128, 138)
CRED = json.load(open(os.path.join(A, "credits.json")))
V = json.load(open(os.path.join(B, "voice.json")))
GAP = {"L10": 0.55, "L11": 0.45, "L13": 0.35}          # extra silence before these lines
HIGHLIGHT = {"panzer", "wrong", "grave", "never", "existed", "spain", "secret", "greece", "spies", "hitler's", "believed",
             "greece.", "sicily", "fiction", "real", "forgotten", "who", "linked"}

# ---------------- timeline ----------------
def timeline():
    t = 0.25; segs = []
    for lid, text, kind, args in LINES:
        t += GAP.get(lid, 0.0)
        d = V[lid]["dur"]; segs.append(dict(id=lid, text=text, kind=kind, args=args, t0=t, d=d))
        t += d + 0.16
    for i, s in enumerate(segs):
        s["start"] = 0.0 if i == 0 else s["t0"] - 0.08
        s["end"] = segs[i + 1]["t0"] - 0.08 if i + 1 < len(segs) else t + 2.6
    return segs, segs[-1]["end"]

SEGS, TOT = timeline()

def words():
    out = []
    for s in SEGS:
        for w, a, b in V[s["id"]]["words"]: out.append((w, s["t0"] + a, s["t0"] + b))
    return out
WORDS = words()

# ---------------- assets ----------------
_cache = {}
def photo(key, bw=False):
    k = (key, bw)
    if k not in _cache:
        im = Image.open(os.path.join(A, CRED[key]["file"])).convert("RGB")
        if bw: im = ImageOps.grayscale(im).convert("RGB")
        im = ImageOps.autocontrast(im, cutoff=0.5)
        _cache[k] = im
    return _cache[k]

def cover(im, w, h, z=1.0, c=(0.5, 0.5)):
    s = max(w / im.width, h / im.height) * z
    cw, ch = w / s, h / s
    x0 = clamp(c[0] * im.width - cw / 2, 0, im.width - cw); y0 = clamp(c[1] * im.height - ch / 2, 0, im.height - ch)
    return im.resize((w, h), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

def bg_blur(key, bw):
    k = ("blur", key, bw)
    if k not in _cache:
        b = cover(photo(key, bw), SW // 4, SH // 4).filter(ImageFilter.GaussianBlur(10)).resize((SW, SH), Image.BICUBIC)
        arr = np.asarray(b).astype(np.float32) * 0.32
        _cache[k] = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    return _cache[k]

def base_bg():
    if "bg" not in _cache:
        rng = np.random.default_rng(3)
        n = rng.normal(0, 1, (SH // 8, SW // 8)).astype(np.float32)
        n = np.asarray(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((SW, SH), Image.BICUBIC)).astype(np.float32) - 128
        yy, xx = np.mgrid[0:SH, 0:SW]; r = np.sqrt(((xx - SW / 2) / SW) ** 2 + ((yy - SH * 0.42) / SH) ** 2)
        g = (1 - np.clip(r * 1.6, 0, 1)) * 26 + 10 + n * 0.25
        arr = np.stack([g, g * 1.02, g * 1.08], -1)
        _cache["bg"] = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    return _cache["bg"]

def grain_frames():
    rng = np.random.default_rng(7)
    return [rng.normal(0, 7, (SH // 2, SW // 2)).astype(np.float32) for _ in range(12)]
GRAIN = grain_frames()

def vig():
    if "vig" not in _cache:
        yy, xx = np.mgrid[0:SH, 0:SW]; r = np.sqrt(((xx - SW / 2) / (SW * 0.75)) ** 2 + ((yy - SH / 2) / (SH * 0.7)) ** 2)
        _cache["vig"] = (1 - 0.55 * np.clip(r - 0.35, 0, 1) ** 1.3)[..., None].astype(np.float32)
    return _cache["vig"]

# ---------------- drawing helpers ----------------
def rotated(im, deg):
    return im.rotate(deg, resample=Image.BICUBIC, expand=True)

def print_card(img, w, h, credit=None):
    """photo print with off-white border and drop shadow"""
    bd = 16; card = Image.new("RGBA", (w + 2 * bd, h + 2 * bd + (34 if credit else 0)), OFF + (255,))
    card.paste(img, (bd, bd))
    if credit:
        f = font(F_INTER_M, 19); t = text_img(credit[:95], f, fill=(70, 70, 70))
        paste(card, t, bd, h + bd + 7)
    return card

def shadowed(card, r=18, op=0.75):
    pad = 40; sh = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    a = Image.new("L", card.size, int(255 * op)); sh.paste((0, 0, 0, 255), (pad, pad + 10), a)
    sh = sh.filter(ImageFilter.GaussianBlur(r)); sh.alpha_composite(card, (pad, pad)); return sh

def stamp(text, size=130, color=RED, rot=-12, seed=1):
    f = font(F_BEBAS, size); t = text_img(text, f, fill=color, tracking=6)
    w, h = t.width + 60, t.height + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w - 5, h - 5), 14, outline=color + (255,), width=9)
    paste(im, t, w / 2, h / 2 + 4, "cm")
    rng = np.random.default_rng(seed); a = np.asarray(im.getchannel("A")).astype(np.float32)
    holes = (np.asarray(Image.fromarray((rng.random((h // 3, w // 3)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0)
    a *= np.clip((holes - 0.18) * 3, 0, 1) * 0.9
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return rotated(im, rot)

def marker_circle(frame, cx, cy, rx, ry, p, width=10):
    if p <= 0: return
    layer = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    n = int(90 * p) + 2; pts = []
    for i in range(n):
        a = -math.pi / 2 + 2.15 * math.pi * i / 89
        wob = 1 + 0.04 * math.sin(a * 3 + 1)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    d.line(pts, fill=RED + (235,), width=width, joint="curve")
    frame.alpha_composite(layer)

def header(frame, t):
    f = font(F_OSW_B, 30); tx = text_img("WAR FILES  ·  CASE FILE 1943", f, fill=GOLD, tracking=5)
    paste(frame, tx, 70, 215, opacity=0.9)
    ImageDraw.Draw(frame).line((70, 262, 70 + tx.width, 262), fill=GOLD + (200,), width=3)

def label(frame, text):
    f = font(F_OSW_B, 24); t = text_img(text, f, fill=OFF, tracking=4)
    box = Image.new("RGBA", (t.width + 26, t.height + 8), (0, 0, 0, 170)); paste(box, t, 13, 2)
    paste(frame, box, SW - 70, 215, "rt")

def date_card(frame, text, p):
    if p <= 0: return
    f = font(F_TYPE, 64); n = int(len(text) * clamp(p * 1.4)); t = text_img(text[:n], f, fill=OFF)
    box = Image.new("RGBA", (int(font(F_TYPE, 64).getlength(text)) + 60, 100), (12, 12, 14, 215))
    ImageDraw.Draw(box).rectangle((0, 0, 9, 100), fill=RED + (255,)); paste(box, t, 34, 50, "lm")
    paste(frame, box, 70, 330)

# ---------------- scene kinds ----------------
PRINT_W, PRINT_H, PRINT_Y = 940, 880, 330

def scene_photo(frame, s, lt, ld):
    a = s["args"]; key = a["img"]; bw = a.get("bw", False)
    frame.alpha_composite(bg_blur(key, bw))
    p = lt / max(ld, 0.01); z = a.get("z0", 1.0) + (a.get("z1", 1.1) - a.get("z0", 1.0)) * smooth(p)
    c0 = a.get("c0", (0.5, 0.5)); c1 = a.get("c1", c0); c = (c0[0] + (c1[0] - c0[0]) * smooth(p), c0[1] + (c1[1] - c0[1]) * smooth(p))
    img = cover(photo(key, bw), PRINT_W, PRINT_H, z, c)
    card = shadowed(print_card(img, PRINT_W, PRINT_H, CRED[key]["credit"]))
    slam = 1 - ease_out(lt / 0.28); sc = 1 + 0.16 * slam
    rot = (-1.6 if hash(s["id"]) % 2 else 1.4) * (1 + 0.6 * slam)
    card = rotated(card, rot)
    if sc != 1: card = card.resize((int(card.width * sc), int(card.height * sc)), Image.BILINEAR)
    paste(frame, card, SW / 2, PRINT_Y + PRINT_H / 2 + 20, "cm")
    if a.get("place"):
        f = font(F_OSW_B, 30); tx = text_img(a["place"], f, fill=OFF, tracking=4)
        bx = Image.new("RGBA", (tx.width + 30, tx.height + 12), (0, 0, 0, 190)); paste(bx, tx, 15, 4)
        paste(frame, bx, SW / 2 - PRINT_W / 2 + 10, PRINT_Y + PRINT_H - 30, "lb", opacity=clamp((lt - 0.4) / 0.4))
    if a.get("date"): date_card(frame, a["date"], (lt - 0.2) / 1.2)
    if a.get("circle"):
        rx, ry = a["circle"]; marker_circle(frame, SW / 2, PRINT_Y + PRINT_H / 2 + 20, rx, ry, clamp((lt - a.get("circle_t", 0.9)) / 0.7))
    if a.get("stamp"):
        st0 = ld * 0.52; q = (lt - st0) / 0.18
        if q > 0:
            stp = stamp(a["stamp"], 150, seed=len(a["stamp"]))
            k = 1 + 1.2 * (1 - ease_out(q))
            stp = stp.resize((int(stp.width * k), int(stp.height * k)), Image.BILINEAR)
            paste(frame, stp, SW / 2, PRINT_Y + PRINT_H * 0.78, "cm", opacity=clamp(q * 1.5))
            if q < 1.4: shake(frame, q)
    return lt < 0.07  # flash on slam

def shake(frame, q):
    pass  # handled via global offset (see render_frame)

def scene_secret(frame, s, lt, ld):
    frame.alpha_composite(base_bg())
    w, h = 760, 900; paper = Image.new("RGBA", (w, h), (226, 218, 198, 255)); d = ImageDraw.Draw(paper)
    rng = random.Random(5)
    f = font(F_TYPE, 38); paste(paper, text_img("MOST SECRET  ·  PERSONAL", f, fill=(40, 36, 30)), 60, 70)
    d.line((60, 130, w - 60, 130), fill=(60, 55, 48), width=3)
    lines = 11; shown = lt / max(ld * 0.75, 0.01) * lines
    for i in range(lines):
        y = 175 + i * 62; ww = rng.randint(380, w - 120)
        if i < shown:
            d.rectangle((60, y, 60 + ww * clamp(shown - i), y + 30), fill=(18, 18, 20))
    card = rotated(shadowed(paper), 2.0 * (1 - ease_out(lt / 0.4)) - 1.0)
    paste(frame, card, SW / 2, 790, "cm")
    if lt > ld * 0.45:
        q = (lt - ld * 0.45) / 0.18; stp = stamp("TOP SECRET", 140, seed=3, rot=-9)
        k = 1 + 1.0 * (1 - ease_out(q)); stp = stp.resize((int(stp.width * k), int(stp.height * k)), Image.BILINEAR)
        paste(frame, stp, SW / 2, 740, "cm", opacity=clamp(q * 1.5))
    return lt < 0.05

def big_word(text, size, color=OFF):
    return text_img(text, font(F_BEBAS, size), fill=color, tracking=8)

def scene_word(frame, s, lt, ld):
    a = s["args"]; frame.alpha_composite(base_bg())
    f2 = font(F_OSW_B, 40); sub = text_img(a["sub"], f2, fill=GOLD, tracking=8)
    paste(frame, sub, SW / 2, 610, "cm", opacity=clamp(lt / 0.4))
    ImageDraw.Draw(frame).line((SW / 2 - sub.width / 2, 650, SW / 2 + sub.width / 2, 650), fill=GOLD + (220,), width=3)
    word = a["word"]; n = len(word)
    for i, ch in enumerate(word):
        q = (lt - 0.08 * i) / 0.22
        if q <= 0: continue
        ci = big_word(ch, 300)
        x = SW / 2 - 300 * 0.42 * n / 2 + i * 300 * 0.42 + 300 * 0.21
        paste(frame, ci, x, 820 + 60 * (1 - ease_out(q)), "cm", opacity=clamp(q))
    if a.get("arrows"):
        d = ImageDraw.Draw(frame)
        for j in range(6):
            q = clamp((lt - 0.15 * j) / 0.9)
            if q <= 0: continue
            sx = 90 + j * 180; sy = 1180; ex = SW / 2 + (sx - SW / 2) * 0.25; ey = 960
            px, py = sx + (ex - sx) * ease_out(q), sy + (ey - sy) * ease_out(q)
            d.line((sx, sy, px, py), fill=RED + (230,), width=9)
            ang = math.atan2(py - sy, px - sx)
            d.polygon([(px + 26 * math.cos(ang), py + 26 * math.sin(ang)), (px + 20 * math.cos(ang + 2.3), py + 20 * math.sin(ang + 2.3)),
                       (px + 20 * math.cos(ang - 2.3), py + 20 * math.sin(ang - 2.3))], fill=RED + (255,))
    return False

def scene_swap(frame, s, lt, ld):
    a = s["args"]; frame.alpha_composite(base_bg())
    old = big_word(a["old"], 210, (130, 130, 128)); paste(frame, old, SW / 2, 640, "cm")
    q = clamp(lt / 0.25); d = ImageDraw.Draw(frame)
    x0 = SW / 2 - old.width / 2 - 20; d.line((x0, 650, x0 + (old.width + 40) * q, 630), fill=RED + (255,), width=16)
    q2 = (lt - 0.15) / 0.2
    if q2 > 0:
        new = big_word(a["new"], 330, RED); k = 1 + 0.5 * (1 - ease_out(q2))
        new = new.resize((int(new.width * k), int(new.height * k)), Image.BILINEAR)
        g = glow(new, 26, 1.4); paste(frame, g, SW / 2, 960, "cm", opacity=0.6); paste(frame, new, SW / 2, 960, "cm")
    return 0.15 < lt < 0.2

def scene_list(frame, s, lt, ld):
    a = s["args"]; frame.alpha_composite(base_bg())
    f = font(F_BEBAS, 150); items = a["items"]
    ts = [0.15 + w for w in (1.2, 1.95, 2.85)]                   # synced to "fiancée / love letters / theatre tickets"
    words_ = [(w, b) for w, b, _ in V[s["id"]]["words"]]
    keys = ["fianc", "love", "theat"]
    for i, kk in enumerate(keys):
        m = next((b for w, b in words_ if w.lower().startswith(kk)), None)
        if m is not None: ts[i] = m
    hd = text_img("PURE FICTION", font(F_OSW_B, 40), fill=GOLD, tracking=8); paste(frame, hd, 90, 420)
    ImageDraw.Draw(frame).line((90, 470, 90 + hd.width, 470), fill=GOLD + (220,), width=3)
    for i, it in enumerate(items):
        q = (lt - ts[i]) / 0.2
        if q <= 0: continue
        y = 560 + i * 200; t = text_img(it, f, fill=OFF); paste(frame, t, 90 + 40 * (1 - ease_out(q)), y, opacity=clamp(q))
        q2 = (lt - ts[i] - 0.35) / 0.15
        if q2 > 0:
            stp = stamp("FAKE", 90, seed=10 + i, rot=-14 + 6 * i); k = 1 + 0.8 * (1 - ease_out(q2))
            stp = stp.resize((int(stp.width * k), int(stp.height * k)), Image.BILINEAR)
            paste(frame, stp, min(90 + t.width + 120, SW - 150), y + 80, "cm", opacity=clamp(q2 * 1.5))
    return False

LOGO = None
def scene_end(frame, s, lt, ld):
    global LOGO
    frame.alpha_composite(bg_blur("sicily_loc", True))
    if LOGO is None: LOGO = Image.open(BRAND).convert("RGBA").resize((300, 300), Image.LANCZOS)
    paste(frame, LOGO, SW / 2, 520, "cm", opacity=clamp(lt / 0.4))
    f1 = font(F_OSW_B, 44); t1 = text_img("WATCH THE FULL DOCUMENTARY", f1, fill=GOLD, tracking=6)
    paste(frame, t1, SW / 2, 760, "cm", opacity=clamp((lt - 0.2) / 0.4))
    f2 = font(F_BEBAS, 140)
    for i, ln in enumerate(["THE DEAD MAN", "WHO FOOLED HITLER"]):
        q = (lt - 0.35 - 0.15 * i) / 0.3
        if q > 0: paste(frame, text_img(ln, f2, fill=OFF if i == 0 else RED), SW / 2, 880 + i * 140 + 30 * (1 - ease_out(q)), "cm", opacity=clamp(q))
    # bouncing arrow toward the Short's related-video link (bottom-left of the Shorts UI)
    q = clamp((lt - 0.9) / 0.3)
    if q > 0:
        bob = 18 * math.sin(lt * 7)
        f3 = font(F_OSW_B, 46); t3 = text_img("TAP THE LINK BELOW", f3, fill=OFF, tracking=5)
        box = Image.new("RGBA", (t3.width + 50, t3.height + 26), RED + (240,)); paste(box, t3, 25, 11)
        paste(frame, box, SW / 2, 1290 + bob * 0.3, "cm", opacity=q)
        d = ImageDraw.Draw(frame); cx = 300; cy = 1440 + bob
        d.polygon([(cx - 55, cy), (cx + 55, cy), (cx, cy + 70)], fill=RED + (int(255 * q),))
        d.rectangle((cx - 20, cy - 70, cx + 20, cy), fill=RED + (int(255 * q),))
    return False

KINDS = dict(photo=scene_photo, secret=scene_secret, word=scene_word, swap=scene_swap, list=scene_list, end=scene_end)

# ---------------- captions ----------------
def caption_chunks():
    chunks = []; cur = []
    for w, a, b in WORDS:
        cur.append((w, a, b))
        if len(cur) >= 3 or w.endswith((".", ",", "?", ":")):
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        end = chunks[i + 1][0][1] if i + 1 < len(chunks) else c[-1][2] + 0.4
        out.append((c, c[0][1], min(end, c[-1][2] + 0.6)))
    return out
CHUNKS = caption_chunks()
CAP_Y = 1400

def captions(frame, t):
    for c, a, b in CHUNKS:
        if not (a <= t < b): continue
        f = font(F_BEBAS, 118); parts = []
        for w, wa, wb in c:
            clean = w.strip(".,?:").upper()
            col = RED if w.lower().strip(".,?:") in HIGHLIGHT or w.lower() in HIGHLIGHT else OFF
            parts.append((clean, col, wa))
        gap = 28; imgs = [text_img(p, f, fill=col) for p, col, _ in parts]
        tw = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
        x = SW / 2 - tw / 2
        for (p, col, wa), im in zip(parts, imgs):
            if t >= wa - 0.03:
                q = clamp((t - wa + 0.03) / 0.12); k = 1 + 0.18 * (1 - ease_out(q))
                sh = text_img(p, f, fill=(0, 0, 0)).filter(ImageFilter.GaussianBlur(7))
                paste(frame, sh, x + im.width / 2 + 4, CAP_Y + 8, "cm", opacity=0.95)
                imk = im.resize((int(im.width * k), int(im.height * k)), Image.BILINEAR)
                paste(frame, imk, x + im.width / 2, CAP_Y, "cm")
            x += im.width + gap
        break

# ---------------- frame ----------------
def seg_at(t):
    for s in SEGS:
        if s["start"] <= t < s["end"]: return s
    return SEGS[-1]

def render_frame(fi):
    t = fi / FPS; s = seg_at(t); lt = t - s["start"]; ld = s["end"] - s["start"]
    frame = Image.new("RGBA", (SW, SH), BLACK + (255,))
    flash = KINDS[s["kind"]](frame, s, lt, ld)
    if s["kind"] not in ("end",): header(frame, t)
    lab = {"secret": "ILLUSTRATION"}.get(s["kind"])
    if lab: label(frame, lab)
    if s["kind"] != "swap": captions(frame, t)
    arr = np.asarray(frame.convert("RGB")).astype(np.float32)
    # stamp impact shake
    a = s["args"]
    if s["kind"] == "photo" and a.get("stamp"):
        q = (lt - ld * 0.52) / 0.18
        if 0 < q < 1.6:
            amp = 14 * (1 - q / 1.6); dx = int(amp * math.sin(q * 40)); dy = int(amp * math.cos(q * 33))
            arr = np.roll(np.roll(arr, dx, 1), dy, 0)
    if flash: arr = arr * 0.4 + 255 * 0.6
    arr *= vig()
    g = GRAIN[fi % len(GRAIN)]; g = np.repeat(np.repeat(g, 2, 0), 2, 1)
    arr += g[..., None]
    if t > TOT - 0.5: arr *= clamp((TOT - t) / 0.5)
    return np.clip(arr, 0, 255).astype(np.uint8)

def render_chunk(ci, n):
    N = int(TOT * FPS); a, b = N * ci // n, N * (ci + 1) // n
    out = os.path.join(B, f"chunk_{ci}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{SW}x{SH}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(a, b): p.stdin.write(render_frame(fi).tobytes())
    p.stdin.close(); p.wait(); print("chunk", ci, "done", flush=True)

if __name__ == "__main__":
    if sys.argv[1] == "still":
        for tt in map(float, sys.argv[2:]):
            Image.fromarray(render_frame(int(tt * FPS))).save(os.path.join(B, f"still_{tt:05.1f}.png"))
    elif sys.argv[1] == "chunk":
        render_chunk(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "info":
        print("TOTAL", round(TOT, 2))
        for s in SEGS: print(s["id"], round(s["start"], 2), round(s["end"], 2), s["kind"])
