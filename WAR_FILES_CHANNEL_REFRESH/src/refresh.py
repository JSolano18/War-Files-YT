"""Channel refresh: new thumbnails for existing videos, built with WAR_FILES_PLAYBOOK/TITULOS_Y_MINIATURAS.md.
Antwerp heist (accent: diamond cyan) and Eli Cohen (accent: radio green). Original illustration only."""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "WAR_FILES_OPERATION_MINCEMEAT", "project", "src"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from common import font, text_img, paste, radial, smooth_noise, F_TYPE, F_OSW_B, F_OSW
from props import vault_door, box_open, box_closed, diamond, glint_sprite, skyline
from thumbs_m import TW, TH, grade
from thumbs_v2 import word, burn, GOLD, WHT, X3, Y3
OUT = os.path.join(HERE, "..")
CYAN = (90, 205, 245); GREEN = (70, 220, 140)


def dark_bg(seed, tint=(16, 18, 24), cx=0.5, cy=0.5):
    n = smooth_noise(TW, TH, 60, seed, 3); arr = np.array(tint, np.float32) * (0.6 + 0.7 * n)[..., None]
    arr *= (0.3 + 1.0 * radial(TW, TH, TW * cx, TH * cy, TW * 0.65) ** 1.2)[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


def open_vault(DS):
    """open circular vault door with boxes inside (RGBA, DS x DS*1.35)"""
    door = vault_door(DS, (0.95, 1.0, 1.06)); out = Image.new("RGBA", (int(DS * 1.35), DS), (0, 0, 0, 0))
    inner = Image.new("RGBA", (DS, DS), (6, 6, 8, 255)); bw, bh = int(DS * 0.1), int(DS * 0.064)
    for r in range(17):
        for c in range(12):
            k = r * 12 + c; x, y = c * (bw + 5) - 20, r * (bh + 5) - 20
            if (r * 7 + c * 3) % 5 < 3:
                o, dr, dw = box_open(bw, bh, 1, k); inner.alpha_composite(o, (x, y)); inner.alpha_composite(dr, (max(0, x - dw), y))
            else: inner.alpha_composite(box_closed(bw, bh, 300 + k, k % 7), (x, y))
    ia = np.asarray(inner, np.float32); gm = radial(DS, DS, DS * 0.5, DS * 0.6, DS * 0.6)
    ia[..., 0] *= 0.3 + 0.8 * gm; ia[..., 1] *= 0.35 + 0.9 * gm; ia[..., 2] *= 0.45 + 1.1 * gm
    inner = Image.fromarray(ia.clip(0, 255).astype(np.uint8), "RGBA")
    m = Image.new("L", (DS, DS), 0); ImageDraw.Draw(m).ellipse([DS * 0.115, DS * 0.115, DS * 0.885, DS * 0.885], fill=255)
    out.paste(inner, (0, 0), m)
    fa = np.asarray(door).copy(); yy, xx = np.mgrid[:DS, :DS]; rr = np.sqrt((xx - DS / 2) ** 2 + (yy - DS / 2) ** 2) / (DS / 2); fa[rr < 0.80, 3] = 0
    out.alpha_composite(Image.fromarray(fa, "RGBA"))
    slab = door.resize((int(DS * 0.30), DS), Image.LANCZOS); sa = np.asarray(slab).astype(np.float32); sa[..., :3] *= 0.6
    edge = Image.new("RGBA", (int(DS * 0.36), DS), (0, 0, 0, 0)); ImageDraw.Draw(edge).ellipse([0, 0, int(DS * 0.36) - 1, DS - 1], fill=(70, 72, 76, 255))
    out.alpha_composite(edge, (int(DS * 0.95) - 30, 0)); out.alpha_composite(Image.fromarray(sa.clip(0, 255).astype(np.uint8), "RGBA"), (int(DS * 0.95), 0))
    return out


def diamonds_pile(cv, cx, cy, n, scale, seed):
    rng = random.Random(seed)
    for i in range(n):
        a = rng.uniform(0, 6.28); r = rng.uniform(0, 1) ** 0.7
        s = int(scale * rng.uniform(0.2, 0.42))
        paste(cv, diamond(s, phase=rng.uniform(0, 10), seed=rng.randint(0, 999), rot=rng.uniform(0, 6), squash=rng.uniform(0.45, 0.7)),
              cx + math.cos(a) * r * scale * 1.5, cy + math.sin(a) * r * scale * 0.4, "cm")
    for i in range(6): paste(cv, glint_sprite(int(scale * rng.uniform(0.5, 0.9))), cx + rng.uniform(-1.1, 1.1) * scale, cy + rng.uniform(-0.3, 0.2) * scale, "cm", rng.uniform(0.6, 1))


def sandwich_bag(w):
    """half-eaten sandwich sealed in a police evidence bag (RGBA)"""
    h = int(w * 0.78); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 30, fill=(220, 228, 236, 70), outline=(230, 236, 240, 200), width=8)
    d.rectangle([0, 0, w, h * 0.12], fill=(200, 40, 34, 230)); d.text((w / 2, h * 0.06), "EVIDENCE", font=font(F_OSW_B, w * 0.07), fill=(255, 255, 255), anchor="mm")
    cx, cy = w * 0.5, h * 0.55; s = w * 0.36
    d.pieslice([cx - s, cy - s * 0.55, cx + s, cy + s * 0.75], 180, 360, fill=(204, 150, 88))
    d.rectangle([cx - s, cy + s * 0.08, cx + s, cy + s * 0.16], fill=(170, 60, 60))
    for k in range(7): d.ellipse([cx - s * 0.9 + k * s * 0.27, cy + s * 0.04, cx - s * 0.7 + k * s * 0.27, cy + s * 0.2], fill=(196, 80, 80), outline=(235, 205, 190))
    d.rectangle([cx - s, cy + s * 0.16, cx + s, cy + s * 0.34], fill=(216, 170, 110))
    bite = Image.new("L", (w, h), 0); ImageDraw.Draw(bite).ellipse([cx + s * 0.45, cy - s * 0.5, cx + s * 1.25, cy + s * 0.45], fill=255)
    for k in range(5):   # tooth marks
        ImageDraw.Draw(bite).ellipse([cx + s * 0.40, cy - s * 0.45 + k * s * 0.18, cx + s * 0.56, cy - s * 0.30 + k * s * 0.18], fill=255)
    arr = np.asarray(im).copy(); bm = np.asarray(bite) > 0; arr[bm] = (220, 228, 236, 70); im = Image.fromarray(arr, "RGBA"); d = ImageDraw.Draw(im)
    lab = Image.new("RGBA", (int(w * 0.42), int(h * 0.2)), (238, 232, 214, 255)); ld = ImageDraw.Draw(lab)
    ld.text((14, 10), "ITEM: SANDWICH", font=font(F_TYPE, w * 0.032), fill=(40, 34, 30)); ld.text((14, 10 + w * 0.045), "FOUND NEAR E19", font=font(F_TYPE, w * 0.032), fill=(40, 34, 30))
    ld.text((14, 10 + w * 0.09), "17 FEB 2003", font=font(F_TYPE, w * 0.032), fill=(150, 30, 24))
    im.alpha_composite(lab.rotate(4, expand=True, resample=Image.BICUBIC), (int(w * 0.06), int(h * 0.72)))
    return im


