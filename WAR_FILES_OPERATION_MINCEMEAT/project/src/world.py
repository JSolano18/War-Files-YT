"""Environment renderers for Operation Mincemeat: sea, sky, coast, ships, London, valleys, interiors."""
import math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *

# ───────────────────────── palettes ─────────────────────────
SKY = {  # top, horizon, sea_deep, sea_sky, light(color), light_pos(x,y frac) , stars, light_size
    "night":    ((4, 7, 14), (22, 32, 52), (6, 10, 18), (30, 44, 66), (210, 220, 235), (0.70, 0.18), True, 26),
    "predawn":  ((10, 14, 30), (64, 70, 98), (10, 14, 24), (60, 70, 96), (200, 190, 200), (0.30, 0.40), True, 0),
    "dawn":     ((60, 90, 140), (236, 180, 130), (24, 44, 66), (190, 160, 140), (255, 225, 170), (0.62, 0.43), False, 46),
    "day":      ((70, 130, 200), (190, 214, 232), (22, 70, 105), (140, 180, 210), (255, 250, 235), (0.80, 0.10), False, 40),
    "overcast": ((92, 100, 112), (172, 176, 180), (40, 52, 60), (120, 128, 134), (230, 230, 230), (0.5, 0.2), False, 0),
    "dusk":     ((40, 46, 80), (214, 120, 90), (20, 24, 40), (150, 96, 92), (255, 170, 120), (0.30, 0.44), False, 54),
}
HOR = {"night": 0.50, "predawn": 0.50, "dawn": 0.47, "day": 0.45, "overcast": 0.46, "dusk": 0.48}


@functools.lru_cache(None)
def sky_plate(variant, w=W, h=H, seed=3):
    top, hor, _, _, lc, lp, stars, ls = SKY[variant]
    yh = int(h * HOR[variant])
    g = np.linspace(0, 1, yh)[:, None] ** 1.6
    sky = np.array(top)[None, None] * (1 - g[..., None]) + np.array(hor)[None, None] * g[..., None]
    sky = np.repeat(sky, w, axis=1).astype(np.float32)
    rng = np.random.default_rng(seed)
    if stars:
        for _ in range(500):
            x, y = rng.integers(0, w), rng.integers(0, int(yh * 0.85)); sky[y, x] += rng.uniform(40, 170) * (1 - y / yh)
    lx, ly = lp[0] * w, lp[1] * h
    if ls:
        yy, xx = np.mgrid[:yh, :w]
        d = np.sqrt((xx - lx) ** 2 + (yy - ly) ** 2)
        sky += (np.clip(1 - d / ls, 0, 1) ** 0.6 * 255)[..., None] * (np.array(lc) / 255)[None, None] * 0.95
        sky += (np.exp(-d / (ls * 9)) * 90)[..., None] * (np.array(lc) / 255)[None, None]
    if variant in ("overcast", "dawn", "dusk", "day"):
        n = smooth_noise(w, yh, 160, seed + 1, 4)
        cl = np.clip((n - (0.45 if variant != "overcast" else 0.25)) * 2.2, 0, 1)
        cc = {"overcast": (150, 154, 160), "dawn": (240, 170, 140), "dusk": (120, 70, 80), "day": (245, 248, 252)}[variant]
        sky = sky * (1 - cl[..., None] * 0.7) + np.array(cc) * cl[..., None] * 0.7
    return sky.clip(0, 255).astype(np.float32)


