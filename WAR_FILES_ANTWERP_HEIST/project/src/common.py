import os, math, functools, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1920, 1080, 24
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FD = os.path.join(ROOT, "fonts")

GOLD = (201, 165, 76); GOLD_D = (150, 118, 50)
RED = (190, 40, 32); WHITE = (236, 233, 226); DIM = (150, 150, 146)
STEEL = (118, 128, 138); NAVY = (12, 22, 38); CYAN = (150, 205, 230)
BG = (9, 11, 14)

F_BEBAS = "bebas-neue-latin-400-normal.ttf"
F_OSW = "oswald-latin-400-normal.ttf"; F_OSW_B = "oswald-latin-600-normal.ttf"; F_OSW_L = "oswald-latin-300-normal.ttf"
F_INTER = "inter-latin-400-normal.ttf"; F_INTER_M = "inter-latin-500-normal.ttf"; F_INTER_B = "inter-latin-600-normal.ttf"
F_TYPE = "special-elite-latin-400-normal.ttf"; F_SERIF_I = "eb-garamond-latin-400-italic.ttf"; F_SERIF = "eb-garamond-latin-500-normal.ttf"


@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype(os.path.join(FD, name), int(size))


def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, t): return a + (b - a) * t
def ramp(t, t0, d=0.6): return smooth((t - t0) / d) if d > 0 else float(t >= t0)