# ═════════════ ANTWERP ═════════════
def antwerp_1():   # big number + simple object (open vault)
    cv = dark_bg(3, (18, 24, 34), 0.68, 0.5)
    v = open_vault(1500); paste(cv, v, 2 * X3 + 120, TH * 0.52, "cm")
    diamonds_pile(cv, 2 * X3 - 60, TH * 0.90, 22, 360, 4)
    cv = burn(cv, TW * 0.30, TH * 0.40, TW * 0.34, TH * 0.34, 0.6); cv = grade(cv)
    paste(cv, word("ANTWERP  ·  2003", 90, GOLD, track=12), X3, Y3 * 0.38, "cm")
    paste(cv, word("$100,000,000", 270, GOLD, glow_col=(255, 210, 120)), X3 + 40, Y3 * 1.05, "cm")
    paste(cv, word("GONE", 330, CYAN, glow_col=CYAN), X3 - 120, Y3 * 1.95, "cm")
    return cv


def antwerp_2():   # hidden/evidence object + bold statement
    cv = dark_bg(7, (26, 22, 18), 0.33, 0.5)
    bag = sandwich_bag(1250).rotate(-6, expand=True, resample=Image.BICUBIC)
    paste(cv, bag, X3 + 40, TH * 0.52, "cm")
    cv = burn(cv, TW * 0.78, TH * 0.42, TW * 0.24, TH * 0.4, 0.6); cv = grade(cv)
    paste(cv, word("THE", 220, WHT), TW * 0.78, Y3 * 0.62, "cm")
    paste(cv, word("$100M", 300, GOLD, glow_col=(255, 210, 120)), TW * 0.78, Y3 * 1.32, "cm")
    paste(cv, word("MISTAKE", 250, CYAN, glow_col=CYAN), TW * 0.75, Y3 * 2.05, "cm")
    return cv


