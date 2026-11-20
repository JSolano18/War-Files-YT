"""Thumbnails at 3840x2160 (+1280x720). Fully illustrated; no photographs."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from props import *
TW, TH = 3840, 2160
OUT = os.path.join(ROOT, "..")
def radialT(cx, cy, r): return radial(TW, TH, cx, cy, r)
def silhouette(h, rim=(255, 60, 40), side=1):
    w = int(h * 0.5); im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    c = w / 2; s = h
    d.ellipse([c - 0.055 * s, 0.02 * s, c + 0.055 * s, 0.16 * s], fill=255)
    d.polygon([(c - 0.03 * s, 0.14 * s), (c + 0.03 * s, 0.14 * s), (c + 0.035 * s, 0.19 * s), (c - 0.035 * s, 0.19 * s)], fill=255)
    coat = [(c - 0.07 * s, 0.17 * s), (c + 0.07 * s, 0.17 * s), (c + 0.15 * s, 0.215 * s), (c + 0.17 * s, 0.30 * s), (c + 0.175 * s, 0.55 * s),
            (c + 0.19 * s, 0.62 * s), (c + 0.16 * s, 0.63 * s), (c + 0.18 * s, 0.98 * s), (c + 0.06 * s, 0.98 * s), (c + 0.04 * s, 1.0 * s),
            (c - 0.04 * s, 1.0 * s), (c - 0.06 * s, 0.98 * s), (c - 0.18 * s, 0.98 * s), (c - 0.16 * s, 0.63 * s), (c - 0.19 * s, 0.62 * s),
            (c - 0.175 * s, 0.55 * s), (c - 0.17 * s, 0.30 * s), (c - 0.15 * s, 0.215 * s)]
    d.polygon(coat, fill=255)
    d.polygon([(c - 0.07 * s, 0.17 * s), (c - 0.05 * s, 0.12 * s), (c - 0.02 * s, 0.2 * s)], fill=255)
    d.polygon([(c + 0.07 * s, 0.17 * s), (c + 0.05 * s, 0.12 * s), (c + 0.02 * s, 0.2 * s)], fill=255)
    m = im.filter(ImageFilter.GaussianBlur(2))
    ma = np.asarray(m, np.float32) / 255
    shifted = np.roll(ma, -side * int(h * 0.008), axis=1)
    rimm = np.clip(ma - shifted, 0, 1)
    rimm = np.asarray(Image.fromarray((rimm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(h * 0.004)), np.float32) / 255
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = np.array([6, 6, 8]) + rimm[..., None] * np.array(rim) * 1.6
    out[..., 3] = np.maximum(ma, rimm) * 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")
def big_text(txt, size, col, track=10, stroke=0):
    f = font(F_BEBAS, size)
    im = text_img(txt, f, col, tracking=track)
    sh = Image.new("RGBA", (im.size[0] + 80, im.size[1] + 80), (0, 0, 0, 0)); a = im.getchannel("A")
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (40, 50)); sh = sh.filter(ImageFilter.GaussianBlur(size * 0.06))
    sh.alpha_composite(im, (40, 40))
    return sh
def grade(img, red_side="left", grain=0.035):
    arr = np.asarray(img.convert("RGB"), np.float32)
    rx = TW * (0.05 if red_side == "left" else 0.95)
    rmask = radialT(rx, TH * 0.45, TW * 0.7)[..., None] ** 1.3
    arr = arr * (1 - 0.35 * rmask) + rmask * np.array([170, 20, 12]) * 0.9 + arr * rmask * np.array([0.6, 0.0, 0.0])
    bmask = radialT(TW - rx, TH * 0.35, TW * 0.8)[..., None] ** 1.5
    arr = arr + bmask * np.array([10, 30, 60])
    arr *= vignette(TW, TH, 0.55)[..., None]
    arr += np.random.default_rng(1).normal(0, 255 * grain, arr.shape[:2])[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
def diamond_pile(cv, cx, cy, n, scale, seed):
    rng = random.Random(seed)
    for i in range(n):
        a = rng.uniform(0, 6.28); r = rng.uniform(0, 1) ** 0.7
        x = cx + math.cos(a) * r * scale * 1.6; y = cy + math.sin(a) * r * scale * 0.45 - (1 - r) * scale * 0.25
        s = int(scale * rng.uniform(0.18, 0.42))
        dm = diamond(s, phase=rng.uniform(0, 10), seed=rng.randint(0, 999), rot=rng.uniform(0, 6), squash=rng.uniform(0.45, 0.7))
        paste(cv, dm, x, y, "cm")
    for i in range(7):
        g = glint_sprite(int(scale * rng.uniform(0.5, 1.0)))
        paste(cv, g, cx + rng.uniform(-1.2, 1.2) * scale, cy + rng.uniform(-0.35, 0.2) * scale, "cm", rng.uniform(0.6, 1.0))
def vault_open_plate(DS, cx, cy, cv):
    from scenes import VaultDoor
    door = vault_door(DS, (0.95, 1.0, 1.06))
    interior = Image.new("RGBA", (DS, DS), (5, 5, 7, 255))
    bw, bh = int(DS * 0.095), int(DS * 0.06)
    for r in range(18):
        for c in range(14):
            k = r * 14 + c
            if (r * 7 + c * 3) % 5 < 3:
                o, dr, dwid = box_open(bw, bh, 1, k); interior.alpha_composite(o, (c * (bw + 5) - 30, r * (bh + 5) - 20)); interior.alpha_composite(dr, (max(0, c * (bw + 5) - 30 - dwid), r * (bh + 5) - 20))
            else: interior.alpha_composite(box_closed(bw, bh, 400 + k, k % 7), (c * (bw + 5) - 30, r * (bh + 5) - 20))
    ia = np.asarray(interior, np.float32); gm = radial(DS, DS, DS * 0.5, DS * 0.6, DS * 0.6)
    ia[..., 0] *= 0.25 + 1.1 * gm; ia[..., 1] *= 0.15 + 0.55 * gm; ia[..., 2] *= 0.15 + 0.4 * gm
    interior = Image.fromarray(ia.clip(0, 255).astype(np.uint8), "RGBA")
    m = Image.new("L", (DS, DS), 0); ImageDraw.Draw(m).ellipse([DS * 0.115, DS * 0.115, DS * 0.885, DS * 0.885], fill=255)
    fa = np.asarray(door).copy(); yy, xx = np.mgrid[:DS, :DS]; rr = np.sqrt((xx - DS / 2) ** 2 + (yy - DS / 2) ** 2) / (DS / 2); fa[rr < 0.80, 3] = 0
    x0, y0 = int(cx - DS / 2), int(cy - DS / 2)
    cv.paste(interior, (x0, y0), m); cv.alpha_composite(Image.fromarray(fa, "RGBA"), (x0, y0))
    slab = door.resize((int(DS * 0.30), DS), Image.LANCZOS); sa = np.asarray(slab).astype(np.float32); sa[..., :3] *= 0.6
    edge = Image.new("RGBA", (int(DS * 0.36), DS), (0, 0, 0, 0)); ImageDraw.Draw(edge).ellipse([0, 0, int(DS * 0.36) - 1, DS - 1], fill=(70, 72, 76, 255))
    sx = int(x0 + DS * 0.95); cv.alpha_composite(edge, (sx - 30, y0)); cv.alpha_composite(Image.fromarray(sa.clip(0, 255).astype(np.uint8), "RGBA"), (sx, y0))

def concept_A():
    cv = bg_plate(TW, TH, 3, (8, 9, 12), (30, 38, 52), 0.7, 0.3).convert("RGBA")
    vault_open_plate(1900, TW * 0.60, TH * 0.47, cv)
    fl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); ImageDraw.Draw(fl).rectangle([0, TH * 0.86, TW, TH], fill=(10, 10, 12, 255)); cv.alpha_composite(fl.filter(ImageFilter.GaussianBlur(30)))
    paste(cv, silhouette(1500, side=1), TW * 0.30, TH * 1.02, "cb")
    diamond_pile(cv, TW * 0.76, TH * 0.90, 30, 470, 4)
    cv = grade(cv, "left")
    paste(cv, glow(big_text("$100,000,000", 560, GOLD, 8), 40, 0.5), TW * 0.5, TH * 0.20, "cm")
    paste(cv, big_text("HOW DID THEY DO IT?", 220, WHITE, 14), TW * 0.31, TH * 0.86, "cm")
    return cv
def concept_B():
    cv = bg_plate(TW, TH, 5, (6, 6, 8), (34, 30, 30), 0.5, 0.4).convert("RGBA")
    door = vault_door(1500); dd = Image.fromarray((np.asarray(door).astype(np.float32) * [0.45, 0.45, 0.5, 1]).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(10))
    paste(cv, dd, TW * 0.70, TH * 0.48, "cm")
    # backlight halo
    hl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); ImageDraw.Draw(hl).ellipse([TW * 0.22, TH * 0.15, TW * 0.48, TH * 0.75], fill=(220, 60, 40, 150)); cv.alpha_composite(hl.filter(ImageFilter.GaussianBlur(220)))
    paste(cv, silhouette(2050, rim=(255, 80, 50), side=-1), TW * 0.35, TH * 1.08, "cb")
    # case file corner
    from scenes import folder_card
    card = folder_card(980, 640, "L. NOTARBARTOLO", "—", "TENANT, ANTWERP DIAMOND CENTRE", "", 0).rotate(8, expand=True, resample=Image.BICUBIC)
    card = card.resize((int(card.size[0] * 1.2), int(card.size[1] * 1.2)))
    paste(cv, card, TW * 0.78, TH * 0.75, "cm", 0.92)
    cv = grade(cv, "left", 0.03)
    paste(cv, glow(big_text("$100 MILLION", 470, GOLD, 8), 40, 0.5), TW * 0.71, TH * 0.18, "cm")
    paste(cv, big_text("THE INSIDE MAN", 230, WHITE, 14), TW * 0.71, TH * 0.40, "cm")
    return cv
def concept_C():
    cv = Image.new("RGBA", (TW, TH), (14, 15, 18, 255))
    bw, bh, g = 300, 186, 12
    rng = random.Random(3)
    for r in range(TH // (bh + g) + 1):
        for c in range(TW // (bw + g) + 1):
            x, y = c * (bw + g), r * (bh + g)
            o, dr, dwid = box_open(bw, bh, 1, r * 20 + c); cv.alpha_composite(o, (x, y)); cv.alpha_composite(dr, (max(0, x - dwid), y))
    arr = np.asarray(cv, np.float32)[..., :3] * (0.3 + 1.0 * radialT(TW * 0.5, TH * 0.55, TW * 0.55)[..., None] ** 1.4)
    cv = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    fl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); ImageDraw.Draw(fl).rectangle([0, TH * 0.78, TW, TH], fill=(8, 8, 10, 245)); cv.alpha_composite(fl.filter(ImageFilter.GaussianBlur(40)))
    diamond_pile(cv, TW * 0.5, TH * 0.88, 22, 470, 9)
    cv = grade(cv, "right", 0.03)
    paste(cv, glow(big_text("$100,000,000", 580, GOLD, 8), 40, 0.55), TW * 0.5, TH * 0.38, "cm")
    paste(cv, big_text("STILL MISSING", 230, WHITE, 18), TW * 0.5, TH * 0.62, "cm")
    paste(cv, big_text("THE DIAMOND HEIST", 250, WHITE, 26), TW * 0.5, TH * 0.15, "cm")
    return cv
if __name__ == "__main__":
    for nm, fn in (("A", concept_A), ("B", concept_B), ("C", concept_C)):
        im = fn().convert("RGB"); im.save(os.path.join(ROOT, "build", f"thumb_{nm}_3840.png"))
        im.resize((1280, 720), Image.LANCZOS).save(os.path.join(ROOT, "build", f"thumb_{nm}_1280.png")); print(nm)