class Sea:
    """Analytic wave field rendered at half resolution."""
    def __init__(self, variant, seed=1, calm=1.0):
        self.v = variant; top, hor, deep, skyc, lc, lp, stars, ls = SKY[variant]
        self.deep, self.skyc, self.lc, self.lx = np.array(deep, np.float32), np.array(skyc, np.float32), np.array(lc, np.float32), lp[0]
        self.hw, self.hh = W // 2, H // 2
        self.yh = int(self.hh * HOR[variant])
        rows = self.hh - self.yh
        yy = np.arange(1, rows + 1, dtype=np.float32)[:, None]
        self.z = 60.0 / yy  # depth
        xx = (np.arange(self.hw, dtype=np.float32)[None, :] - self.hw / 2) / (self.hw / 2)
        self.X = xx * self.z * 1.2
        rng = random.Random(seed)
        self.waves = [(rng.uniform(0.6, 1.4) * (1.8 ** -i) * calm, rng.uniform(-0.6, 0.6), rng.uniform(1.2, 2.0) * (1.6 ** i), rng.uniform(0, 6.28)) for i in range(6)]
        self.fres = np.clip(1 - yy / rows, 0, 1) ** 2.2  # far rows reflect more sky
        self.colmask = np.exp(-((np.arange(self.hw)[None, :] / self.hw - self.lx) / (0.035 + 0.25 * (yy / rows))) ** 2)
    def render(self, t):
        X, Z = self.X, self.z
        h = np.zeros_like(X); dz = np.zeros_like(X); dx = np.zeros_like(X)
        for a, ang, k, ph in self.waves:
            kx, kz = k * math.sin(ang), k * math.cos(ang)
            arg = kx * X + kz * Z - (1.1 * math.sqrt(k)) * t + ph
            s = np.sin(arg); c = np.cos(arg)
            h += a * s; dz += a * kz * c; dx += a * kx * c
        att = 1 / (1 + Z * 0.02)
        facing = np.clip(dz * att * 0.35, -1, 1)
        col = self.deep * (1 - self.fres[..., None]) + self.skyc * self.fres[..., None]
        col = col * (0.78 + 0.35 * facing[..., None])
        glint = np.clip(facing * 1.3 + np.abs(dx) * -0.08 - 0.15, 0, 1) ** 3 * self.colmask
        near = 0.25 + 0.75 * self.fres[..., None] ** 0.35          # weaker sparkle close to camera
        col = col + np.minimum(glint[..., None] * near * self.lc * (1.1 if self.v in ("night", "dawn", "dusk", "day") else 0.35), 150)
        return col


def coast_layer(variant, side="left", lights=False, seed=5):
    yh = int(H * HOR[variant]); im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rng = random.Random(seed)
    base = {"night": (8, 10, 16), "predawn": (30, 32, 44), "dawn": (92, 84, 92), "day": (120, 140, 130), "overcast": (110, 116, 118), "dusk": (60, 46, 60)}[variant]
    x0, x1 = (0, W * 0.62) if side == "left" else (W * 0.38, W)
    pts = [(x0, yh + 2)]
    for i in range(41):
        x = x0 + (x1 - x0) * i / 40
        taper = math.sin(math.pi * min(1, (i / 40) * 1.25)) if side == "left" else math.sin(math.pi * max(0, (i / 40) * 1.25 - 0.25))
        hh = (8 + 26 * abs(math.sin(i * 0.37 + seed)) + rng.uniform(0, 6)) * max(0.15, taper)
        pts.append((x, yh - hh))
    pts.append((x1, yh + 2))
    d.polygon(pts, fill=base + (255,))
    if lights:
        for i in range(28):
            x = rng.uniform(x0 + 40, x1 - 60); d.ellipse([x, yh - 5 - rng.uniform(0, 6), x + 3, yh - 2], fill=(255, 205, 140, rng.randint(120, 230)))
    return im