def antwerp_3():   # comparison
    cv = dark_bg(9, (16, 18, 24))
    d = ImageDraw.Draw(cv, "RGBA"); d.rectangle([TW / 2, 0, TW, TH], fill=(40, 30, 20, 120))
    vd = vault_door(820); paste(cv, vd, X3 - 40, TH * 0.47, "cm")
    bag = sandwich_bag(800).rotate(5, expand=True, resample=Image.BICUBIC); paste(cv, bag, 2 * X3 + 60, TH * 0.47, "cm")
    cv = grade(cv)
    paste(cv, word("10 SECURITY LAYERS", 130, WHT, track=6), X3 - 40, TH * 0.86, "cm")
    paste(cv, word("1 SANDWICH", 150, CYAN, track=6, glow_col=CYAN), 2 * X3 + 60, TH * 0.86, "cm")
    paste(cv, word("VS", 260, GOLD), TW / 2, TH * 0.46, "cm")
    return cv


# ═════════════ ELI COHEN ═════════════
def businessman(h, rim=(255, 170, 110), side=1):
    """1960s businessman silhouette: fedora, suit, briefcase (no face, no likeness)"""
    w = int(h * 0.62); m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); c = w * 0.45; s = h
    d.ellipse([c - 0.045 * s, 0.07 * s, c + 0.045 * s, 0.16 * s], fill=255)
    d.rounded_rectangle([c - 0.05 * s, 0.025 * s, c + 0.05 * s, 0.085 * s], radius=int(0.015 * s), fill=255)   # fedora crown
    d.ellipse([c - 0.09 * s, 0.07 * s, c + 0.09 * s, 0.095 * s], fill=255)                                     # brim
    d.polygon([(c - 0.03 * s, 0.15 * s), (c + 0.03 * s, 0.15 * s), (c + 0.035 * s, 0.185 * s), (c - 0.035 * s, 0.185 * s)], fill=255)
    suit = [(-0.07, 0.18), (0.07, 0.18), (0.14, 0.21), (0.15, 0.30), (0.15, 0.55), (0.12, 0.56), (0.11, 1.0), (0.015, 1.0), (0.0, 0.62), (-0.015, 1.0), (-0.11, 1.0), (-0.12, 0.56), (-0.15, 0.55), (-0.15, 0.30), (-0.14, 0.21)]
    d.polygon([(c + x * s, y * s) for x, y in suit], fill=255)
    bx = c + 0.12 * s; by = 0.58 * s; d.rounded_rectangle([bx, by, bx + 0.15 * s, by + 0.10 * s], int(0.01 * s), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.5)); ma = np.asarray(m, np.float32) / 255
    shf = np.roll(ma, -side * int(h * 0.007), axis=1); rimm = np.clip(ma - shf, 0, 1)
    rimm = np.asarray(Image.fromarray((rimm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(h * 0.003)), np.float32) / 255
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = np.array([7, 7, 9]) + rimm[..., None] * np.array(rim) * 1.7; out[..., 3] = np.maximum(ma, rimm) * 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def damascus_night(seed=5):
    cv = Image.new("RGBA", (TW, TH)); arr = np.zeros((TH, TW, 3), np.float32); g = np.linspace(0, 1, TH)[:, None]
    arr[:] = (np.array([4, 8, 18]) + np.array([30, 40, 70]) * g ** 1.6)[:, :, None].transpose(0, 2, 1) if False else (np.array([4, 8, 18])[None, None] + np.array([30, 40, 70])[None, None] * (g ** 1.6)[..., None])
    rng = np.random.default_rng(seed)
    for _ in range(400): x, y = rng.integers(0, TW), rng.integers(0, TH // 2); arr[y, x] += rng.uniform(40, 160)
    cv = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    sk = skyline(TW, TH, seed, int(TH * 0.86), (8, 10, 16, 255), (255, 200, 120), 0.10, scale=1.5, hmin=40, hmax=160)
    d = ImageDraw.Draw(sk)
    for mx in (TW * 0.22, TW * 0.61, TW * 0.83):   # minarets and domes
        d.rectangle([mx - 16, TH * 0.42, mx + 16, TH * 0.9], fill=(8, 10, 16, 255)); d.polygon([(mx - 16, TH * 0.42), (mx, TH * 0.34), (mx + 16, TH * 0.42)], fill=(8, 10, 16, 255))
        d.rectangle([mx - 26, TH * 0.52, mx + 26, TH * 0.535], fill=(8, 10, 16, 255))
        d.chord([mx + 40, TH * 0.66, mx + 260, TH * 0.86], 180, 360, fill=(8, 10, 16, 255))
    cv.alpha_composite(sk); return cv


def radio_set(w):
    h = int(w * 0.62); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, h * 0.1, w, h], 24, fill=(46, 52, 44)); d.rounded_rectangle([18, h * 0.14, w - 18, h * 0.96], 18, outline=(90, 96, 84), width=6)
    for i, x in enumerate((0.18, 0.38, 0.58)):
        cx, cy, r = w * x, h * 0.42, w * 0.07; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(24, 24, 22), outline=(140, 140, 128), width=5)
        d.line([(cx, cy), (cx + r * 0.8 * math.cos(i + 0.6), cy - r * 0.8 * math.sin(i + 0.6))], fill=(220, 220, 200), width=6)
    d.rectangle([w * 0.70, h * 0.28, w * 0.92, h * 0.56], fill=(18, 24, 18)); d.rectangle([w * 0.72, h * 0.30, w * 0.90, h * 0.54], fill=(40, 90, 60))
    d.ellipse([w * 0.76, h * 0.70, w * 0.84, h * 0.80], fill=GREEN + (255,))
    # Morse key
    d.rectangle([w * 0.12, h * 0.72, w * 0.55, h * 0.84], fill=(90, 70, 40)); d.line([(w * 0.16, h * 0.70), (w * 0.50, h * 0.66)], fill=(170, 160, 140), width=14)
    d.ellipse([w * 0.46, h * 0.60, w * 0.56, h * 0.70], fill=(20, 20, 20))
    return im


