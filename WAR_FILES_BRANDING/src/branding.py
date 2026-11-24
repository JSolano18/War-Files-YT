"""WAR FILES channel branding concepts: 3 logo directions + matching banners + size/crop mockups.
Palette and fonts follow WAR_FILES_PLAYBOOK (gold #C9A54C, black, off-white, steel, accent red)."""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(__file__); OUT = os.path.join(HERE, "..")
FD = os.path.join(HERE, "..", "..", "WAR_FILES_OPERATION_MINCEMEAT", "project", "fonts")
def F(n, s): return ImageFont.truetype(os.path.join(FD, n), int(s))
BEB, OSW, OSWB, TYPE = "bebas-neue-latin-400-normal.ttf", "oswald-latin-400-normal.ttf", "oswald-latin-600-normal.ttf", "special-elite-latin-400-normal.ttf"
GOLD = (201, 165, 76); GOLD_L = (232, 202, 120); GOLD_D = (120, 92, 38); BLK = (10, 11, 14); WHT = (242, 239, 232); STEEL = (118, 128, 138); RED = (200, 38, 30)
S = 2000  # logo master size


def noise(w, h, cell, seed):
    rng = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(3):
        c = max(2, cell // (2 ** o)); sm = (rng.random((h // c + 2, w // c + 2)) * 255).astype(np.uint8)
        acc += np.asarray(Image.fromarray(sm).resize((w, h), Image.BICUBIC), np.float32) / 255 * amp; tot += amp; amp *= 0.5
    return acc / tot


def metal(w, h, base, seed=1, brushed=True):
    """brushed-metal / brass fill"""
    n = noise(w, h, 4, seed) if brushed else noise(w, h, 40, seed)
    y = np.linspace(0, 1, h)[:, None]; shade = 0.75 + 0.45 * np.exp(-((y - 0.3) / 0.25) ** 2) - 0.2 * y
    arr = np.array(base, np.float32)[None, None] * (shade * (0.88 + 0.24 * n))[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


def stencil_text(txt, size, fill, bridges=True, tracking=0):
    f = F(BEB, size); w = int(sum(f.getlength(c) for c in txt) + tracking * (len(txt) - 1)) + 20; asc, desc = f.getmetrics()
    im = Image.new("L", (w, asc + desc + 20), 0); d = ImageDraw.Draw(im); x = 10
    for c in txt:
        d.text((x, 10), c, font=f, fill=255)
        if bridges and c.strip():   # stencil bridges: two thin horizontal cuts per glyph
            cw = f.getlength(c); bb = f.getbbox(c)
            for fy in (0.42,):
                y = 10 + bb[1] + (bb[3] - bb[1]) * fy; d.rectangle([x - 2, y, x + cw + 2, y + size * 0.035], fill=0)
        x += f.getlength(c) + tracking
    out = Image.new("RGBA", im.size, fill + (0,)); out.putalpha(im); return out


def circle_mask(size):
    m = Image.new("L", (size * 4, size * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    return m.resize((size, size), Image.LANCZOS)


def ring_text(img, text, r, size, col, start=-90, span=300):
    f = F(OSWB, size); d = ImageDraw.Draw(img); c = img.size[0] / 2
    chars = list(text); n = len(chars)
    for i, ch in enumerate(chars):
        a = math.radians(start - span / 2 + span * i / (n - 1)) if n > 1 else math.radians(start)
        g = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); ImageDraw.Draw(g).text((size, size), ch, font=f, fill=col, anchor="mm")
        g = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        img.alpha_composite(g, (int(c + r * math.cos(a) - size), int(c + r * math.sin(a) - size)))


# ───────────── LOGO A — "SEAL": brass seal, stencil WF monogram ─────────────
def logo_A():
    im = Image.new("RGBA", (S, S), BLK + (255,)); c = S / 2
    brass = metal(S, S, GOLD, 3); ring = Image.new("L", (S, S), 0); d = ImageDraw.Draw(ring)
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], fill=255); d.ellipse([S * 0.10, S * 0.10, S * 0.90, S * 0.90], fill=0)
    d.ellipse([S * 0.145, S * 0.145, S * 0.855, S * 0.855], fill=255); d.ellipse([S * 0.165, S * 0.165, S * 0.835, S * 0.835], fill=0)
    im.paste(brass, (0, 0), ring)
    ring_text(im, "WAR FILES · DECLASSIFIED HISTORY · WAR FILES · DECLASSIFIED HISTORY ·", S * 0.425, int(S * 0.040), BLK, start=-90, span=355)
    mono = stencil_text("WF", S * 0.62, GOLD_L, tracking=-S * 0.02)
    mb = metal(mono.size[0], mono.size[1], GOLD, 5); mb.putalpha(mono.getchannel("A"));
    sh = Image.new("RGBA", mono.size, (0, 0, 0, 0)); sh.putalpha(mono.getchannel("A").point(lambda v: v * 0.8))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (int(c - mono.size[0] / 2 + 10), int(c - mono.size[1] / 2 + 30)))
    im.alpha_composite(mb, (int(c - mono.size[0] / 2), int(c - mono.size[1] / 2 + 10)))
    d = ImageDraw.Draw(im); d.rectangle([c - S * 0.16, c + S * 0.255, c + S * 0.16, c + S * 0.27], fill=RED)   # red underline accent
    return im


