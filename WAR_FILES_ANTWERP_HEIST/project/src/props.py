"""Procedurally rendered props (no stock or third-party imagery)."""
import math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *


# ───────────────────────── VAULT DOOR ─────────────────────────
@functools.lru_cache(None)
def vault_door(S=1600, tint=(1.0, 1.0, 1.0), seed=4):
    """Front view of a round vault door with frame, bolts and dial. Returns RGBA SxS."""
    y, x = np.mgrid[:S, :S].astype(np.float32)
    cx = cy = S / 2
    dx, dy = x - cx, y - cy
    r = np.sqrt(dx ** 2 + dy ** 2) / (S / 2)
    th = np.arctan2(dy, dx)
    light = -0.75 * np.pi  # light from top-left
    rng = np.random.default_rng(seed)
    brushed = smooth_noise(S, S, 6, seed, 2)
    grain = (brushed - 0.5) * 0.10
    base = np.full((S, S), 0.42, np.float32)
    # frame ring 0.80..1.0 with bevels
    ring = (r > 0.80) & (r <= 1.0)
    bevel_o = np.clip((1.0 - r) / 0.03, 0, 1); bevel_i = np.clip((r - 0.80) / 0.03, 0, 1)
    dirl = np.cos(th - light)
    v = 0.40 + 0.08 * np.sin(r * 160) * 0.2
    v = np.where(ring, 0.36 + 0.22 * dirl * (1 - bevel_o) - 0.18 * dirl * (1 - bevel_i), v)
    # gap ring 0.76..0.80 dark
    gap = (r > 0.765) & (r <= 0.80)
    v = np.where(gap, 0.06 + 0.04 * dirl, v)
    # door face <0.765: concentric machining rings
    face = r <= 0.765
    facev = 0.34 + 0.05 * np.sin(r * 420) + 0.06 * np.cos(th - light) * r + 0.10 * (1 - r)
    # raised inner disc 0..0.52 with bevel
    disc_b = (r > 0.50) & (r < 0.53)
    facev = np.where(disc_b, 0.30 + 0.25 * np.cos(th - light) * np.sign(0.515 - r + 1e-6), facev)
    facev = np.where(r < 0.50, 0.38 + 0.04 * np.sin(r * 700) + 0.05 * np.cos(th - light) * r, facev)
    # hub
    hub = r < 0.13
    facev = np.where(hub, 0.50 + 0.25 * np.cos(th - light) * (r / 0.13) ** 2, facev)
    hub_b = (r >= 0.13) & (r < 0.145)
    facev = np.where(hub_b, 0.12, facev)
    v = np.where(face, facev, v)
    v = v + grain
    col = np.stack([v * 255 * tint[0] * 0.96, v * 255 * tint[1] * 1.0, v * 255 * tint[2] * 1.05], -1)
    alpha = np.clip((1.0 - r) * S / 2, 0, 1) * 255
    img = np.dstack([np.clip(col, 0, 255), alpha]).astype(np.uint8)
    im = Image.fromarray(img, "RGBA")
    d = ImageDraw.Draw(im)
    # bolts on frame
    for i in range(28):
        a = i / 28 * 2 * np.pi
        bx, by = cx + math.cos(a) * S / 2 * 0.90, cy + math.sin(a) * S / 2 * 0.90
        br = S * 0.018
        d.ellipse([bx - br * 1.25, by - br * 1.25, bx + br * 1.25, by + br * 1.25], fill=(28, 30, 33, 255))
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=(120, 124, 128, 255))
        d.ellipse([bx - br * 0.7 - br * 0.25, by - br * 0.7 - br * 0.25, bx + br * 0.3, by + br * 0.3], fill=(170, 172, 175, 255))
    # locking bolts visible in gap (rectangular)
    for i in range(12):
        a = i / 12 * 2 * np.pi + 0.13
        p = [(cx + math.cos(a + s) * S / 2 * rr, cy + math.sin(a + s) * S / 2 * rr) for s, rr in [(-0.035, 0.74), (0.035, 0.74), (0.035, 0.81), (-0.035, 0.81)]]
        d.polygon(p, fill=(150, 152, 150, 255), outline=(40, 40, 40, 255))
    # dial ticks around hub
    for i in range(100):
        a = i / 100 * 2 * np.pi
        r0 = S / 2 * (0.155 if i % 10 else 0.150); r1 = S / 2 * 0.175
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], fill=(205, 205, 200, 255), width=2 if i % 10 else 4)
    d.ellipse([cx - S * 0.012, cy - S * 0.012, cx + S * 0.012, cy + S * 0.012], fill=(30, 30, 30, 255))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return im