def passport(w):
    h = int(w * 0.68); im = Image.new("RGBA", (w, h), (214, 200, 168, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 90, 60), width=8)
    d.text((40, 30), "COVER IDENTITY  ·  1961–1965", font=font(F_TYPE, w * 0.032), fill=(90, 40, 30))
    ph = Image.new("RGBA", (int(w * 0.28), int(h * 0.56)), (40, 40, 42, 255)); pd = ImageDraw.Draw(ph)
    pw, phh = ph.size; pd.ellipse([pw * 0.28, phh * 0.18, pw * 0.72, phh * 0.55], fill=(14, 14, 16)); pd.pieslice([pw * 0.05, phh * 0.5, pw * 0.95, phh * 1.3], 180, 360, fill=(14, 14, 16))
    im.alpha_composite(ph.filter(ImageFilter.GaussianBlur(8)), (40, int(h * 0.24)))
    for i, (k, v) in enumerate([("NAME", "KAMEL AMIN THAABET"), ("OCCUPATION", "BUSINESSMAN"), ("RESIDENCE", "DAMASCUS")]):
        d.text((w * 0.36, h * 0.26 + i * h * 0.2), k, font=font(F_TYPE, w * 0.03), fill=(90, 80, 66)); d.text((w * 0.36, h * 0.31 + i * h * 0.2), v, font=font(F_TYPE, w * 0.045), fill=(30, 28, 26))
    st = word("ALIAS", int(w * 0.13), (200, 38, 30), track=12).rotate(-14, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(st, (int(w * 0.62), int(h * 0.66))); return im


def cohen_1():   # simple object + bold statement (the radio)
    cv = damascus_night(5)
    arr = np.asarray(cv, np.float32).copy(); arr[int(TH * 0.62):] *= 0.35; cv = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(cv); d.rectangle([0, TH * 0.74, TW, TH], fill=(30, 22, 14, 255))
    r = radio_set(1250); paste(cv, r, X3 + 20, TH * 0.70, "cm")
    gl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([X3 - 500, TH * 0.4, X3 + 500, TH * 1.1], fill=GREEN + (60,)); cv.alpha_composite(gl.filter(ImageFilter.GaussianBlur(140)))
    cv = burn(cv, TW * 0.78, TH * 0.40, TW * 0.24, TH * 0.4, 0.6); cv = grade(cv)
    paste(cv, word("DAMASCUS  ·  1965", 90, GOLD, track=12), TW * 0.78, Y3 * 0.38, "cm")
    paste(cv, word("HIS RADIO", 230, WHT), TW * 0.78, Y3 * 1.05, "cm")
    paste(cv, word("BETRAYED HIM", 200, GREEN, glow_col=GREEN), TW * 0.75, Y3 * 1.75, "cm")
    return cv


def cohen_2():   # hidden identity document
    cv = dark_bg(12, (24, 20, 16), 0.35, 0.5)
    p = passport(1400).rotate(5, expand=True, resample=Image.BICUBIC); paste(cv, p, X3 + 30, TH * 0.52, "cm")
    cv = burn(cv, TW * 0.80, TH * 0.42, TW * 0.22, TH * 0.4, 0.6); cv = grade(cv)
    paste(cv, word("ISRAEL'S", 200, WHT), TW * 0.81, Y3 * 0.75, "cm")
    paste(cv, word("MAN IN", 200, WHT), TW * 0.81, Y3 * 1.35, "cm")
    paste(cv, word("DAMASCUS", 210, GREEN, glow_col=GREEN), TW * 0.79, Y3 * 1.98, "cm")
    return cv


def cohen_3():   # silhouette + city + big number
    cv = damascus_night(8)
    fig = businessman(1200, rim=(120, 255, 170), side=1)
    paste(cv, fig, 2 * X3 + 80, TH * 1.03, "cb")
    cv = burn(cv, TW * 0.30, TH * 0.40, TW * 0.30, TH * 0.4, 0.55); cv = grade(cv)
    paste(cv, word("4 YEARS", 300, GREEN, glow_col=GREEN), X3, Y3 * 0.95, "cm")
    paste(cv, word("UNDERCOVER", 210, WHT), X3, Y3 * 1.72, "cm")
    paste(cv, word("INSIDE SYRIA", 110, GOLD, track=10), X3, Y3 * 2.25, "cm")
    return cv


if __name__ == "__main__":
    for folder, items in (("ANTWERP", [("A1_100M_GONE", antwerp_1), ("A2_100M_MISTAKE", antwerp_2), ("A3_10_LAYERS_VS_SANDWICH", antwerp_3)]),
                          ("ELI_COHEN", [("E1_RADIO_BETRAYED_HIM", cohen_1), ("E2_MAN_IN_DAMASCUS", cohen_2), ("E3_4_YEARS_UNDERCOVER", cohen_3)])):
        os.makedirs(os.path.join(OUT, folder), exist_ok=True)
        for nm, fn in items:
            fn().convert("RGB").resize((1280, 720), Image.LANCZOS).save(os.path.join(OUT, folder, f"THUMBNAIL_{nm}.png")); print(folder, nm)


# ═════════════ v2: with owner-supplied photos ═════════════
A = os.path.join(HERE, "..", "assets")

def faded_photo(path, height, tint, fade_left=0.35, fade_bottom=0.18, crop=None, contrast=1.2, fade_right=0.0):
    im = Image.open(path).convert("L")
    if crop: w, h = im.size; im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    im = ImageOps.autocontrast(im, cutoff=1); a = np.asarray(im, np.float32) / 255; a = np.clip((a - 0.5) * contrast + 0.5, 0, 1)
    rgb = a[..., None] * np.array(tint, np.float32) + (1 - a[..., None]) * np.array([6, 7, 9])
    s = height / im.size[1]; lay = Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).resize((int(im.size[0] * s), int(height)), Image.LANCZOS).convert("RGBA")
    lw, lh = lay.size; xx = np.linspace(0, 1, lw)[None, :]; yy = np.linspace(0, 1, lh)[:, None]
    m = np.clip(xx / max(1e-3, fade_left), 0, 1) ** 1.3 * (np.clip((1 - yy) / max(1e-3, fade_bottom), 0, 1) ** 0.8 if fade_bottom else 1)
    if fade_right: m = m * np.clip((1 - xx) / fade_right, 0, 1) ** 1.3
    arr = np.asarray(lay).copy(); arr[..., 3] = (m * 255).astype(np.uint8); return Image.fromarray(arr, "RGBA")