# ───────────── LOGO B — "FILE": folder tab + red stamp ─────────────
def logo_B():
    im = Image.new("RGBA", (S, S), BLK + (255,)); d = ImageDraw.Draw(im)
    fx0, fy0, fx1, fy1 = S * 0.08, S * 0.27, S * 0.92, S * 0.82
    folder = metal(S, S, (196, 160, 98), 7, brushed=False); m = Image.new("L", (S, S), 0); md = ImageDraw.Draw(m)
    md.rounded_rectangle([fx0, fy0, fx1, fy1], radius=int(S * 0.03), fill=255); md.rounded_rectangle([fx0, fy0 - S * 0.07, fx0 + S * 0.26, fy0 + S * 0.02], radius=int(S * 0.025), fill=255)
    im.paste(folder, (0, 0), m)
    t = stencil_text("WAR FILES", S * 0.22, BLK, bridges=False, tracking=S * 0.008); im.alpha_composite(t, (int(S / 2 - t.size[0] / 2), int(fy0 + S * 0.05)))
    st = stencil_text("TOP SECRET", S * 0.15, RED, bridges=False, tracking=S * 0.01)
    w, h = st.size; box = Image.new("RGBA", (w + 60, h + 30), (0, 0, 0, 0)); bd = ImageDraw.Draw(box); bd.rectangle([6, 6, w + 54, h + 24], outline=RED + (255,), width=14); box.alpha_composite(st, (30, 10))
    n = (noise(box.size[0], box.size[1], 6, 2) > 0.33).astype(np.float32); a = np.asarray(box).copy(); a[..., 3] = (a[..., 3] * n).astype(np.uint8)
    box = Image.fromarray(a, "RGBA").rotate(-10, expand=True, resample=Image.BICUBIC); im.alpha_composite(box, (int(S / 2 - box.size[0] / 2), int(S * 0.52)))
    return im


# ───────────── LOGO C — "HELMET": evolution of the current logo, flat and bold ─────────────
def logo_C():
    im = Image.new("RGBA", (S, S), BLK + (255,)); c = S / 2; d = ImageDraw.Draw(im)
    d.ellipse([S * 0.03, S * 0.03, S * 0.97, S * 0.97], outline=GOLD, width=int(S * 0.025))
    for i in range(24):   # rivets like the current logo, simplified
        a = i / 24 * 2 * math.pi; x, y = c + math.cos(a) * S * 0.445, c + math.sin(a) * S * 0.445; r = S * 0.012
        d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD_D)
    hel = metal(S, S, (150, 150, 140), 9, brushed=False); m = Image.new("L", (S, S), 0); md = ImageDraw.Draw(m)
    md.chord([S * 0.26, S * 0.20, S * 0.74, S * 0.86], 180, 360, fill=255)            # dome (side profile)
    md.polygon([(S * 0.14, S * 0.545), (S * 0.86, S * 0.545), (S * 0.80, S * 0.575), (S * 0.20, S * 0.575)], fill=255)   # flat brim
    md.polygon([(S * 0.26, S * 0.53), (S * 0.74, S * 0.53), (S * 0.75, S * 0.55), (S * 0.25, S * 0.55)], fill=255)
    im.paste(hel, (0, 0), m)
    d = ImageDraw.Draw(im); d.arc([S * 0.30, S * 0.30, S * 0.62, S * 0.62], 200, 260, fill=(220, 220, 210), width=int(S * 0.02))  # highlight
    d.ellipse([S * 0.555, S * 0.37, S * 0.585, S * 0.40], fill=BLK); d.ellipse([S * 0.43, S * 0.43, S * 0.452, S * 0.452], fill=BLK)  # bullet holes
    t = stencil_text("WAR FILES", S * 0.20, GOLD_L, tracking=S * 0.006); mb = metal(t.size[0], t.size[1], GOLD, 4); mb.putalpha(t.getchannel("A"))
    im.alpha_composite(mb, (int(c - t.size[0] / 2), int(S * 0.62)))
    d.line([(S * 0.27, S * 0.865), (S * 0.73, S * 0.865)], fill=RED, width=int(S * 0.018))
    return im


