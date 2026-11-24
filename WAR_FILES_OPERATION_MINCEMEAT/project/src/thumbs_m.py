"""Three thumbnail concepts, rendered at 2560x1440 and exported at 1280x720. Original illustration only."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import common
from common import font, text_img, glow, paste, radial, vignette, smooth_noise, F_BEBAS, F_OSW_B, F_TYPE, GOLD, WHITE
TW, TH = 2560, 1440
OUT = os.path.join(os.path.dirname(__file__), "..", "..")


def sea_scene(variant, horizon=0.56, sun=(0.70, 0.50)):
    # simple high-res painterly sea: gradient sky + banded water + sun path
    yh = int(TH * horizon); img = np.zeros((TH, TW, 3), np.float32)
    if variant == "dawn":
        top, hor, wat1, wat2, sc = (32, 46, 82), (238, 150, 96), (40, 44, 64), (10, 14, 24), (255, 214, 150)
    else:
        top, hor, wat1, wat2, sc = (4, 7, 16), (30, 40, 66), (22, 30, 48), (4, 6, 12), (220, 228, 240)
    g = np.linspace(0, 1, yh)[:, None, None] ** 1.5
    img[:yh] = np.array(top) * (1 - g) + np.array(hor) * g
    gw = np.linspace(0, 1, TH - yh)[:, None, None] ** 0.8
    img[yh:] = np.array(wat1) * (1 - gw) + np.array(wat2) * gw
    sx, sy = sun[0] * TW, sun[1] * TH
    yy, xx = np.mgrid[:TH, :TW]
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    img += (np.exp(-d / 520) * 120)[..., None] * (np.array(sc) / 255) * (yy < yh)[..., None]
    img += (np.clip(1 - d / 70, 0, 1) ** 0.5 * 255)[..., None] * (np.array(sc) / 255) * (yy < yh)[..., None]
    # sun path glitter on water
    n = smooth_noise(TW, TH, 6, 3, 2)
    depth = np.clip((yy - yh) / (TH - yh), 0, 1)
    col = np.exp(-((xx - sx) / (60 + 700 * depth)) ** 2) * (yy >= yh)
    fine = smooth_noise(TW, TH, 3, 9, 2)
    rip = np.clip((fine - 0.45) * 3, 0, 1)
    img += (col * rip ** 2 * 200)[..., None] * (np.array(sc) / 255)
    img += ((smooth_noise(TW, TH, 18, 4, 3) - 0.5)[..., None] * 26) * (yy >= yh)[..., None]
    if variant == "dawn":
        cl = np.clip((smooth_noise(TW, yh, 300, 7, 4) - 0.5) * 2.5, 0, 1)
        img[:yh] = img[:yh] * (1 - 0.55 * cl[..., None]) + np.array((250, 170, 130)) * 0.55 * cl[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA"), yh


def officer(h, rim=(255, 170, 110), side=1, case=True):
    w = int(h * 0.62); m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); c = w * 0.45; s = h
    # peaked cap
    d.ellipse([c - 0.058 * s, 0.035 * s, c + 0.058 * s, 0.075 * s], fill=255)
    d.polygon([(c - 0.06 * s, 0.07 * s), (c + 0.075 * s, 0.07 * s), (c + 0.09 * s, 0.085 * s), (c - 0.05 * s, 0.085 * s)], fill=255)
    d.ellipse([c - 0.045 * s, 0.06 * s, c + 0.045 * s, 0.155 * s], fill=255)  # head
    d.polygon([(c - 0.03 * s, 0.14 * s), (c + 0.03 * s, 0.14 * s), (c + 0.035 * s, 0.18 * s), (c - 0.035 * s, 0.18 * s)], fill=255)
    coat = [(c - 0.07, 0.17), (c + 0.07, 0.17), (c + 0.15, 0.205), (c + 0.165, 0.30), (c + 0.17, 0.56), (c + 0.15, 0.58), (c + 0.18, 0.86),
            (c + 0.06, 0.88), (c + 0.05, 1.0), (c - 0.05, 1.0), (c - 0.06, 0.88), (c - 0.18, 0.86), (c - 0.15, 0.58), (c - 0.17, 0.56), (c - 0.165, 0.30), (c - 0.15, 0.205)]
    d.polygon([((cx - c) * s + c, cy * s) for cx, cy in coat], fill=255)
    # collar points
    for k in (-1, 1): d.polygon([(c + k * 0.07 * s, 0.17 * s), (c + k * 0.05 * s, 0.13 * s), (c + k * 0.015 * s, 0.2 * s)], fill=255)
    if case:  # briefcase in right hand, chain implied
        bx = c + 0.13 * s; by = 0.60 * s
        d.rounded_rectangle([bx, by, bx + 0.17 * s, by + 0.11 * s], int(0.01 * s), fill=255)
        d.rounded_rectangle([bx + 0.06 * s, by - 0.025 * s, bx + 0.11 * s, by + 0.005 * s], int(0.008 * s), outline=255, width=int(0.008 * s))
    m = m.filter(ImageFilter.GaussianBlur(1.5)); ma = np.asarray(m, np.float32) / 255
    sh = np.roll(ma, -side * int(h * 0.007), axis=1); rimm = np.clip(ma - sh, 0, 1)
    rimm = np.asarray(Image.fromarray((rimm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(h * 0.003)), np.float32) / 255
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = np.array([7, 7, 9]) + rimm[..., None] * np.array(rim) * 1.7; out[..., 3] = np.maximum(ma, rimm) * 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def headline(cv, lines, y, sizes, cols, cx=TW / 2, anchor="cm"):
    for ln, sz, col in zip(lines, sizes, cols):
        f = font(F_BEBAS, sz); ti = text_img(ln, f, col, tracking=int(sz * 0.04))
        a = ti.getchannel("A"); blk = Image.new("RGBA", ti.size, (0, 0, 0, 255)); blk.putalpha(a)
        shd = Image.new("RGBA", (ti.size[0] + 120, ti.size[1] + 120), (0, 0, 0, 0)); shd.alpha_composite(blk, (60, 72)); shd = shd.filter(ImageFilter.GaussianBlur(sz * 0.07))
        paste(cv, shd, cx, y + 12, anchor, 0.95); paste(cv, ti, cx, y, anchor); y += int(sz * 0.98)
    return y


def grade(cv, red=0.0):
    arr = np.asarray(cv.convert("RGB"), np.float32)
    arr *= vignette(TW, TH, 0.55)[..., None]
    if red: arr += radial(TW, TH, TW * 0.1, TH * 0.5, TW * 0.6)[..., None] ** 1.5 * np.array([90, 10, 6]) * red
    arr = (arr - 128) * 1.08 + 128
    arr += np.random.default_rng(2).normal(0, 6, arr.shape[:2])[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


def europe_ghost(w, h):
    from scenes_m import countries
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx, cy, s = 10, 49, w / 40; cosl = math.cos(math.radians(49))
    for nm, polys in countries().items():
        for p in polys:
            xs = w / 2 + (p[:, 0] - cx) * cosl * s; ys = h / 2 - (p[:, 1] - cy) * s
            if len(xs) > 2: d.polygon(list(zip(xs.tolist(), ys.tolist())), fill=(150, 20, 16, 150) if nm == "Germany" else (40, 40, 48, 70), outline=(90, 90, 100, 90))
    return im.filter(ImageFilter.GaussianBlur(3))


def concept_A():  # the officer on the shore at dawn
    cv, yh = sea_scene("dawn", 0.58, (0.74, 0.52))
    g = europe_ghost(1500, 900); paste(cv, g, TW * 0.78, TH * 0.28, "cm", 0.45)
    fig = officer(1380, side=-1); paste(cv, fig, TW * 0.26, TH * 1.02, "cb")
    cv = grade(cv, red=0.25)
    y = headline(cv, ["HE WAS", "ALREADY DEAD"], TH * 0.22, [300, 300], [WHITE, (232, 52, 40)], cx=TW * 0.66)
    paste(cv, text_img("1943  ·  TOP SECRET", font(F_OSW_B, 64), GOLD, tracking=14), TW * 0.66, y + 40, "cm")
    return cv


def concept_B():  # the briefcase on wet sand
    cv, yh = sea_scene("dawn", 0.34, (0.5, 0.30))
    arr = np.asarray(cv, np.float32).copy(); yy = np.arange(TH)[:, None]
    sand = (yy > TH * 0.55); n = smooth_noise(TW, TH, 5, 11, 2)
    arr[..., :3] = np.where(sand[..., None], np.array([150, 120, 96]) * (0.6 + 0.5 * n[..., None]) * (0.7 + 0.5 * (yy / TH))[..., None], arr[..., :3])
    cv = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"); d = ImageDraw.Draw(cv, "RGBA")
    for k in range(5):  # foam line
        y = TH * 0.55 + k * 10; d.line([(0, y), (TW, y + 30 * math.sin(k))], fill=(240, 240, 236, 90 - k * 15), width=14)
    S = 1150; bx, by = TW * 0.55 - S / 2, TH * 0.66
    case = Image.new("RGBA", (S + 200, int(S * 0.75)), (0, 0, 0, 0)); cd = ImageDraw.Draw(case)
    cd.rounded_rectangle([120, 140, 120 + S, 140 + S * 0.55], 50, fill=(0, 0, 0, 170)); case = case.filter(ImageFilter.GaussianBlur(26)); cd = ImageDraw.Draw(case)
    cd.rounded_rectangle([90, 100, 90 + S, 100 + S * 0.55], 46, fill=(56, 36, 22)); cd.rectangle([90, 190, 90 + S, 206], fill=(40, 26, 16))
    for cx in (90 + S * 0.28, 90 + S * 0.72): cd.rectangle([cx - 34, 180, cx + 34, 228], fill=(186, 160, 100))
    case = case.rotate(-8, expand=True, resample=Image.BICUBIC)
    # document sliding out
    doc = Image.new("RGBA", (760, 520), (230, 222, 196, 255)); dd = ImageDraw.Draw(doc); dd.text((380, 110), "MOST SECRET", font=font(F_TYPE, 84), fill=(150, 30, 24), anchor="mm")
    for i in range(7): dd.line([(80, 200 + i * 40), (680 - (i % 3) * 90, 200 + i * 40)], fill=(110, 100, 90), width=6)
    paste(cv, doc.rotate(10, expand=True, resample=Image.BICUBIC), TW * 0.33, TH * 0.70, "cm")
    paste(cv, case, TW * 0.58, TH * 0.78, "cm")
    for k in range(30):  # chain
        x = TW * 0.40 - k * 34; y = TH * 0.66 + 18 * math.sin(k * 0.5) - k * 4
        d = ImageDraw.Draw(cv, "RGBA"); d.ellipse([x - 18, y - 11, x + 18, y + 11], outline=(150, 120, 80, 255), width=7)
    cv = grade(cv)
    headline(cv, ["HE WAS ALREADY DEAD"], TH * 0.15, [250], [WHITE])
    return cv


def concept_C():  # the submarine at night
    cv, yh = sea_scene("night", 0.55, (0.80, 0.18))
    from world import submarine_sprite
    sub = submarine_sprite(2000, (5, 6, 9)); paste(cv, sub, TW * 0.52, yh + 120, "cb")
    d = ImageDraw.Draw(cv, "RGBA")
    for k in range(3):
        px = TW * 0.50 + k * 34; py = yh + 120 - 2000 * 0.32 * 0.22 - 4
        d.ellipse([px - 14, py - 110, px + 14, py - 82], fill=(5, 6, 9, 255)); d.rectangle([px - 20, py - 86, px + 20, py], fill=(5, 6, 9, 255))
    cv = grade(cv)
    headline(cv, ["HE WAS", "ALREADY DEAD"], TH * 0.18, [270, 270], [WHITE, (232, 52, 40)], cx=TW * 0.30)
    return cv


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "thumbnails"), exist_ok=True)
    for nm, fn in (("A", concept_A), ("B", concept_B), ("C", concept_C)):
        im = fn().convert("RGB").resize((1280, 720), Image.LANCZOS)
        im.save(os.path.join(OUT, "thumbnails", f"THUMBNAIL_{nm}.png")); print(nm)