def antwerp_1b():   # big number + the surveillance-style still (owner-supplied) on the right two thirds
    cv = dark_bg(3, (14, 20, 26), 0.7, 0.5)
    ph = faded_photo(os.path.join(A, "antwerp_cctv_style_still.jpg"), TH * 1.0, (190, 235, 225), fade_left=0.30, fade_bottom=0, contrast=1.1)
    paste(cv, ph, TW + 20, 0, "rt")
    diamonds_pile(cv, X3 + 80, TH * 0.90, 18, 300, 4)
    cv = burn(cv, TW * 0.28, TH * 0.42, TW * 0.30, TH * 0.36, 0.7); cv = grade(cv)
    paste(cv, word("ANTWERP  ·  2003", 90, GOLD, track=12), X3, Y3 * 0.38, "cm")
    paste(cv, word("$100 MILLION", 300, GOLD, glow_col=(255, 210, 120)), X3 + 40, Y3 * 1.08, "cm")
    paste(cv, word("GONE", 330, CYAN, glow_col=CYAN), X3 - 140, Y3 * 1.95, "cm")
    return cv


def antwerp_2b():   # evidence bag over the still
    cv = dark_bg(7, (20, 18, 16), 0.33, 0.5)
    ph = faded_photo(os.path.join(A, "antwerp_cctv_style_still.jpg"), TH, (120, 150, 145), fade_left=0.10, fade_bottom=0, contrast=1.0, fade_right=0.35)
    paste(cv, ph, -80, 0, "lt", 0.55)
    bag = sandwich_bag(1150).rotate(-6, expand=True, resample=Image.BICUBIC); paste(cv, bag, X3 + 40, TH * 0.54, "cm")
    cv = burn(cv, TW * 0.78, TH * 0.42, TW * 0.24, TH * 0.4, 0.7); cv = grade(cv)
    paste(cv, word("THE", 220, WHT), TW * 0.78, Y3 * 0.62, "cm")
    paste(cv, word("$100M", 300, GOLD, glow_col=(255, 210, 120)), TW * 0.78, Y3 * 1.32, "cm")
    paste(cv, word("MISTAKE", 250, CYAN, glow_col=CYAN), TW * 0.75, Y3 * 2.05, "cm")
    return cv