# ───────────── BANNER ─────────────
def banner(logo, tag="DECLASSIFIED HISTORY  ·  ESPIONAGE  ·  WAR"):
    BW, BH = 2560, 1440; n = noise(BW, BH, 120, 11)
    arr = np.array(BLK, np.float32)[None, None] * (0.8 + 0.6 * n)[..., None]
    yy, xx = np.mgrid[:BH, :BW]; glow = np.exp(-(((xx - BW / 2) / 900) ** 2 + ((yy - BH / 2) / 260) ** 2))
    arr += glow[..., None] * np.array([46, 36, 22])
    bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(bg, "RGBA")
    # faint Europe outline in steel
    try:
        sys.path.insert(0, os.path.join(HERE, "..", "..", "WAR_FILES_OPERATION_MINCEMEAT", "project", "src"))
        from scenes_m import countries
        cx, cy, sc = 12, 47, 46; cosl = math.cos(math.radians(47))
        for nm, polys in countries().items():
            for p in polys:
                xs = BW / 2 + (p[:, 0] - cx) * cosl * sc; ys = BH / 2 - (p[:, 1] - cy) * sc
                if len(xs) > 2: d.polygon(list(zip(xs.tolist(), ys.tolist())), outline=STEEL + (55,))
    except Exception as e: print("map skipped", e)
    # file folders drifting at the edges (outside safe area)
    for i, (x, y, r) in enumerate([(260, 560, -8), (2330, 820, 7), (420, 980, 5), (2150, 420, -6)]):
        f = Image.new("RGBA", (520, 360), (0, 0, 0, 0)); fd = ImageDraw.Draw(f)
        fd.rounded_rectangle([0, 40, 519, 359], 14, fill=(150, 122, 74, 110)); fd.rounded_rectangle([0, 0, 180, 60], 12, fill=(150, 122, 74, 110))
        fd.text((260, 220), "CLASSIFIED", font=F(BEB, 70), fill=RED + (120,), anchor="mm")
        bg.alpha_composite(f.rotate(r, expand=True, resample=Image.BICUBIC), (x - 260, y - 180))
    # safe area 1546x423 centred
    sx0, sy0 = (BW - 1546) / 2, (BH - 423) / 2
    lg = logo.resize((330, 330), Image.LANCZOS); m = circle_mask(330)
    bg.paste(lg, (int(sx0 + 40), int(BH / 2 - 165)), m)
    t = F(BEB, 230); d.text((sx0 + 430, BH / 2 - 40), "WAR FILES", font=t, fill=WHT, anchor="lm")
    d.line([(sx0 + 436, BH / 2 + 64), (sx0 + 1480, BH / 2 + 64)], fill=GOLD, width=4)
    d.text((sx0 + 436, BH / 2 + 118), tag, font=F(OSW, 52), fill=GOLD, anchor="lm")
    return bg


def avatar_sheet(logos):
    """each logo at real YouTube sizes: 800, 176, 98, 48, 32 px circles on dark and light UI"""
    sizes = [400, 176, 98, 48, 32]; W = 60 + sum(s + 40 for s in sizes); H = 120 + len(logos) * 2 * 440
    out = Image.new("RGB", (W, len(logos) * 2 * 460 + 40), (15, 15, 15)); d = ImageDraw.Draw(out)
    y = 30
    for name, lg in logos:
        for bgc, tc in (((15, 15, 15), (230, 230, 230)), ((255, 255, 255), (20, 20, 20))):
            d.rectangle([0, y - 10, W, y + 440], fill=bgc); d.text((30, y), name, font=F(OSWB, 34), fill=tc); x = 30
            for s in sizes:
                a = lg.resize((s, s), Image.LANCZOS); out.paste(a, (x, y + 50), circle_mask(s)); x += s + 40
            y += 460
    return out


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "logos"), exist_ok=True); os.makedirs(os.path.join(OUT, "banners"), exist_ok=True)
    L = [("A — SEAL (WF monogram)", "A_SEAL", logo_A()), ("B — CLASSIFIED FILE", "B_FILE", logo_B()), ("C — HELMET (evolution)", "C_HELMET", logo_C())]
    for name, key, lg in L:
        lg.convert("RGB").resize((800, 800), Image.LANCZOS).save(os.path.join(OUT, "logos", f"LOGO_{key}_800.png"))
        b = banner(lg); b.convert("RGB").save(os.path.join(OUT, "banners", f"BANNER_{key}_2560x1440.jpg"), quality=92)
        # safe-area preview (what phones show)
        sx0, sy0 = (2560 - 1546) // 2, (1440 - 423) // 2
        b.convert("RGB").crop((sx0, sy0, sx0 + 1546, sy0 + 423)).save(os.path.join(OUT, "banners", f"BANNER_{key}_mobile_safe_area.jpg"), quality=90)
        print(key)
    avatar_sheet([(n, lg) for n, k, lg in L]).save(os.path.join(OUT, "logos", "LOGO_SIZE_TEST.png"))