def smooth_noise(w, h, cell, seed=0, octaves=3):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        sw, sh = max(2, w // c + 2), max(2, h // c + 2)
        small = (rng.random((sh, sw)) * 255).astype(np.uint8)
        im = Image.fromarray(small).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * amp; tot += amp; amp *= 0.5
    return acc / tot


def radial(w, h, cx, cy, r):
    y, x = np.ogrid[:h, :w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    return np.clip(1 - d, 0, 1).astype(np.float32)


def vignette(w, h, strength=0.65):
    y, x = np.ogrid[:h, :w]
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / 1.42
    return (1 - strength * np.clip(d, 0, 1) ** 1.8).astype(np.float32)


def bg_plate(w, h, seed=1, base=(12, 14, 18), light=(38, 46, 58), lx=0.3, ly=0.25, tex=0.12):
    n = smooth_noise(w, h, 260, seed)
    r = radial(w, h, w * lx, h * ly, max(w, h) * 0.9) ** 1.6
    base = np.array(base, np.float32); light = np.array(light, np.float32)
    img = base[None, None] + (light - base)[None, None] * r[..., None]
    img *= (1 - tex + 2 * tex * n)[..., None]
    img *= vignette(w, h, 0.5)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def text_img(text, fnt, fill=WHITE, tracking=0, alpha=255):
    fill = tuple(fill[:3]) + (alpha,)
    asc, desc = fnt.getmetrics()
    if tracking == 0:
        bb = fnt.getbbox(text)
        w = bb[2] + 4; h = asc + desc + 4
        im = Image.new("RGBA", (max(1, w), h), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((2, 2), text, font=fnt, fill=fill)
        return im
    widths = [fnt.getlength(c) for c in text]
    w = int(sum(widths) + tracking * (len(text) - 1)) + 6; h = asc + desc + 4
    im = Image.new("RGBA", (max(1, w), h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 2
    for c, cw in zip(text, widths):
        d.text((x, 2), c, font=fnt, fill=fill); x += cw + tracking
    return im


def paste(dst, src, x, y, anchor="lt", opacity=1.0):
    """alpha-composite src onto dst (RGBA) with anchor: l/c/r + t/m/b"""
    w, h = src.size
    if anchor[0] == "c": x -= w / 2
    elif anchor[0] == "r": x -= w
    if anchor[1] == "m": y -= h / 2
    elif anchor[1] == "b": y -= h
    if opacity <= 0: return dst
    if opacity < 1:
        src = src.copy(); a = src.getchannel("A").point(lambda v: int(v * opacity)); src.putalpha(a)
    dst.alpha_composite(src, (int(round(x)), int(round(y))))
    return dst


def glow(img_rgba, radius=12, strength=1.0):
    g = img_rgba.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1:
        a = g.getchannel("A").point(lambda v: min(255, int(v * strength))); g.putalpha(a)
    out = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0)); out.alpha_composite(g); out.alpha_composite(img_rgba)
    return out


def tag(frame, text, opacity=1.0):
    """Reconstruction label: top-left, discreet."""
    if not text or opacity <= 0: return frame
    f = font(F_OSW, 21)
    ti = text_img(text, f, (225, 222, 214), tracking=3)
    w, h = ti.size
    box = Image.new("RGBA", (w + 30, h + 10), (0, 0, 0, 120))
    ImageDraw.Draw(box).rectangle([0, 0, 3, h + 10], fill=GOLD + (255,))
    box.alpha_composite(ti, (18, 3))
    paste(frame, box, 56, 48, opacity=0.85 * opacity)
    return frame


def kb_transform(img, t, z0=1.0, z1=1.1, c0=(0.5, 0.5), c1=(0.5, 0.5), out=(W, H), resample=Image.BILINEAR):
    """Ken Burns: img plate (any size, ~16:9). zoom relative to fitting the plate."""
    pw, ph = img.size
    z = z0 * (z1 / z0) ** t if z0 > 0 and z1 > 0 else lerp(z0, z1, t)
    cx = lerp(c0[0], c1[0], t) * pw; cy = lerp(c0[1], c1[1], t) * ph
    vw = min(pw / z, ph / z * out[0] / out[1]); vh = vw * out[1] / out[0]
    cx = clamp(cx, vw / 2, pw - vw / 2); cy = clamp(cy, vh / 2, ph - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    return img.transform(out, Image.EXTENT, box, resample)


def to_rgba(im): return im if im.mode == "RGBA" else im.convert("RGBA")


@functools.lru_cache(None)
def dust_sprite(r):
    s = int(r * 4) + 2
    a = radial(s, s, s / 2, s / 2, r * 2) ** 2
    im = np.zeros((s, s, 4), np.uint8); im[..., :3] = 255; im[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(im, "RGBA")


class Dust:
    def __init__(self, n=40, seed=3, color=(255, 240, 210)):
        rng = random.Random(seed)
        self.p = [(rng.random(), rng.random(), rng.uniform(1.0, 3.2), rng.uniform(0.15, 0.55), rng.uniform(0, 6.28), rng.uniform(0.004, 0.02)) for _ in range(n)]
    def draw(self, frame, t, opacity=1.0):
        for x, y, r, a, ph, sp in self.p:
            xx = (x + sp * t * 0.6 + 0.01 * math.sin(t * 0.5 + ph)) % 1.0
            yy = (y - sp * t * 0.3 + 0.012 * math.cos(t * 0.4 + ph)) % 1.0
            tw = 0.6 + 0.4 * math.sin(t * 1.3 + ph)
            paste(frame, dust_sprite(round(r, 1)), xx * W, yy * H, "cm", opacity=a * tw * opacity)
        return frame


def light_sweep(arr, t, period=7.0, width=0.18, strength=0.35, angle=0.35, offset=0.0):
    """additive diagonal specular sweep weighted by luminance (arr float32 HxWx3 0..255)"""
    h, w = arr.shape[:2]
    pos = ((t / period + offset) % 1.0) * 1.8 - 0.4
    y, x = np.ogrid[:h, :w]
    u = (x / w) + angle * (y / h)
    band = np.exp(-((u - pos * (1 + angle)) / width) ** 2).astype(np.float32)
    lum = arr.mean(2, keepdims=True) / 255
    return arr + band[..., None] * lum * 255 * strength


def perspective_coeffs(src_quad, dst_quad):
    """coeffs mapping output(dst) -> input(src) for PIL PERSPECTIVE"""
    m = []
    for (x, y), (u, v) in zip(dst_quad, src_quad):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); m.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.array(m, float); B = np.array([c for p in src_quad for c in p], float)
    return np.linalg.solve(A, B).tolist()


def wrap_text(text, fnt, maxw):
    words = text.split(); lines = []; cur = ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if fnt.getlength(trial) <= maxw: cur = trial
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines


def finish(frame_rgba, vig=0.45):
    arr = np.asarray(frame_rgba.convert("RGB"), np.float32)
    if vig: arr *= VIG[..., None]
    return np.clip(arr, 0, 255).astype(np.uint8)


VIG = vignette(W, H, 0.45)