def cohen_1b():   # famous face (real portrait) on the right third + the radio + statement
    cv = damascus_night(5)
    arr = np.asarray(cv, np.float32).copy(); arr *= 0.55; cv = Image.fromarray(arr.astype(np.uint8), "RGBA")
    face = faded_photo(os.path.join(A, "eli_cohen_portrait.jpg"), TH * 1.12, (226, 236, 226), fade_left=0.28, fade_bottom=0.15, crop=(0.0, 0.03, 1.0, 1.0), contrast=1.25)
    paste(cv, face, TW + 30, -40, "rt")
    gl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([TW * 0.55, TH * 0.1, TW * 1.05, TH * 1.1], fill=GREEN + (40,)); cv.alpha_composite(gl.filter(ImageFilter.GaussianBlur(160)))
    r = radio_set(820); paste(cv, r, X3 - 20, TH * 0.80, "cm")
    cv = burn(cv, TW * 0.28, TH * 0.36, TW * 0.30, TH * 0.32, 0.65); cv = grade(cv)
    paste(cv, word("DAMASCUS  ·  1965", 84, GOLD, track=12), X3, Y3 * 0.36, "cm")
    paste(cv, word("HIS RADIO", 220, WHT), X3, Y3 * 0.98, "cm")
    paste(cv, word("BETRAYED HIM", 190, GREEN, glow_col=GREEN), X3, Y3 * 1.62, "cm")
    return cv