def submarine_sprite(L=900, sil=(8, 10, 14)):
    Hs = int(L * 0.32); im = Image.new("RGBA", (L, Hs), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    wl = Hs * 0.78
    d.polygon([(0, wl), (L * 0.06, wl - L * 0.025), (L * 0.94, wl - L * 0.022), (L, wl - L * 0.006), (L * 0.97, wl + 6), (L * 0.03, wl + 6)], fill=sil + (255,))
    # conning tower (S-class)
    tx = L * 0.44
    d.polygon([(tx - L * 0.06, wl - L * 0.02), (tx - L * 0.045, wl - L * 0.10), (tx + L * 0.055, wl - L * 0.10), (tx + L * 0.075, wl - L * 0.02)], fill=sil + (255,))
    d.rectangle([tx - L * 0.008, wl - L * 0.16, tx + L * 0.002, wl - L * 0.10], fill=sil + (255,))  # periscope standards
    d.rectangle([tx + L * 0.015, wl - L * 0.14, tx + L * 0.022, wl - L * 0.10], fill=sil + (255,))
    # deck gun
    d.rectangle([tx - L * 0.13, wl - L * 0.045, tx - L * 0.11, wl - L * 0.02], fill=sil + (255,))
    d.line([(tx - L * 0.12, wl - L * 0.04), (tx - L * 0.20, wl - L * 0.05)], fill=sil + (255,), width=max(2, int(L * 0.006)))
    # jumping wire
    d.line([(L * 0.02, wl - L * 0.02), (tx, wl - L * 0.16), (L * 0.985, wl - L * 0.012)], fill=sil + (200,), width=max(1, int(L * 0.0016)))
    return im


def boat_sprite(L=260, sil=(30, 26, 30)):
    Hs = int(L * 0.9); im = Image.new("RGBA", (L, Hs), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    wl = Hs * 0.86
    d.polygon([(0, wl - L * 0.13), (L, wl - L * 0.16), (L * 0.86, wl), (L * 0.1, wl)], fill=sil + (255,))
    d.line([(L * 0.5, wl - L * 0.14), (L * 0.52, wl - L * 0.8)], fill=sil + (255,), width=max(2, int(L * 0.018)))
    d.polygon([(L * 0.53, wl - L * 0.75), (L * 0.53, wl - L * 0.22), (L * 0.86, wl - L * 0.24)], fill=sil + (230,))
    d.ellipse([L * 0.28, wl - L * 0.32, L * 0.34, wl - L * 0.25], fill=sil + (255,))
    d.rectangle([L * 0.285, wl - L * 0.26, L * 0.335, wl - L * 0.14], fill=sil + (255,))
    return im


def plane_sprite(L=220, sil=(40, 44, 50)):
    im = Image.new("RGBA", (L, int(L * 0.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = L * 0.25
    d.polygon([(0, c), (L * 0.95, c - L * 0.02), (L, c + L * 0.01), (L * 0.05, c + L * 0.035)], fill=sil + (255,))
    d.polygon([(L * 0.4, c), (L * 0.55, c - L * 0.0), (L * 0.6, c + L * 0.16), (L * 0.48, c + L * 0.16)], fill=sil + (255,))
    d.polygon([(L * 0.08, c), (L * 0.14, c - L * 0.08), (L * 0.17, c), ], fill=sil + (255,))
    for ex in (0.42, 0.56): d.ellipse([L * ex, c + L * 0.03, L * (ex + 0.06), c + L * 0.07], fill=sil + (255,))
    return im


def ship_sprite(L, kind, sil):
    Hs = int(L * 0.4); im = Image.new("RGBA", (L, Hs), (0, 0, 0, 0)); d = ImageDraw.Draw(im); wl = Hs * 0.9
    if kind == "lst":
        d.polygon([(0, wl - L * 0.07), (L, wl - L * 0.07), (L * 0.97, wl), (L * 0.02, wl)], fill=sil)
        d.rectangle([L * 0.78, wl - L * 0.16, L * 0.92, wl - L * 0.07], fill=sil); d.rectangle([L * 0.84, wl - L * 0.22, L * 0.86, wl - L * 0.16], fill=sil)
    elif kind == "destroyer":
        d.polygon([(0, wl - L * 0.04), (L * 0.15, wl - L * 0.06), (L, wl - L * 0.05), (L * 0.95, wl), (L * 0.04, wl)], fill=sil)
        d.rectangle([L * 0.3, wl - L * 0.12, L * 0.42, wl - L * 0.05], fill=sil); d.rectangle([L * 0.5, wl - L * 0.14, L * 0.54, wl - L * 0.05], fill=sil)
        d.line([(L * 0.36, wl - L * 0.12), (L * 0.36, wl - L * 0.25)], fill=sil, width=max(1, L // 120))
    else:  # transport / liner
        d.polygon([(0, wl - L * 0.08), (L, wl - L * 0.1), (L * 0.95, wl), (L * 0.03, wl)], fill=sil)
        d.rectangle([L * 0.35, wl - L * 0.18, L * 0.7, wl - L * 0.08], fill=sil); d.rectangle([L * 0.5, wl - L * 0.27, L * 0.56, wl - L * 0.18], fill=sil)
    return im


def landing_craft(L, sil):
    im = Image.new("RGBA", (L, int(L * 0.45)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); wl = L * 0.4
    d.polygon([(0, wl - L * 0.16), (L * 0.85, wl - L * 0.2), (L, wl - L * 0.08), (L * 0.96, wl), (L * 0.04, wl)], fill=sil)
    for i in range(6): d.ellipse([L * (0.2 + i * 0.1), wl - L * 0.27, L * (0.25 + i * 0.1), wl - L * 0.2], fill=sil)
    return im


# ───────────────────────── LONDON 1943 ─────────────────────────
@functools.lru_cache(None)
def london_layers(variant):
    night = variant.startswith("night"); rng = random.Random(11)
    PW = W + 400
    sky = np.zeros((H, PW, 3), np.float32); g = np.linspace(0, 1, H)[:, None]
    top, bot = ((6, 8, 14), (30, 34, 44)) if night else ((120, 126, 134), (182, 184, 184))
    sky[:] = (np.array(top) + (np.array(bot) - np.array(top)) * g)[:, None, :]
    if not night:
        n = smooth_noise(PW, H, 200, 4, 3); sky = sky * (0.9 + 0.2 * n[..., None])
    sky = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert("RGBA")
    # barrage balloons
    bl = Image.new("RGBA", (PW, H), (0, 0, 0, 0)); d = ImageDraw.Draw(bl)
    bc = (30, 32, 40, 255) if night else (90, 94, 102, 255)
    for i in range(5):
        x, y, s = rng.uniform(100, PW - 100), rng.uniform(80, 340), rng.uniform(40, 80)
        d.ellipse([x - s, y - s * 0.38, x + s, y + s * 0.38], fill=bc)
        for k in (-1, 1): d.polygon([(x - s * 0.95, y), (x - s * 1.35, y + k * s * 0.45), (x - s * 0.7, y + k * s * 0.12)], fill=bc)
        d.line([(x, y + s * 0.38), (x + rng.uniform(-40, 40), H)], fill=bc[:3] + (90,), width=1)
    # perspective street: two terraces converging to vanishing point
    st = Image.new("RGBA", (PW, H), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
    vx, vy = PW / 2 + 60, H * 0.52
    brick = (22, 18, 18) if night else (92, 70, 60)
    brick2 = (16, 13, 13) if night else (74, 56, 48)
    for side in (-1, 1):
        for k in range(14):
            f0 = 1 - k / 14; f1 = 1 - (k + 1) / 14
            x0 = vx + side * (PW * 0.6) * f0 ** 1.2; x1 = vx + side * (PW * 0.6) * f1 ** 1.2
            r0 = vy - 760 * f0 ** 1.2 - 30; r1 = vy - 760 * f1 ** 1.2 - 30
            b0 = vy + 520 * f0 ** 1.2; b1 = vy + 520 * f1 ** 1.2
            d.polygon([(x0, r0), (x1, r1), (x1, b1), (x0, b0)], fill=brick if k % 2 else brick2)
            # chimney pots
            cx = (x0 + x1) / 2; ch = (r0 - r1) * 0.0 + 30 * f0 ** 1.2 + 6
            d.rectangle([cx - 10 * f0, (r0 + r1) / 2 - ch, cx + 10 * f0, (r0 + r1) / 2 + 2], fill=brick2)
            # windows
            for row in range(3):
                for col in range(2):
                    fx = 0.3 + 0.4 * col; fy = 0.2 + 0.22 * row
                    wx0 = lerp(x0, x1, fx - 0.08); wx1 = lerp(x0, x1, fx + 0.08)
                    yt0 = lerp(r0, b0, fy); yt1 = lerp(r0, b0, fy + 0.12)
                    yb0 = lerp(r1, b1, fy); yb1 = lerp(r1, b1, fy + 0.12)
                    wc = (6, 6, 8) if night else (40, 46, 54)
                    if not night and rng.random() < 0.5: wc = (70, 78, 88)
                    d.polygon([(wx0, lerp(yt0, yb0, fx - 0.08)), (wx1, lerp(yt0, yb0, fx + 0.08)), (wx1, lerp(yt1, yb1, fx + 0.08)), (wx0, lerp(yt1, yb1, fx - 0.08))], fill=wc + (255,))
                    if not night:  # anti-blast tape crosses
                        d.line([(wx0, lerp(yt0, yb0, fx - .08)), (wx1, lerp(yt1, yb1, fx + .08))], fill=(200, 196, 180, 120), width=1)
    # road and pavement
    d.polygon([(vx - 30, vy + 8), (vx + 30, vy + 8), (PW, H), (0, H)], fill=(10, 11, 14, 255) if night else (66, 68, 70, 255))
    # sandbags
    for i in range(10):
        sx = 80 + i * 40; sy = H - 120 - (i % 2) * 22
        d.ellipse([sx, sy, sx + 70, sy + 34], fill=(40, 36, 30, 255) if night else (150, 136, 108, 255), outline=(20, 18, 14, 255))
    # street lamp (masked)
    lx = PW * 0.72
    d.line([(lx, H * 0.95), (lx, H * 0.3)], fill=(10, 10, 12, 255), width=10)
    d.rectangle([lx - 26, H * 0.28, lx + 26, H * 0.33], fill=(12, 12, 14, 255))
    return sky, bl, st, (lx, H * 0.33)


def rain_layer(seed, t, n=420, angle=0.16, alpha=70):
    rng = random.Random(seed); im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        x0 = rng.uniform(-200, W); y0 = rng.uniform(0, H); sp = rng.uniform(900, 1500); ln = rng.uniform(25, 60)
        y = (y0 + sp * t) % (H + 100) - 50; x = x0 + angle * y
        d.line([(x, y), (x + angle * ln, y + ln)], fill=(200, 210, 225, rng.randint(alpha // 2, alpha)), width=1)
    return im


# ───────────────────────── WELSH VALLEY ─────────────────────────
@functools.lru_cache(None)
def valley_layers(variant):
    dusk = variant == "dusk"; rng = random.Random(21); PW = W + 400
    sky = np.zeros((H, PW, 3), np.float32); g = np.linspace(0, 1, H)[:, None]
    top, bot = ((50, 60, 92), (220, 150, 110)) if dusk else ((110, 140, 170), (200, 208, 210))
    sky[:] = (np.array(top) + (np.array(bot) - np.array(top)) * g ** 1.3)[:, None, :]
    n = smooth_noise(PW, H, 220, 3, 3); sky = sky * (0.92 + 0.16 * n[..., None])
    sky = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert("RGBA")
    layers = []
    cols = [(118, 130, 128), (84, 104, 82), (58, 76, 56), (38, 50, 36)] if not dusk else [(96, 86, 110), (70, 64, 86), (48, 44, 60), (28, 26, 36)]
    for li, (base_y, amp, c) in enumerate([(0.50, 90, cols[0]), (0.58, 110, cols[1]), (0.70, 120, cols[2]), (0.86, 90, cols[3])]):
        im = Image.new("RGBA", (PW, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        ph = rng.uniform(0, 6); pts = [(0, H)]
        for i in range(121):
            x = PW * i / 120
            y = H * base_y - amp * (0.6 * math.sin(x / PW * 3.2 + ph) + 0.3 * math.sin(x / PW * 7.1 + ph * 2) + 0.1 * math.sin(x / PW * 17 + ph))
            pts.append((x, y))
        pts.append((PW, H)); d.polygon(pts, fill=c + (255,))
        if li in (1, 2):  # terraced miners' houses following the contour
            for row in range(3):
                for i in range(int(PW / 26)):
                    x = i * 26 + row * 13; xi = int(x / PW * 120)
                    if xi >= 120: continue
                    y = pts[xi + 1][1] + 30 + row * 26
                    if rng.random() < 0.15: continue
                    hc = tuple(int(v * 0.8) for v in c)
                    d.rectangle([x, y, x + 24, y + 16], fill=hc + (255,)); d.polygon([(x - 2, y), (x + 12, y - 9), (x + 26, y)], fill=(54, 56, 62, 255) if not dusk else (34, 32, 42, 255))
                    if dusk and rng.random() < 0.3: d.rectangle([x + 9, y + 5, x + 14, y + 10], fill=(255, 200, 120, 220))
        if li == 2:  # colliery headframe
            hx, hy = PW * 0.62, H * 0.56
            sc = (30, 30, 34, 255)
            d.line([(hx - 40, hy + 120), (hx, hy - 60)], fill=sc, width=6); d.line([(hx + 40, hy + 120), (hx, hy - 60)], fill=sc, width=6)
            d.line([(hx + 110, hy + 120), (hx, hy - 50)], fill=sc, width=5)
            d.ellipse([hx - 34, hy - 94, hx + 34, hy - 26], outline=sc, width=6)
            d.rectangle([hx - 120, hy + 60, hx - 40, hy + 130], fill=sc); d.rectangle([hx - 100, hy - 30, hx - 86, hy + 60], fill=sc)
        layers.append(im)
    smoke = smooth_noise(PW, 400, 60, 9, 3)
    sa = np.zeros((400, PW, 4), np.uint8); sa[..., :3] = (200, 196, 190) if not dusk else (120, 110, 120)
    sa[..., 3] = (np.clip(smoke - 0.5, 0, 1) * 160).astype(np.uint8)
    return sky, layers, Image.fromarray(sa, "RGBA")


# ───────────────────────── INTERIOR (office / mortuary) ─────────────────────────
@functools.lru_cache(None)
def office_plate(variant):
    PW, PH = W + 300, H + 170
    rng = random.Random(31)
    if variant == "mortuary":
        img = Image.new("RGB", (PW, PH), (40, 48, 52)); d = ImageDraw.Draw(img)
        for y in range(0, int(PH * 0.72), 44):
            for x in range(0, PW, 64): d.rectangle([x, y, x + 62, y + 42], fill=(58 + rng.randint(-4, 4), 70, 74), outline=(34, 40, 44))
        d.rectangle([0, PH * 0.72, PW, PH], fill=(26, 30, 32))
        d.rectangle([PW * 0.62, PH * 0.2, PW * 0.82, PH * 0.72], fill=(70, 76, 80), outline=(30, 32, 34), width=6)  # cold-store door
        d.rectangle([PW * 0.79, PH * 0.42, PW * 0.81, PH * 0.5], fill=(150, 152, 150))
        arr = np.asarray(img, np.float32) * (0.45 + 0.75 * radial(PW, PH, PW * 0.4, PH * 0.15, PW * 0.7)[..., None])
        return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    lamp = variant == "lamp"
    img = Image.new("RGB", (PW, PH), (52, 46, 40) if not lamp else (24, 21, 19)); d = ImageDraw.Draw(img)
    # wood panelling lower wall
    d.rectangle([0, PH * 0.48, PW, PH * 0.74], fill=(60, 40, 28) if not lamp else (30, 20, 14))
    for x in range(0, PW, 150): d.line([(x, PH * 0.48), (x, PH * 0.74)], fill=(40, 26, 18), width=3)
    # window with blackout tape
    wx0, wy0, wx1, wy1 = PW * 0.66, PH * 0.08, PW * 0.88, PH * 0.44
    d.rectangle([wx0, wy0, wx1, wy1], fill=(170, 180, 190) if not lamp else (14, 16, 22), outline=(30, 24, 20), width=12)
    d.line([(wx0, wy0), (wx1, wy1)], fill=(220, 214, 190) if not lamp else (60, 58, 50), width=6); d.line([(wx1, wy0), (wx0, wy1)], fill=(220, 214, 190) if not lamp else (60, 58, 50), width=6)
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(30, 24, 20), width=8)
    # wall map (real geography outline)
    from scenes_m import draw_map_into
    mp = Image.new("RGB", (620, 400), (196, 186, 160)); draw_map_into(mp, (12, 44, 42), 3.0 if True else 1, fill=(160, 150, 126), line=(90, 80, 64))
    img.paste(mp, (int(PW * 0.12), int(PH * 0.08)))
    d.rectangle([PW * 0.12 - 6, PH * 0.08 - 6, PW * 0.12 + 626, PH * 0.08 + 406], outline=(40, 28, 20), width=8)
    # filing cabinet
    d.rectangle([PW * 0.02, PH * 0.3, PW * 0.1, PH * 0.78], fill=(70, 74, 64) if not lamp else (34, 36, 32))
    for k in range(4): d.rectangle([PW * 0.03, PH * (0.33 + k * 0.11), PW * 0.09, PH * (0.42 + k * 0.11)], outline=(40, 42, 36), width=3)
    # desk
    d.polygon([(0, PH * 0.74), (PW, PH * 0.70), (PW, PH), (0, PH)], fill=(70, 46, 30) if not lamp else (38, 24, 16))
    # papers, typewriter, phone, lamp
    for i in range(6):
        x, y = rng.uniform(PW * 0.2, PW * 0.6), rng.uniform(PH * 0.8, PH * 0.92)
        d.polygon([(x, y), (x + 160, y - 10), (x + 170, y + 100), (x + 8, y + 112)], fill=(214, 206, 186))
    tx, ty = PW * 0.66, PH * 0.80
    d.rectangle([tx, ty - 50, tx + 230, ty + 40], fill=(22, 22, 24)); d.rectangle([tx + 20, ty - 90, tx + 210, ty - 50], fill=(30, 30, 32))
    d.ellipse([PW * 0.08, PH * 0.82, PW * 0.14, PH * 0.88], fill=(14, 14, 14))
    lx = PW * 0.46
    d.line([(lx, PH * 0.8), (lx + 40, PH * 0.56)], fill=(30, 40, 30), width=10); d.polygon([(lx - 30, PH * 0.58), (lx + 120, PH * 0.52), (lx + 110, PH * 0.6), (lx - 10, PH * 0.64)], fill=(30, 60, 40))
    arr = np.asarray(img, np.float32)
    if lamp:
        arr *= (0.35 + 1.25 * radial(PW, PH, lx + 40, PH * 0.82, PW * 0.42)[..., None] ** 1.4)
        arr += radial(PW, PH, lx + 40, PH * 0.82, PW * 0.3)[..., None] ** 2 * np.array([60, 44, 20])
    else:
        arr *= (0.6 + 0.6 * radial(PW, PH, PW * 0.77, PH * 0.26, PW * 0.8)[..., None])
    n = smooth_noise(PW, PH, 4, 7, 1)
    arr *= (0.92 + 0.16 * n[..., None])
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


@functools.lru_cache(None)
def huelva_plate():
    PW, PH = W + 300, H + 170; rng = random.Random(41)
    sky = np.zeros((PH, PW, 3), np.float32); g = np.linspace(0, 1, PH)[:, None]
    sky[:] = (np.array([70, 128, 196]) + (np.array([200, 222, 238]) - np.array([70, 128, 196])) * g ** 1.2)[:, None, :]
    img = Image.fromarray(sky.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    x = -20
    while x < PW:
        bw = rng.uniform(120, 260); bh = rng.uniform(200, 420); top = PH * 0.78 - bh
        wc = rng.choice([(238, 234, 222), (230, 222, 200), (244, 238, 230), (226, 200, 160)])
        d.rectangle([x, top, x + bw, PH], fill=wc)
        d.rectangle([x, top - 10, x + bw, top], fill=(180, 100, 70) if rng.random() < 0.5 else (210, 206, 196))
        for wy in np.arange(top + 30, PH * 0.74, 70):
            for wx in np.arange(x + 20, x + bw - 40, 60):
                d.rectangle([wx, wy, wx + 26, wy + 44], fill=(60, 70, 72)); d.rectangle([wx - 4, wy + 44, wx + 30, wy + 48], fill=(40, 40, 40))
        x += bw + rng.uniform(0, 10)
    # church tower
    cx = PW * 0.58
    d.rectangle([cx - 50, PH * 0.12, cx + 50, PH * 0.6], fill=(236, 222, 196)); d.polygon([(cx - 56, PH * 0.12), (cx, PH * 0.02), (cx + 56, PH * 0.12)], fill=(190, 110, 70))
    d.rectangle([cx - 20, PH * 0.17, cx + 20, PH * 0.25], fill=(60, 50, 40))
    # palms
    for px in (PW * 0.15, PW * 0.83):
        d.line([(px, PH), (px + 20, PH * 0.42)], fill=(90, 70, 50), width=18)
        for a in range(9):
            ang = a / 9 * math.pi * 1.05 - 0.05
            d.line([(px + 20, PH * 0.42), (px + 20 + math.cos(ang) * 190, PH * 0.42 - math.sin(ang) * 80 + 60)], fill=(40, 80, 40), width=14)
    d.rectangle([0, PH * 0.86, PW, PH], fill=(196, 180, 150))
    arr = np.asarray(img, np.float32)
    # hard sun shadow diagonal
    yy, xx = np.mgrid[:PH, :PW]; sh = ((xx * 0.35 + yy) % 520 < 120) & (yy > PH * 0.3)
    arr[sh] *= 0.82
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