def wheel(S, angle):
    """three/five-spoke handle wheel overlay, RGBA SxS, rotated."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2; R = S / 2 * 0.40
    for i in range(5):
        a = angle + i / 5 * 2 * math.pi
        x1, y1 = c + math.cos(a) * S / 2 * 0.19, c + math.sin(a) * S / 2 * 0.19
        x2, y2 = c + math.cos(a) * R, c + math.sin(a) * R
        d.line([(x1 + 4, y1 + 6), (x2 + 4, y2 + 6)], fill=(0, 0, 0, 120), width=int(S * 0.028))
        d.line([(x1, y1), (x2, y2)], fill=(150, 152, 154, 255), width=int(S * 0.026))
        d.line([(x1, y1 - 3), (x2, y2 - 3)], fill=(205, 205, 205, 255), width=int(S * 0.008))
        kr = S * 0.03
        d.ellipse([x2 - kr + 4, y2 - kr + 6, x2 + kr + 4, y2 + kr + 6], fill=(0, 0, 0, 120))
        d.ellipse([x2 - kr, y2 - kr, x2 + kr, y2 + kr], fill=(140, 142, 145, 255))
        d.ellipse([x2 - kr * 0.6, y2 - kr * 0.75, x2 + kr * 0.2, y2], fill=(215, 215, 215, 255))
    return im.filter(ImageFilter.GaussianBlur(0.7))


# ───────────────────────── DIAMOND ─────────────────────────
def diamond(size, phase=0.0, seed=0, rot=0.0, squash=1.0, warm=0.0):
    """Top-view brilliant-cut diamond sprite (RGBA). phase animates scintillation."""
    ss = 2; S = int(size * ss); c = S / 2; R = S / 2 * 0.96
    rng = random.Random(seed)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def P(r, a): return (c + math.cos(a + rot) * R * r, c + math.sin(a + rot) * R * r * squash)
    T = [P(0.52, i * math.pi / 4) for i in range(8)]
    Sx = [P(0.74, i * math.pi / 4 + math.pi / 8) for i in range(8)]
    G = [P(1.0, i * math.pi / 4) for i in range(8)]
    M = [P(1.0, i * math.pi / 4 + math.pi / 8) for i in range(8)]
    def shade(k, tier):
        base = {0: 0.35, 1: 0.55, 2: 0.45, 3: 0.40}[tier]
        s = 0.5 + 0.5 * math.sin(3.1 * k + phase * (1.3 + 0.4 * tier) + seed * 1.7 + rng.random() * 0.8)
        b = base * 0.8 + 0.75 * s ** 5
        fire = 0.55 * (0.5 + 0.5 * math.sin(phase * 0.9 + k * 2.3 + seed)) ** 24
        hue = (k * 0.137 + seed * 0.21 + phase * 0.05) % 1.0
        fr, fg, fb = colorsys_hsv(hue, 0.55, 1.0)
        rr = b * (1 - 0.6 * fire) + fire * fr * b; gg = b * (1 - 0.6 * fire) + fire * fg * b; bb = b * (1 - 0.6 * fire) + fire * fb * b
        tintb = 1.06 - 0.06 * warm
        col = (int(clamp(rr * (0.93 + 0.1 * warm)) * 255), int(clamp(gg * 0.98) * 255), int(clamp(bb * tintb) * 255), 255)
        return col
    edge = (40, 46, 58, 200)
    # pavilion reflections seen through table (arrows)
    tc = (c, c)
    for i in range(8):
        a, b = T[i], T[(i + 1) % 8]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        d.polygon([tc, a, mid], fill=shade(i * 2, 0)); d.polygon([tc, mid, b], fill=shade(i * 2 + 1, 3))
    for i in range(8):
        d.polygon([T[i], T[(i + 1) % 8], Sx[i]], fill=shade(i + 20, 1), outline=edge)
    for i in range(8):
        d.polygon([T[i], Sx[i - 1], G[i], Sx[i]], fill=shade(i + 40, 2), outline=edge)
    for i in range(8):
        d.polygon([Sx[i], G[i], M[i]], fill=shade(i + 60, 1), outline=edge)
        d.polygon([Sx[i], M[i], G[(i + 1) % 8]], fill=shade(i + 80, 2), outline=edge)
    d.polygon(T, outline=(200, 210, 225, 160))
    gp = [P(1.0, i * math.pi / 32) for i in range(64)]
    d.polygon(gp, outline=(210, 215, 225, 220))
    im = im.resize((int(size), int(size)), Image.LANCZOS)
    return im


def colorsys_hsv(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h, s, v)


@functools.lru_cache(None)
def glint_sprite(size):
    S = int(size); c = S / 2
    y, x = np.mgrid[:S, :S].astype(np.float32)
    dx, dy = np.abs(x - c) / c, np.abs(y - c) / c
    core = np.exp(-(dx ** 2 + dy ** 2) * 40)
    rays = np.exp(-dy * 60) * np.clip(1 - dx, 0, 1) ** 2 + np.exp(-dx * 60) * np.clip(1 - dy, 0, 1) ** 2
    diag = np.exp(-np.abs(dx - dy) * 50) * np.clip(1 - (dx + dy) / 1.4, 0, 1) ** 3 * 0.35
    a = np.clip(core + rays * 0.8 + diag, 0, 1)
    im = np.zeros((S, S, 4), np.uint8); im[..., 0] = 255; im[..., 1] = 250; im[..., 2] = 240; im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im, "RGBA")


# ───────────────────────── SAFE-DEPOSIT BOXES ─────────────────────────
@functools.lru_cache(None)
def box_closed(w, h, num, seed=0):
    rng = np.random.default_rng(seed)
    g = np.linspace(0.62, 0.40, h)[:, None] * np.ones((1, w))
    g = g + (smooth_noise(w, h, 4, seed, 1) - 0.5) * 0.06
    arr = np.dstack([g * 168, g * 172, g * 178, np.full((h, w), 255)]).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(25, 25, 28, 255), width=3)
    d.line([(3, 3), (w - 4, 3)], fill=(215, 215, 215, 255), width=2); d.line([(3, 3), (3, h - 4)], fill=(200, 200, 200, 255), width=2)
    d.line([(4, h - 4), (w - 4, h - 4)], fill=(60, 60, 62, 255), width=2)
    for kx in (w * 0.36, w * 0.64):
        ky = h * 0.55; r = h * 0.11
        d.ellipse([kx - r * 1.5, ky - r * 1.5, kx + r * 1.5, ky + r * 1.5], fill=(185, 160, 95, 255), outline=(80, 66, 30, 255))
        d.ellipse([kx - r * 0.5, ky - r * 0.7, kx + r * 0.5, ky + r * 0.1], fill=(12, 12, 12, 255))
        d.rectangle([kx - r * 0.18, ky - r * 0.2, kx + r * 0.18, ky + r * 0.8], fill=(12, 12, 12, 255))
    pw = w * 0.22; d.rectangle([w / 2 - pw / 2, h * 0.12, w / 2 + pw / 2, h * 0.30], fill=(200, 180, 120, 255), outline=(90, 75, 40, 255))
    d.text((w / 2, h * 0.21), str(num), font=font(F_OSW_B, max(8, int(h * 0.14))), fill=(40, 30, 10, 255), anchor="mm")
    return im


@functools.lru_cache(None)
def box_open(w, h, num, seed=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(12):
        f = i / 12
        c = int(8 + 22 * f)
        d.rectangle([int(w * 0.5 * f * 0.25), int(h * 0.5 * f * 0.25), int(w - w * 0.5 * f * 0.25), int(h - h * 0.5 * f * 0.25)], fill=(c, c, c + 2, 255))
    d.rectangle([0, 0, w - 1, h - 1], outline=(30, 30, 32, 255), width=4)
    rng = random.Random(seed)
    # door hanging open from left hinge (seen edge-on), sometimes bent
    dw = int(w * rng.uniform(0.22, 0.34)); sk = int(h * rng.uniform(0.04, 0.16))
    poly = [(-dw, sk), (2, 0), (2, h), (-dw, h - sk * 0.4)]
    door = Image.new("RGBA", (w + dw, h), (0, 0, 0, 0)); dd = ImageDraw.Draw(door)
    dd.polygon([(p[0] + dw, p[1]) for p in poly], fill=(132, 136, 142, 255), outline=(35, 35, 38, 255))
    dd.line([(dw, 0), (dw, h)], fill=(210, 210, 210, 255), width=2)
    return im, door, dw


# ───────────────────────── KEY ─────────────────────────
@functools.lru_cache(None)
def big_key(L=1500):
    H_ = int(L * 0.32); ss = 2
    im = Image.new("RGBA", (L * ss, H_ * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cy = H_ * ss / 2; s = ss
    # bow
    bx, br = 190 * s, 150 * s
    d.ellipse([bx - br, cy - br, bx + br, cy + br], fill=(150, 150, 150, 255))
    d.ellipse([bx - br * 0.55, cy - br * 0.55, bx + br * 0.55, cy + br * 0.55], fill=(0, 0, 0, 0))
    for i in range(6):
        a = i / 6 * 2 * math.pi
        d.ellipse([bx + math.cos(a) * br * 0.78 - 20 * s, cy + math.sin(a) * br * 0.78 - 20 * s, bx + math.cos(a) * br * 0.78 + 20 * s, cy + math.sin(a) * br * 0.78 + 20 * s], fill=(0, 0, 0, 0))
    # collar + shaft
    d.rectangle([bx + br * 0.9, cy - 34 * s, bx + br * 0.9 + 70 * s, cy + 34 * s], fill=(150, 150, 150, 255))
    d.rectangle([bx + br, cy - 20 * s, (L - 60) * s, cy + 20 * s], fill=(150, 150, 150, 255))
    # bit with wards
    x0 = (L - 300) * s
    d.rectangle([x0, cy + 10 * s, (L - 60) * s, cy + 150 * s], fill=(150, 150, 150, 255))
    for i, (a, b, dep) in enumerate([(20, 55, 60), (85, 110, 95), (140, 170, 40), (195, 225, 110)]):
        d.rectangle([x0 + a * s, cy + (150 - dep) * s, x0 + b * s, cy + 152 * s], fill=(0, 0, 0, 0))
    arr = np.asarray(im).astype(np.float32)
    hh, ww = arr.shape[:2]
    yy = np.linspace(0, 1, hh)[:, None]
    shade = 0.55 + 0.6 * np.exp(-((yy - 0.42) / 0.08) ** 2) - 0.25 * yy
    n = smooth_noise(ww, hh, 8, 5, 2)
    col = np.array([1.0, 0.86, 0.6])  # aged brass
    rgb = (arr[..., :1] / 150) * shade[..., None] * (0.85 + 0.3 * n[..., None]) * col * 200
    arr[..., :3] = np.clip(rgb, 0, 255)
    im = Image.fromarray(arr.astype(np.uint8), "RGBA").resize((L, H_), Image.LANCZOS)
    return im


# ───────────────────────── TREES (winter) ─────────────────────────
def draw_tree(d, x, y, h, rng, col, width):
    def br(x, y, ang, ln, w, depth):
        if depth == 0 or ln < 4: return
        x2 = x + math.cos(ang) * ln; y2 = y - math.sin(ang) * ln
        d.line([(x, y), (x2, y2)], fill=col, width=max(1, int(w)))
        n = 2 if depth > 2 else rng.choice([1, 2, 2, 3])
        for _ in range(n):
            br(x2, y2, ang + rng.uniform(-0.75, 0.75), ln * rng.uniform(0.62, 0.8), w * 0.68, depth - 1)
    # trunk
    d.polygon([(x - width / 2, y), (x + width / 2, y), (x + width * 0.18, y - h * 0.62), (x - width * 0.18, y - h * 0.62)], fill=col)
    for i in range(rng.randint(4, 7)):
        yy = y - h * rng.uniform(0.35, 0.62)
        br(x, yy, math.pi / 2 + rng.uniform(-1.1, 1.1), h * rng.uniform(0.18, 0.3), width * 0.35, 6)
    br(x, y - h * 0.6, math.pi / 2 + rng.uniform(-0.2, 0.2), h * 0.32, width * 0.3, 7)


def forest_layer(w, h, seed, n, hmin, hmax, ground, col, wmin, wmax):
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        x = rng.uniform(-50, w + 50); th = rng.uniform(hmin, hmax)
        draw_tree(d, x, ground + rng.uniform(-8, 8), th, rng, col, rng.uniform(wmin, wmax))
    d.rectangle([0, ground, w, h], fill=col)
    return im


# ───────────────────────── SKYLINE ─────────────────────────
def skyline(w, h, seed, base_y, col, win_col=None, win_p=0.0, spire_x=None, scale=1.0, hmin=80, hmax=260):
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = -20
    while x < w + 20:
        bw = rng.uniform(60, 170) * scale; bh = rng.uniform(hmin, hmax) * scale
        top = base_y - bh
        d.rectangle([x, top, x + bw, h], fill=col)
        if rng.random() < 0.45:  # gabled roof (Flemish style)
            if rng.random() < 0.5:
                d.polygon([(x, top), (x + bw / 2, top - bw * 0.45), (x + bw, top)], fill=col)
            else:  # stepped gable
                steps = 4; sw = bw / (2 * steps)
                for s in range(steps):
                    d.rectangle([x + s * sw, top - (s + 1) * bw * 0.09, x + bw - s * sw, top], fill=col)
        if win_col and win_p > 0:
            for wy in np.arange(top + 14 * scale, base_y + 200, 24 * scale):
                for wx in np.arange(x + 10 * scale, x + bw - 14 * scale, 20 * scale):
                    if rng.random() < win_p:
                        a = rng.randint(120, 255)
                        d.rectangle([wx, wy, wx + 7 * scale, wy + 11 * scale], fill=win_col + (a,))
        x += bw + rng.uniform(-10, 6)
    if spire_x is not None:  # Gothic cathedral tower silhouette
        s = scale; cx = spire_x
        tiers = [(90, 260), (74, 150), (60, 110), (48, 90), (34, 70)]
        y = base_y
        for tw, th in tiers:
            d.rectangle([cx - tw * s / 2, y - th * s, cx + tw * s / 2, h], fill=col)
            for k in (-1, 1):  # pinnacles
                d.polygon([(cx + k * tw * s / 2 - 5 * s, y - th * s), (cx + k * tw * s / 2, y - th * s - 34 * s), (cx + k * tw * s / 2 + 5 * s, y - th * s)], fill=col)
            y -= th * s
        d.polygon([(cx - 18 * s, y), (cx, y - 170 * s), (cx + 18 * s, y)], fill=col)
        d.line([(cx, y - 170 * s), (cx, y - 200 * s)], fill=col, width=max(1, int(3 * s)))
        if win_col:
            for k in range(3):
                d.rectangle([cx - 6 * s, base_y - 120 * s - k * 140 * s, cx + 6 * s, base_y - 90 * s - k * 140 * s], fill=win_col + (90,))
    return im