def passport_photo(w):
    im = passport(w); h = im.size[1]
    ph = Image.open(os.path.join(A, "eli_cohen_portrait.jpg")).convert("L"); ph = ImageOps.autocontrast(ph, cutoff=1)
    pw, phh = int(w * 0.28), int(h * 0.56); ph = ImageOps.fit(ph, (pw, phh), Image.LANCZOS, centering=(0.5, 0.35)).convert("RGBA")
    im.alpha_composite(ph, (40, int(h * 0.24))); ImageDraw.Draw(im).rectangle([40, int(h * 0.24), 40 + pw, int(h * 0.24) + phh], outline=(60, 50, 40), width=4)
    st = word("ALIAS", int(w * 0.13), (200, 38, 30), track=12).rotate(-14, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(st, (int(w * 0.62), int(h * 0.66))); return im


def cohen_2b():
    cv = dark_bg(12, (24, 20, 16), 0.35, 0.5)
    p = passport_photo(1400).rotate(5, expand=True, resample=Image.BICUBIC); paste(cv, p, X3 + 30, TH * 0.52, "cm")
    cv = burn(cv, TW * 0.80, TH * 0.42, TW * 0.22, TH * 0.4, 0.6); cv = grade(cv)
    paste(cv, word("ISRAEL'S", 200, WHT), TW * 0.81, Y3 * 0.75, "cm")
    paste(cv, word("MAN IN", 200, WHT), TW * 0.81, Y3 * 1.35, "cm")
    paste(cv, word("DAMASCUS", 210, GREEN, glow_col=GREEN), TW * 0.79, Y3 * 1.98, "cm")
    return cv


def run_v2():
    for folder, items in (("ANTWERP", [("A1b_100M_GONE_PHOTO", antwerp_1b), ("A2b_100M_MISTAKE_PHOTO", antwerp_2b)]),
                          ("ELI_COHEN", [("E1b_RADIO_BETRAYED_HIM_PHOTO", cohen_1b), ("E2b_MAN_IN_DAMASCUS_PHOTO", cohen_2b)])):
        for nm, fn in items:
            fn().convert("RGB").resize((1280, 720), Image.LANCZOS).save(os.path.join(OUT, folder, f"THUMBNAIL_{nm}.png")); print(nm)
