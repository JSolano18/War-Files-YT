"""Scene renderers. Each factory returns an object with .frame(t) -> HxWx3 uint8."""
import json, math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *
from props import *

REG = {}
def scene(name):
    def deco(cls): REG[name] = cls; return cls
    return deco


class Base:
    def __init__(self, dur, cues, p):
        self.dur, self.cues, self.p = dur, cues, p
        self.dust = Dust(36, seed=hash(str(p)) % 1000)
        self.setup()
    def setup(self): pass
    def cue(self, i, frac=0.0):
        if not self.cues: return self.dur * 0.1
        if i >= len(self.cues): i = len(self.cues) - 1; frac = 1.0
        c = self.cues[i]; return c["s"] + frac * c["d"]
    def u(self, t): return clamp(t / max(self.dur, 1e-3))
    def post(self, fr, t, tagtxt=None, dust=True, vig=0.45):
        if dust: self.dust.draw(fr, t, 0.8)
        tg = tagtxt if tagtxt is not None else self.p.get("tag")
        tag(fr, tg)
        return finish(fr, vig)


def rgba(im): return im.convert("RGBA")


# ───────────────────────── VAULT DOOR ─────────────────────────
@scene("vault_door")
class VaultDoor(Base):
    def setup(self):
        PW, PH = 2560, 1440
        red = self.p.get("light") == "red"
        plate = bg_plate(PW, PH, 11, (10, 12, 15), (55, 30, 28) if red else (34, 44, 58), 0.2, 0.2)
        plate = rgba(plate)
        # concrete wall texture
        n = smooth_noise(PW, PH, 30, 2, 3)
        arr = np.asarray(plate, np.float32); arr[..., :3] *= (0.85 + 0.3 * n)[..., None]
        plate = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        self.state = self.p.get("state", "closed")
        DS = 1250
        self.DS = DS; self.dx, self.dy = PW / 2 - DS / 2, PH / 2 - DS / 2
        door = vault_door(DS, (1.05, 0.98, 0.95) if red else (0.95, 1.0, 1.06))
        sh = Image.new("RGBA", (DS + 200, DS + 200), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([100, 130, DS + 100, DS + 130], fill=(0, 0, 0, 200))
        plate.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)), (int(self.dx - 100), int(self.dy - 100)))
        if self.state == "open":
            # doorway: dark interior with lit boxes visible
            inner = Image.new("RGBA", (DS, DS), (0, 0, 0, 0)); di = ImageDraw.Draw(inner)
            interior = Image.new("RGBA", (DS, DS), (6, 6, 8, 255))
            bw, bh = 120, 76
            for r in range(16):
                for c in range(12):
                    b = box_closed(bw, bh, 300 + r * 12 + c, (r * 12 + c) % 7)
                    if (r * 7 + c * 3) % 5 < 2:
                        o, dr, dwid = box_open(bw, bh, 1, r * 12 + c); interior.alpha_composite(o, (c * (bw + 6) - 40, r * (bh + 6) - 30))
                    else:
                        interior.alpha_composite(b, (c * (bw + 6) - 40, r * (bh + 6) - 30))
            ia = np.asarray(interior, np.float32)
            glowm = radial(DS, DS, DS * 0.45, DS * 0.55, DS * 0.6)
            ia[..., 0] *= 0.25 + 0.9 * glowm; ia[..., 1] *= 0.18 + 0.6 * glowm; ia[..., 2] *= 0.15 + 0.45 * glowm
            interior = Image.fromarray(ia.clip(0, 255).astype(np.uint8), "RGBA")
            m = Image.new("L", (DS, DS), 0); ImageDraw.Draw(m).ellipse([DS * 0.115, DS * 0.115, DS * 0.885, DS * 0.885], fill=255)
            frame_only = door.copy()
            fa = np.asarray(frame_only).copy(); yy, xx = np.mgrid[:DS, :DS]
            rr = np.sqrt((xx - DS / 2) ** 2 + (yy - DS / 2) ** 2) / (DS / 2); fa[rr < 0.80, 3] = 0
            plate.paste(interior, (int(self.dx), int(self.dy)), m)
            plate.alpha_composite(Image.fromarray(fa, "RGBA"), (int(self.dx), int(self.dy)))
            # door slab swung open to the right (foreshortened)
            slab = door.resize((int(DS * 0.30), DS), Image.LANCZOS)
            sa = np.asarray(slab).astype(np.float32); sa[..., :3] *= 0.55
            slab = Image.fromarray(sa.clip(0, 255).astype(np.uint8), "RGBA")
            edge = Image.new("RGBA", (int(DS * 0.36), DS), (0, 0, 0, 0))
            ImageDraw.Draw(edge).ellipse([0, 0, int(DS * 0.36) - 1, DS - 1], fill=(70, 72, 76, 255))
            sx = int(self.dx + DS * 0.95)
            plate.alpha_composite(edge, (sx - 20, int(self.dy)))
            plate.alpha_composite(slab, (sx, int(self.dy)))
            # light spill on floor
            spill = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
            ImageDraw.Draw(spill).polygon([(PW * 0.38, PH * 0.82), (PW * 0.62, PH * 0.82), (PW * 0.75, PH), (PW * 0.25, PH)], fill=(200, 120, 70, 70))
            plate.alpha_composite(spill.filter(ImageFilter.GaussianBlur(60)))
        else:
            plate.alpha_composite(door, (int(self.dx), int(self.dy)))
        self.plate = plate
        self.z = self.p.get("z", (1.0, 1.15))
        self.red = red

    def frame(self, t):
        u = self.u(t)
        base = self.plate.copy()
        if self.state != "open":
            ang = 0.25 + (0.6 * ease_in_out(u) if not self.red else -0.4 * ease_in_out(u))
            base.alpha_composite(wheel(self.DS, ang), (int(self.dx), int(self.dy)))
        fr = kb_transform(base, ease_in_out(u), self.z[0], self.z[1])
        arr = np.asarray(fr, np.float32)[..., :3]
        arr = light_sweep(arr, t, period=max(8, self.dur * 0.9), width=0.16, strength=0.45, offset=0.15)
        if self.red:
            g = radial(W, H, W * 0.12, H * 0.4, W * 0.9)[..., None]
            arr = arr * (0.75 + 0.25 * g) + g * np.array([70, 6, 4]) * 0.8
        else:
            g = radial(W, H, W * 0.85, H * 0.3, W * 0.8)[..., None]
            arr = arr + g * np.array([10, 20, 38])
        fl = 1.0 - 0.04 * (math.sin(t * 13) > 0.97)
        fr = Image.fromarray(np.clip(arr * fl, 0, 255).astype(np.uint8)).convert("RGBA")
        return self.post(fr, t)


# ───────────────────────── SAFE-DEPOSIT WALL ─────────────────────────
@scene("boxes_wall")
class BoxesWall(Base):
    def setup(self):
        self.mode = self.p.get("mode", "aftermath")
        PW, PH = 2700, 1560; self.PW, self.PH = PW, PH
        rng = random.Random(7 if self.mode != "aftermath2" else 9)
        self.bw, self.bh, self.g = 168, 104, 8
        cols, rows = PW // (self.bw + self.g) + 1, PH // (self.bh + self.g) + 1
        self.cells = [(r, c) for r in range(rows) for c in range(cols)]
        wall = Image.new("RGBA", (PW, PH), (20, 21, 23, 255))
        self.closed = {}
        for (r, c) in self.cells:
            x, y = c * (self.bw + self.g) + 4, r * (self.bh + self.g) + 4
            self.closed[(r, c)] = (x, y)
            wall.alpha_composite(box_closed(self.bw, self.bh, 1000 + r * 40 + c, (r + c) % 9), (x, y))
        self.wall = wall
        order = self.cells[:]; rng.shuffle(order)
        if self.mode == "opening":
            n = int(len(order) * 0.62); self.open_list = order[:n]
            t0, t1 = 0.4, self.dur - 0.6
            self.open_times = {cell: t0 + (t1 - t0) * (i / n) ** 0.8 for i, cell in enumerate(self.open_list)}
        else:
            n = int(len(order) * 0.68)
            for cell in order[:n]: self._open(self.wall, cell)
            self.open_times = {}
        self.done = set()
        self.cur = self.wall.copy()
        # debris (paper) foreground
        deb = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(deb)
        if self.mode != "opening":
            for i in range(140):
                x = rng.uniform(-50, W + 50); y = rng.uniform(H * 0.72, H * 1.05)
                w_, h_ = rng.uniform(40, 130), rng.uniform(25, 80); a = rng.uniform(0, 6.28)
                pts = [(x + math.cos(a + k) * w_ / 2 - math.sin(a + k) * 0, y + math.sin(a + k) * h_ / 2) for k in (0, 1.57, 3.14, 4.71)]
                cc = rng.randint(150, 225)
                d.polygon(pts, fill=(cc, cc - 5, cc - 15, 235))
                if rng.random() < 0.3: d.line([pts[0], pts[2]], fill=(120, 110, 100, 200), width=2)
            self.deb = deb.filter(ImageFilter.GaussianBlur(3.5))
        else: self.deb = None
        self.spot = None

    def _open(self, im, cell):
        x, y = self.closed[cell]; o, dr, dwid = box_open(self.bw, self.bh, 1, hash(cell) % 50)
        im.alpha_composite(o, (x, y)); im.alpha_composite(dr, (max(0, x - dwid), y))

    def frame(self, t):
        if self.open_times:
            for cell, ot in self.open_times.items():
                if ot <= t and cell not in self.done:
                    self._open(self.cur, cell); self.done.add(cell)
        u = ease_in_out(self.u(t))
        PW, PH = self.PW, self.PH
        # camera: perspective quad drifting
        ox = lerp(0.06, 0.16, u) * PW; oy = lerp(0.10, 0.06, u) * PH
        vw = PW * lerp(0.62, 0.55, u); vh = vw * 9 / 16
        k = 0.10  # perspective: right side farther
        src = [(ox, oy), (ox + vw, oy + vh * k), (ox + vw, oy + vh * (1 - k)), (ox, oy + vh)]
        coeffs = perspective_coeffs(src, [(0, 0), (W, 0), (W, H), (0, H)])
        fr = self.cur.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BILINEAR)
        arr = np.asarray(fr, np.float32)[..., :3]
        # flashlight beam sweeping
        sx = W * (0.25 + 0.5 * (0.5 + 0.5 * math.sin(t * 0.45))); sy = H * (0.42 + 0.1 * math.sin(t * 0.31))
        spot = radial(W, H, sx, sy, 620) ** 1.5
        amb = 0.22 if self.mode != "opening" else 0.30
        arr = arr * (amb + 1.15 * spot[..., None]) * np.array([0.92, 0.97, 1.08])
        arr += radial(W, H, W, 0, W)[..., None] * np.array([8, 14, 30])
        fr = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        if self.deb is not None:
            fr.alpha_composite(self.deb)
        return self.post(fr, t)


# ───────────────────────── DIAMONDS ─────────────────────────
@scene("diamonds")
class Diamonds(Base):
    def setup(self):
        self.v = self.p.get("variant", "fall")
        rng = random.Random({"fall": 1, "velvet": 2, "dark": 3}[self.v])
        if self.v == "velvet":
            n = smooth_noise(W + 400, H + 300, 3, 4, 2)
            base = np.array([12, 14, 26], np.float32)
            arr = base * (0.7 + 0.6 * n)[..., None] * (0.4 + 1.2 * radial(W + 400, H + 300, (W + 400) * 0.45, (H + 300) * 0.35, 1500) ** 1.3)[..., None]
            self.bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
        else:
            self.bg = rgba(bg_plate(W + 400, H + 300, 5, (3, 4, 6), (22, 26, 36) if self.v == "fall" else (34, 10, 10), 0.5, 0.3, 0.05))
        # bokeh
        bk = Image.new("RGBA", self.bg.size, (0, 0, 0, 0)); d = ImageDraw.Draw(bk)
        for i in range(40):
            x, y, r = rng.uniform(0, self.bg.size[0]), rng.uniform(0, self.bg.size[1]), rng.uniform(15, 70)
            c = rng.choice([(180, 200, 255), (255, 230, 190), (200, 210, 230)])
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (rng.randint(10, 35),))
        self.bg.alpha_composite(bk.filter(ImageFilter.GaussianBlur(8)))
        self.stones = []
        if self.v == "fall":
            for i in range(22):
                z = rng.uniform(0.3, 1.0)
                self.stones.append(dict(x=rng.uniform(0.05, 0.95), y=rng.uniform(-0.2, 1.0), s=int(60 + 240 * z ** 2), z=z, seed=i,
                                        vy=0.03 + 0.05 * z, rot=rng.uniform(0, 6), vr=rng.uniform(-0.25, 0.25), sq=rng.uniform(0.55, 1.0)))
        elif self.v == "velvet":
            for i in range(30):
                z = rng.uniform(0.35, 1.0)
                self.stones.append(dict(x=rng.uniform(0.0, 1.0), y=rng.uniform(0.15, 0.95), s=int(50 + 180 * z ** 1.5), z=z, seed=i + 50,
                                        vy=0, rot=rng.uniform(0, 6), vr=0.03, sq=rng.uniform(0.45, 0.62)))
        else:
            self.stones.append(dict(x=0.5, y=0.48, s=620, z=1.0, seed=99, vy=0, rot=0, vr=0.06, sq=0.62))
            for i in range(9):
                self.stones.append(dict(x=rng.uniform(0.05, 0.95), y=rng.uniform(0.15, 0.95), s=int(rng.uniform(60, 150)), z=0.4, seed=i + 120, vy=0, rot=rng.uniform(0, 6), vr=0.02, sq=0.55))
        self.stones.sort(key=lambda s: s["z"])

    def frame(self, t):
        u = self.u(t)
        ox = 200 * ease_in_out(u); oy = 150 * (0.5 - 0.5 * math.cos(u * math.pi)) * 0.5
        fr = self.bg.crop((int(ox), int(oy), int(ox) + W, int(oy) + H)).copy()
        zoom = 1.0 + (0.08 * u if self.v == "dark" else 0)
        for st in self.stones:
            y = (st["y"] + st["vy"] * t) % 1.25 - 0.12 if st["vy"] else st["y"]
            x = st["x"] + (0.02 * math.sin(t * 0.3 + st["seed"]) if self.v == "fall" else -0.03 * u * st["z"])
            s = int(st["s"] * zoom)
            dm = diamond(s, phase=t * (1.6 if self.v != "dark" else 0.9) + st["seed"], seed=st["seed"], rot=st["rot"] + st["vr"] * t, squash=st["sq"])
            if st["z"] < 0.55: dm = dm.filter(ImageFilter.GaussianBlur((0.55 - st["z"]) * 10))
            # shadow on velvet
            cx, cy = x * W, y * H
            if self.v != "fall":
                shp = Image.new("RGBA", (s + 60, int(s * st["sq"]) + 60), (0, 0, 0, 0))
                ImageDraw.Draw(shp).ellipse([30, 40, s + 30, int(s * st["sq"]) + 40], fill=(0, 0, 0, 150))
                paste(fr, shp.filter(ImageFilter.GaussianBlur(14)), cx, cy + s * 0.08, "cm")
            paste(fr, dm, cx, cy, "cm")
            # glints
            for gk in range(2):
                ph = t * 2.2 + st["seed"] * 1.37 + gk * 2.1
                a = max(0.0, math.sin(ph)) ** 18
                if a > 0.05 and st["z"] > 0.5:
                    gs = glint_sprite(int(s * 0.9))
                    gx = cx + s * 0.28 * math.cos(st["seed"] + gk * 2.4); gy = cy + s * 0.28 * st["sq"] * math.sin(st["seed"] + gk * 2.4)
                    paste(fr, gs, gx, gy, "cm", opacity=a)
        if self.v == "dark":
            arr = np.asarray(fr, np.float32)[..., :3]
            arr = arr * (0.55 + 0.55 * radial(W, H, W * 0.5, H * 0.45, W * 0.55)[..., None])
            fr = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
        return self.post(fr, t, dust=self.v != "velvet")


# ───────────────────────── TYPOGRAPHIC STATEMENT ─────────────────────────
@scene("statement")
class Statement(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W + 240, H + 135, 21 + len(self.p["lines"]), (8, 9, 12), (30, 32, 40), 0.5, 0.4))
        self.lines = self.p["lines"]; self.acc = set(self.p.get("accent", []))
        st = self.p.get("style", "center")
        self.style = st
        sizes = {"stack": 150, "row": 120, "title": 170, "center": 96, "left": 100}
        fs = sizes[st]
        self.imgs = []
        for i, ln in enumerate(self.lines):
            col = GOLD if i in self.acc else WHITE
            f = font(F_BEBAS, fs if not (st == "title" and i == 0) else 70)
            im = text_img(ln, f, col, tracking=6 if st != "title" else (14 if i == 0 else 8))
            self.imgs.append(glow(im, 18, 0.55) if i in self.acc else im)
        n = len(self.lines)
        # appearance times: spread over the first ~60% of the scene or cue-aligned
        if self.cues and len(self.cues) >= n and st != "stack":
            self.times = [self.cue(i) for i in range(n)]
        else:
            span = min(self.dur * 0.55, 1.1 * n)
            self.times = [0.25 + span * i / max(1, n) for i in range(n)]
        if st == "stack" and self.cues:  # NO EXPLOSION / NO ALARM / NO WITNESSES within sentence 0
            c = self.cues[0]; self.times = [c["s"] + c["d"] * f for f in (0.0, 0.33, 0.62)]

    def frame(self, t):
        u = self.u(t)
        fr = kb_transform(self.plate, u, 1.0, 1.06).convert("RGBA")
        n = len(self.imgs)
        if self.style == "row":
            tot = sum(im.size[0] for im in self.imgs) + 70 * (n - 1); x = W / 2 - tot / 2
            for im, t0 in zip(self.imgs, self.times):
                a = ramp(t, t0, 0.5); paste(fr, im, x, H * 0.44 + 20 * (1 - a), "lm", a); x += im.size[0] + 70
        elif self.style == "left":
            y = H * 0.40 - (n - 1) * 60
            ImageDraw.Draw(fr).rectangle([150, y - 50, 156, y - 50 + (n * 120) * ramp(t, 0, 0.8)], fill=GOLD + (255,))
            for im, t0 in zip(self.imgs, self.times):
                a = ramp(t, t0, 0.6); paste(fr, im, 200 + 30 * (1 - a), y, "lm", a); y += 120
        else:
            gap = {"stack": 150, "title": 150, "center": 105}[self.style]
            y = H * 0.42 - (n - 1) * gap / 2
            for i, (im, t0) in enumerate(zip(self.imgs, self.times)):
                a = ramp(t, t0, 0.5 if self.style == "stack" else 0.7)
                sc = 1.0 + 0.08 * (1 - ease_out(clamp((t - t0) / 0.5))) if self.style == "stack" else 1.0
                img = im if sc == 1.0 else im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.BILINEAR)
                paste(fr, img, W / 2, y, "cm", a); y += gap
        if self.style == "title":
            d = ImageDraw.Draw(fr); lw = 520 * ease_out(ramp(t, 0.4, 1.2))
            d.line([(W / 2 - lw / 2, H * 0.42 + 160), (W / 2 + lw / 2, H * 0.42 + 160)], fill=GOLD + (200,), width=2)
        return self.post(fr, t)


# ───────────────────────── CHAPTER CARD ─────────────────────────
@scene("chapter")
class Chapter(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 40, (6, 7, 9), (26, 26, 30), 0.5, 0.5))
        self.num = text_img("CHAPTER " + self.p["num"], font(F_OSW, 30), GOLD, tracking=12)
        self.title = text_img(self.p["title"], font(F_BEBAS, 150), WHITE, tracking=10)
    def frame(self, t):
        fr = self.plate.copy()
        fin = ramp(t, 0.0, 0.5); fout = 1 - ramp(t, self.dur - 0.45, 0.45)
        a = fin * fout
        paste(fr, self.num, W / 2, H * 0.36, "cm", a * ramp(t, 0.15, 0.6))
        sc = 1.04 - 0.04 * ease_out(t / self.dur)
        ti = self.title.resize((int(self.title.size[0] * sc), int(self.title.size[1] * sc)), Image.BILINEAR)
        paste(fr, ti, W / 2, H * 0.47, "cm", a * ramp(t, 0.3, 0.7))
        d = ImageDraw.Draw(fr); lw = 600 * ease_out(ramp(t, 0.35, 1.4))
        d.line([(W / 2 - lw / 2, H * 0.58), (W / 2 + lw / 2, H * 0.58)], fill=GOLD + (int(220 * a),), width=2)
        return self.post(fr, t, tagtxt="")


# ───────────────────────── TITLE ─────────────────────────
@scene("title")
class Title(Base):
    def setup(self):
        door = rgba(Image.fromarray(VaultDoor(10, [], {"state": "closed", "z": (1.0, 1.0)}).frame(0)))
        door = Image.fromarray((np.asarray(door.filter(ImageFilter.GaussianBlur(6)), np.float32)[..., :3] * 0.35).astype(np.uint8)).convert("RGBA")
        self.plate = door
        self.l1 = text_img("THE ANTWERP", font(F_BEBAS, 120), WHITE, tracking=14)
        self.l2 = glow(text_img("DIAMOND HEIST", font(F_BEBAS, 205), GOLD, tracking=10), 22, 0.6)
        self.l3 = text_img("ANTWERP DIAMOND CENTRE  ·  BELGIUM  ·  FEBRUARY 2003", font(F_OSW, 28), DIM, tracking=6)
        self.disc = text_img("Scenes marked ILLUSTRATION or DRAMATIZATION are reconstructions — not archival footage.", font(F_INTER, 22), (160, 158, 150))
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.08).convert("RGBA")
        paste(fr, self.l1, W / 2, H * 0.30, "cm", ramp(t, 0.2, 0.9))
        sc = 1.06 - 0.06 * ease_out(clamp(t / 2.5))
        l2 = self.l2.resize((int(self.l2.size[0] * sc), int(self.l2.size[1] * sc)), Image.BILINEAR)
        paste(fr, l2, W / 2, H * 0.45, "cm", ramp(t, 0.5, 1.0))
        d = ImageDraw.Draw(fr); lw = 760 * ease_out(ramp(t, 0.9, 1.4))
        d.line([(W / 2 - lw / 2, H * 0.57), (W / 2 + lw / 2, H * 0.57)], fill=GOLD + (200,), width=2)
        paste(fr, self.l3, W / 2, H * 0.62, "cm", ramp(t, 1.4, 0.9))
        paste(fr, self.disc, W / 2, H * 0.72, "cm", 0.85 * ramp(t, 2.0, 0.9))
        return self.post(fr, t, tagtxt="")


# ───────────────────────── MAPS ─────────────────────────
@functools.lru_cache(None)
def countries():
    tj = json.load(open("/home/user/npmassets/node_modules/world-atlas/countries-50m.json"))
    sc, tr = tj["transform"]["scale"], tj["transform"]["translate"]
    arcs = []
    for arc in tj["arcs"]:
        x = y = 0; pts = []
        for dx, dy in arc:
            x += dx; y += dy; pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    def ring(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a[1:] if pts else a)
        return pts
    out = {}
    for g in tj["objects"]["countries"]["geometries"]:
        nm = g.get("properties", {}).get("name", "?")
        if g["type"] == "Polygon": polys = [ring(g["arcs"][0])]
        elif g["type"] == "MultiPolygon": polys = [ring(p[0]) for p in g["arcs"]]
        else: continue
        polys = [np.array(p) for p in polys if any(-25 < q[0] < 45 and 30 < q[1] < 72 for q in p[::5] + [p[0]])]
        if polys: out[nm] = polys
    return out

CITIES = {"ANTWERP": (4.4025, 51.2194), "BRUSSELS": (4.3517, 50.8503), "TURIN": (7.6869, 45.0703),
          "MECHELEN": (4.4776, 51.0259), "VILVOORDE": (4.4245, 50.9281)}
LABELS = {"BELGIUM": (4.6, 50.45), "NETHERLANDS": (5.6, 52.3), "FRANCE": (2.4, 47.0), "GERMANY": (10.2, 51.0),
          "ITALY": (12.5, 43.0), "SWITZERLAND": (8.2, 46.85), "UNITED KINGDOM": (-1.6, 52.6), "NORTH SEA": (3.0, 55.0),
          "LUXEMBOURG": (6.1, 49.75), "SPAIN": (-3.5, 40.0), "AUSTRIA": (14.4, 47.5)}
COSL = math.cos(math.radians(49))

@scene("map")
class MapScene(Base):
    def setup(self):
        self.C = countries(); self.mode = self.p["mode"]
        self.sea = rgba(bg_plate(W, H, 60, (7, 10, 15), (16, 24, 34), 0.4, 0.3, 0.06))
    def proj(self, lon, lat, cam):
        cx, cy, s = cam
        return (W / 2 + (lon - cx) * COSL * s, H / 2 - (lat - cy) * s)
    def cam(self, t):
        if self.mode == "europe_belgium":
            t1 = self.cue(1, 0.0); t2 = self.cue(2, 0.6)
            a = ease_in_out(clamp((t - t1 * 0.6) / max(0.1, (t2 - t1 * 0.6))))
            c0, c1 = (8.0, 49.0, 30), (4.45, 50.95, 400)
            s = c0[2] * (c1[2] / c0[2]) ** a
            return (lerp(c0[0], c1[0], a), lerp(c0[1], c1[1], a), s)
        if self.mode == "turin_antwerp":
            a = ease_in_out(self.u(t)); return (lerp(6.2, 6.0, a), lerp(48.4, 48.2, a), lerp(95, 108, a))
        a = ease_in_out(self.u(t)); return (lerp(4.43, 4.42, a), lerp(51.03, 51.04, a), lerp(1200, 1330, a))
    def frame(self, t):
        cam = self.cam(t); fr = self.sea.copy()
        d = ImageDraw.Draw(fr, "RGBA")
        # graticule
        for lon in range(-30, 50, 2 if cam[2] < 300 else 1):
            x = self.proj(lon, 0, cam)[0]
            if 0 <= x <= W: d.line([(x, 0), (x, H)], fill=(60, 80, 100, 26), width=1)
        for lat in range(30, 72, 2 if cam[2] < 300 else 1):
            y = self.proj(0, lat, cam)[1]
            if 0 <= y <= H: d.line([(0, y), (W, y)], fill=(60, 80, 100, 26), width=1)
        hl = {"europe_belgium": "Belgium", "turin_antwerp": None, "e19": "Belgium"}[self.mode]
        hl_a = ramp(t, self.cue(1, 0.2), 1.0) if self.mode == "europe_belgium" else (1.0 if self.mode == "e19" else 0)
        for nm, polys in self.C.items():
            for p in polys:
                xs = W / 2 + (p[:, 0] - cam[0]) * COSL * cam[2]; ys = H / 2 - (p[:, 1] - cam[1]) * cam[2]
                if xs.max() < -50 or xs.min() > W + 50 or ys.max() < -50 or ys.min() > H + 50: continue
                pts = list(zip(xs.tolist(), ys.tolist()))
                if len(pts) < 3: continue
                if nm == hl:
                    fa = hl_a if self.mode != "e19" else 0.10
                    d.polygon(pts, fill=(int(lerp(34, 120, fa)), int(lerp(38, 96, fa)), int(lerp(46, 46, fa)), 255), outline=(GOLD + (int(80 + 150 * hl_a),)))
                elif nm == "Italy" and self.mode == "turin_antwerp":
                    d.polygon(pts, fill=(52, 48, 40, 255), outline=(110, 100, 80, 255))
                else:
                    d.polygon(pts, fill=(30, 34, 41, 255), outline=(78, 86, 98, 255))
        # country labels
        if cam[2] < 600:
            for nm, (lo, la) in LABELS.items():
                x, y = self.proj(lo, la, cam)
                if -100 < x < W + 100 and -50 < y < H + 50:
                    col = GOLD if nm == "BELGIUM" and self.mode == "europe_belgium" else (120, 128, 138)
                    fs = 22 if cam[2] < 120 else 30
                    paste(fr, text_img(nm, font(F_OSW, fs), col, tracking=6), x, y, "cm", 0.8)
        def city(nm, a, anchor="lm", big=False, dy=0):
            if a <= 0: return
            x, y = self.proj(*CITIES[nm], cam)
            r = 9 if big else 6
            pul = (t * 0.8) % 1.0
            d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD + (int(255 * a),))
            if big:
                rr = r + 40 * pul
                d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=GOLD + (int(200 * (1 - pul) * a),), width=2)
            paste(fr, text_img(nm, font(F_OSW_B, 34 if big else 26), WHITE, tracking=5), x + (22 if anchor == "lm" else -22), y + dy, anchor, a)
        if self.mode == "europe_belgium":
            a = ramp(t, self.cue(1, 0.3), 0.8)
            city("ANTWERP", a, big=True); city("BRUSSELS", a * 0.9)
            if cam[2] > 250:
                x1, y1 = self.proj(*CITIES["ANTWERP"], cam); x2, y2 = self.proj(*CITIES["BRUSSELS"], cam)
                b = ramp(t, self.cue(1, 0.7), 0.8)
                d.line([(x1 - 40, y1), (x2 - 40, y2)], fill=WHITE + (int(160 * b),), width=2)
                paste(fr, text_img("~45 KM", font(F_OSW, 26), DIM, tracking=4), x1 - 60, (y1 + y2) / 2, "rm", b)
            if t > self.cue(3, 0):
                g = ramp(t, self.cue(3, 0), 0.5)
                x, y = self.proj(*CITIES["ANTWERP"], cam)
                gl = Image.new("RGBA", (400, 400), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([150, 150, 250, 250], fill=GOLD + (200,))
                paste(fr, gl.filter(ImageFilter.GaussianBlur(40)), x, y, "cm", g)
        elif self.mode == "turin_antwerp":
            city("TURIN", ramp(t, 0.3, 0.6), big=True); city("ANTWERP", ramp(t, 0.3, 0.6), big=True)
            x1, y1 = self.proj(*CITIES["TURIN"], cam); x2, y2 = self.proj(*CITIES["ANTWERP"], cam)
            prog = ease_in_out(clamp((t - 0.8) / 3.5)); N = 60
            pts = []
            for i in range(int(N * prog) + 1):
                f = i / N; bend = math.sin(f * math.pi) * 70
                pts.append((lerp(x1, x2, f) - bend, lerp(y1, y2, f)))
            for i in range(0, len(pts) - 1, 2): d.line([pts[i], pts[i + 1]], fill=GOLD + (230,), width=4)
            paste(fr, text_img("~730 KM STRAIGHT-LINE", font(F_OSW, 24), DIM, tracking=4), (x1 + x2) / 2 - 120, (y1 + y2) / 2, "rm", ramp(t, 3.5, 0.8))
        else:  # e19
            route = [CITIES["ANTWERP"], (4.43, 51.15), (4.46, 51.08), CITIES["MECHELEN"], (4.45, 50.97), CITIES["VILVOORDE"], (4.39, 50.89), CITIES["BRUSSELS"]]
            prog = ease_in_out(clamp(t / max(1, self.dur * 0.55)))
            pp = [self.proj(*q, cam) for q in route]
            segs = len(pp) - 1; upto = prog * segs
            for i in range(segs):
                if i > upto: break
                f = min(1.0, upto - i); a, b = pp[i], pp[i + 1]
                d.line([a, (lerp(a[0], b[0], f), lerp(a[1], b[1], f))], fill=GOLD + (235,), width=7)
            for nm in ["ANTWERP", "MECHELEN", "VILVOORDE", "BRUSSELS"]:
                city(nm, ramp(t, 0.2, 0.6), big=(nm == "ANTWERP"))
            mx, my = self.proj(4.41, 50.94, cam)
            a = ramp(t, self.cue(1, 0.0), 0.8)
            if a > 0:
                d.ellipse([mx - 16, my - 16, mx + 16, my + 16], outline=RED + (int(255 * a),), width=4)
                lb = text_img("WOODLAND WHERE THE GARBAGE WAS FOUND", font(F_OSW_B, 24), (240, 120, 110), tracking=3)
                paste(fr, lb, mx - 30, my + 6, "rm", a)
            x, y = pp[3]; paste(fr, text_img("E19", font(F_BEBAS, 58), GOLD, tracking=4), x + 120, y - 40, "lm", ramp(t, 1.0, 0.6))
            paste(fr, text_img("SCHEMATIC  ·  POSITIONS APPROXIMATE", font(F_OSW, 20), DIM, tracking=4), W - 70, H - 175, "rm", 0.8)
        return self.post(fr, t, tagtxt=self.p.get("tag", "MAP"), dust=False, vig=0.55)


# ───────────────────────── CITY NIGHT ─────────────────────────
@scene("city_night")
class CityNight(Base):
    def setup(self):
        late = self.p.get("variant") == "late"
        PW = 2500; self.PW = PW
        sky = np.zeros((H, PW, 3), np.float32)
        g = np.linspace(0, 1, H)[:, None]
        top = np.array([4, 6, 12]); bot = np.array([28, 34, 52]) if not late else np.array([18, 24, 38])
        sky[:] = (top + (bot - top) * g ** 1.4)[:, None, :]
        rng = np.random.default_rng(3)
        for i in range(260):
            x, y = rng.integers(0, PW), rng.integers(0, int(H * 0.5)); sky[y, x] += rng.uniform(40, 150)
        self.sky = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert("RGBA")
        self.far = skyline(PW, H, 11, int(H * 0.70), (34, 40, 54, 255), (200, 180, 140), 0.05, scale=0.55, hmin=60, hmax=220)
        self.mid = skyline(PW, H, 12, int(H * 0.80), (16, 19, 27, 255), (255, 196, 120), 0.08 if late else 0.16, spire_x=1300, scale=1.0, hmin=60, hmax=200)
        self.near = skyline(PW, H, 13, int(H * 0.95), (6, 7, 10, 255), (255, 186, 110), 0.04 if late else 0.10, scale=1.5, hmin=40, hmax=160)
        fog = smooth_noise(PW * 2, 400, 160, 7, 3)
        fa = np.zeros((400, PW * 2, 4), np.uint8); fa[..., :3] = (60, 70, 90)
        fa[..., 3] = (np.clip(fog - 0.35, 0, 1) * 160 * np.sin(np.linspace(0, np.pi, 400))[:, None]).astype(np.uint8)
        self.fog = Image.fromarray(fa, "RGBA")
    def frame(self, t):
        u = ease_in_out(self.u(t))
        fr = self.sky.crop((int(40 * u), 0, int(40 * u) + W, H)).copy()
        for lay, sp in ((self.far, 120), (self.mid, 260), (self.near, 480)):
            fr.alpha_composite(lay.crop((int(sp * u), 0, int(sp * u) + W, H)))
            if lay is self.far:
                fx = int((t * 12) % self.PW); fr.alpha_composite(self.fog.crop((fx, 0, fx + W, 400)), (0, int(H * 0.52)))
        fx = int((t * 25 + 600) % self.PW); fr.alpha_composite(self.fog.crop((fx, 0, fx + W, 400)), (0, int(H * 0.68)))
        return self.post(fr, t, dust=False)


# ───────────────────────── DISTRICT SCHEMATIC ─────────────────────────
@scene("district")
class District(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 70, (10, 12, 16), (22, 27, 34), 0.6, 0.4, 0.05))
        # streets as polylines in screen coords (schematic, not to scale)
        self.streets = {
            "PELIKAANSTRAAT": [(1250, 120), (1270, 980)],
            "HOVENIERSSTRAAT": [(380, 300), (800, 330), (1255, 400)],
            "SCHUPSTRAAT": [(600, 470), (900, 520), (1258, 560)],
            "RIJFSTRAAT": [(820, 200), (870, 520), (930, 900)],
            "LANGE HERENTALSESTRAAT": [(250, 720), (1262, 740)],
        }
        self.order = ["PELIKAANSTRAAT", "HOVENIERSSTRAAT", "SCHUPSTRAAT", "RIJFSTRAAT", "LANGE HERENTALSESTRAAT"]
        rng = random.Random(4)
        blk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(blk)
        for i in range(220):
            x, y = rng.uniform(150, 1240), rng.uniform(100, 980)
            w_, h_ = rng.uniform(30, 80), rng.uniform(30, 70)
            d.rectangle([x, y, x + w_, y + h_], fill=(26, 30, 37, 255), outline=(36, 41, 50, 255))
        self.blocks = blk
    def street_t(self, nm):
        if nm == "HOVENIERSSTRAAT": return self.cue(2, 0.0)
        if nm == "SCHUPSTRAAT": return self.cue(2, 0.33)
        if nm == "RIJFSTRAAT": return self.cue(2, 0.66)
        if nm == "PELIKAANSTRAAT": return 0.6
        return self.cue(3, 0.0)
    def frame(self, t):
        u = ease_in_out(self.u(t))
        fr = self.plate.copy(); fr.alpha_composite(self.blocks)
        d = ImageDraw.Draw(fr, "RGBA")
        # station
        sa = ramp(t, 0.2, 0.8)
        d.rectangle([1300, 250, 1720, 780], fill=(40, 44, 52, int(255 * sa)), outline=GOLD + (int(150 * sa),), width=2)
        d.pieslice([1380, 170, 1640, 430], 180, 360, fill=(46, 50, 60, int(255 * sa)))
        paste(fr, text_img("ANTWERP CENTRAL STATION", font(F_OSW_B, 26), WHITE, tracking=4), 1510, 600, "cm", sa)
        for nm in self.order:
            pts = self.streets[nm]; t0 = self.street_t(nm); prog = ease_out(clamp((t - t0) / 0.9))
            if prog <= 0: continue
            hl = nm in ("HOVENIERSSTRAAT", "SCHUPSTRAAT", "RIJFSTRAAT")
            segs = len(pts) - 1; upto = prog * segs; drawn = []
            for i in range(segs):
                if i > upto: break
                f = min(1.0, upto - i); a, b = pts[i], pts[i + 1]
                drawn.append((a, (lerp(a[0], b[0], f), lerp(a[1], b[1], f))))
            for a, b in drawn:
                d.line([a, b], fill=(GOLD + (255,)) if hl else (110, 116, 126, 255), width=16 if hl else 12)
            a, b = pts[0], pts[1]
            ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
            li = text_img(nm, font(F_OSW_B, 24 if hl else 20), WHITE if hl else DIM, tracking=4).rotate(ang, expand=True, resample=Image.BICUBIC)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            paste(fr, li, mx + (-30 if nm == "PELIKAANSTRAAT" else 0), my - 32, "cm", ramp(t, t0 + 0.4, 0.6))
        # diamond centre marker
        if len(self.cues) >= 4:
            ma = ramp(t, self.cue(2, 0.5), 0.8)
            x, y = 1040, 538; pul = (t * 0.9) % 1
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=RED + (int(255 * ma),))
            rr = 12 + 40 * pul; d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=RED + (int(220 * (1 - pul) * ma),), width=3)
            paste(fr, text_img("ANTWERP DIAMOND CENTRE", font(F_OSW_B, 24), (245, 140, 130), tracking=3), x + 26, y + 34, "lm", ma)
        fr = kb_transform(fr, u, 1.0, 1.12, (0.5, 0.5), (0.55, 0.45)).convert("RGBA")
        return self.post(fr, t, dust=False, vig=0.5)


# ───────────────────────── BUILDING CROSS-SECTION ─────────────────────────
@scene("building")
class Building(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 80, (9, 11, 14), (24, 28, 36), 0.5, 0.2, 0.05))
        self.entry = self.p.get("mode") == "entry"
    def frame(self, t):
        fr = self.plate.copy(); d = ImageDraw.Draw(fr, "RGBA")
        G = 610  # street level y
        a0 = ramp(t, 0.1, 0.8)
        # ground hatch
        for i in range(-20, 80):
            x = i * 40
            d.line([(x, G + 8), (x - 300, G + 420)], fill=(70, 60, 45, int(70 * a0)), width=2)
        d.rectangle([0, G, W, G + 6], fill=(150, 140, 120, int(255 * a0)))
        paste(fr, text_img("STREET LEVEL", font(F_OSW, 24), DIM, tracking=6), 80, G - 24, "lm", a0)
        bx0, bx1 = 760, 1260
        # building above ground
        fl = 5; fh = 60
        for i in range(fl):
            a = ramp(t, 0.3 + i * 0.12, 0.5)
            y1 = G - (i + 1) * fh
            d.rectangle([bx0, y1, bx1, y1 + fh], fill=(36, 40, 48, int(255 * a)), outline=(90, 96, 108, int(255 * a)), width=2)
            for k in range(6):
                wx = bx0 + 30 + k * 78; d.rectangle([wx, y1 + 18, wx + 40, y1 + 50], fill=(70, 76, 88, int(200 * a)))
        paste(fr, text_img("ANTWERP DIAMOND CENTRE", font(F_OSW_B, 30), WHITE, tracking=5), (bx0 + bx1) / 2, G - fl * fh - 40, "cm", ramp(t, 0.6, 0.8))
        paste(fr, text_img("SCHUPSTRAAT 9–11", font(F_OSW, 24), GOLD, tracking=5), (bx0 + bx1) / 2, G - fl * fh - 8, "cm", ramp(t, 0.8, 0.8))
        # basements
        b1 = ramp(t, self.cue(1, 0.25) if not self.entry else 0.5, 0.7); b2 = ramp(t, self.cue(1, 0.45) if not self.entry else 0.8, 0.7)
        if b1 > 0.01: d.rectangle([bx0, G + 6, bx1, G + 150], fill=(26, 28, 34, int(255 * b1)), outline=(90, 96, 108, int(255 * b1)), width=2)
        paste(fr, text_img("LEVEL −1", font(F_OSW, 24), DIM, tracking=5), bx0 - 20, G + 78, "rm", b1)
        if b2 > 0.01: d.rectangle([bx0, G + 150, bx1, G + 300], fill=(30, 26, 22, int(255 * b2)), outline=GOLD + (int(255 * b2),), width=3)
        paste(fr, text_img("LEVEL −2  ·  THE VAULT", font(F_OSW_B, 26), GOLD, tracking=5), bx0 - 20, G + 225, "rm", b2)
        # vault icon
        if b2 > 0:
            vx, vy = (bx0 + bx1) / 2, G + 225
            pul = 0.5 + 0.5 * math.sin(t * 2.2)
            gl = Image.new("RGBA", (500, 300), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([150, 75, 350, 225], fill=GOLD + (120,))
            paste(fr, gl.filter(ImageFilter.GaussianBlur(30)), vx, vy, "cm", b2 * (0.5 + 0.5 * pul))
            d.ellipse([vx - 55, vy - 55, vx + 55, vy + 55], outline=(200, 200, 200, int(255 * b2)), width=6)
            d.ellipse([vx - 12, vy - 12, vx + 12, vy + 12], fill=(200, 200, 200, int(255 * b2)))
            for k in range(5):
                an = k / 5 * 6.283 + t * 0.3
                d.line([(vx, vy), (vx + math.cos(an) * 40, vy + math.sin(an) * 40)], fill=(200, 200, 200, int(255 * b2)), width=4)
        # descent path
        pa = ramp(t, self.cue(1, 0.6), 1.5)
        if pa > 0 and not self.entry:
            path = [(bx0 + 70, G - 20), (bx0 + 70, G + 75), (bx0 + 140, G + 75), (bx0 + 140, G + 225), (bx0 + 190, G + 225)]
            self._dash(d, path, pa, WHITE)
        if self.entry:
            # neighbouring property at back (left)
            na = ramp(t, 0.4, 0.8)
            d.rectangle([380, G - 210, 700, G], fill=(30, 33, 40, int(255 * na)), outline=(80, 86, 96, int(255 * na)), width=2)
            paste(fr, text_img("NEIGHBORING PROPERTY", font(F_OSW, 22), DIM, tracking=4), 540, G - 240, "cm", na)
            # street-facing cameras on the right
            for cx_ in (1320, 1420):
                d.polygon([(cx_, G - 160), (cx_ + 40, G - 170), (cx_ + 40, G - 150)], fill=(200, 60, 50, int(255 * na)))
            paste(fr, text_img("STREET CAMERAS", font(F_OSW, 22), (230, 120, 110), tracking=4), 1390, G - 200, "cm", na)
            pa = ramp(t, self.cue(1, 0.0), 2.5)
            path = [(450, G - 40), (720, G - 40), (bx0 + 60, G - 40), (bx0 + 60, G + 75), (bx0 + 140, G + 75), (bx0 + 140, G + 225), (bx0 + 190, G + 225)]
            self._dash(d, path, pa, GOLD)
            paste(fr, text_img("ROUTE AS DESCRIBED BY NOTARBARTOLO — NOT CONFIRMED BY POLICE", font(F_OSW, 22), GOLD, tracking=3), W / 2, G + 360, "cm", ramp(t, self.cue(1, 0.2), 0.8))
        fr = kb_transform(fr, ease_in_out(self.u(t)), 1.0, 1.08, (0.5, 0.5), (0.5, 0.56)).convert("RGBA")
        return self.post(fr, t, dust=False)
    def _dash(self, d, path, prog, col):
        L = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]; tot = sum(L); lim = tot * prog; acc = 0
        for i, l in enumerate(L):
            a, b = path[i], path[i + 1]; s = 0
            while s < l and acc + s < lim:
                e = min(l, s + 16, lim - acc)
                p1 = (lerp(a[0], b[0], s / l), lerp(a[1], b[1], s / l)); p2 = (lerp(a[0], b[0], e / l), lerp(a[1], b[1], e / l))
                d.line([p1, p2], fill=col + (255,), width=4); s += 28
            acc += l
        if prog > 0 and lim < tot + 1:
            acc = 0
            for i, l in enumerate(L):
                if acc + l >= lim:
                    f = (lim - acc) / l; a, b = path[i], path[i + 1]; p = (lerp(a[0], b[0], f), lerp(a[1], b[1], f))
                    d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=col + (255,)); break
                acc += l


# ───────────────────────── DOSSIER ─────────────────────────
def desk_plate(seed=90):
    n = smooth_noise(W + 200, H + 120, 40, seed, 3); st = smooth_noise(W + 200, H + 120, 3, seed + 1, 1)
    base = np.array([28, 20, 14], np.float32)
    arr = base * (0.6 + 0.6 * n + 0.15 * st)[..., None] * (0.35 + 1.1 * radial(W + 200, H + 120, (W + 200) * 0.42, (H + 120) * 0.35, 1500) ** 1.2)[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


def folder_card(w, h, name, alias, role, note, seed=0, photo=True):
    im = Image.new("RGBA", (w + 40, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 30, w + 20, h + 40], 8, fill=(0, 0, 0, 140))
    im = im.filter(ImageFilter.GaussianBlur(12)); d = ImageDraw.Draw(im)
    d.polygon([(10, 22), (w * 0.35, 22), (w * 0.4, 0), (w * 0.05, 0)], fill=(176, 146, 96, 255))
    d.rectangle([10, 20, w + 10, h + 20], fill=(186, 156, 104, 255))
    # paper
    px0, py0, px1, py1 = 40, 50, w - 10, h + 5
    d.rectangle([px0, py0, px1, py1], fill=(226, 218, 198, 255))
    tf = font(F_TYPE, int(w * 0.045)); tfs = font(F_TYPE, int(w * 0.036))
    d.text((px0 + 30, py0 + 24), "CASE FILE — ANTWERP 2003", font=tfs, fill=(120, 40, 30, 255))
    if photo:
        ph = (px0 + 30, py0 + 70, px0 + 30 + int(w * 0.28), py0 + 70 + int(w * 0.34))
        d.rectangle(ph, fill=(40, 40, 42, 255))
        cx, cy = (ph[0] + ph[2]) / 2, ph[1] + (ph[3] - ph[1]) * 0.42; r = (ph[2] - ph[0]) * 0.22
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(15, 15, 16, 255))
        d.pieslice([cx - r * 2.0, cy + r * 0.9, cx + r * 2.0, cy + r * 4.4], 180, 360, fill=(15, 15, 16, 255))
        d.text(((ph[0] + ph[2]) / 2, ph[3] - 14), "NO PHOTO", font=font(F_OSW, int(w * 0.026)), fill=(150, 150, 150, 255), anchor="mm")
        tx = ph[2] + 30
    else: tx = px0 + 30
    y = py0 + 75
    for lab, val in (("NAME", name), ("ALIAS", alias), ("ROLE", role)):
        d.text((tx, y), lab + ":", font=tfs, fill=(90, 80, 70, 255)); y += int(w * 0.045)
        for ln in wrap_text(val, tf, px1 - tx - 20):
            d.text((tx, y), ln, font=tf, fill=(30, 28, 26, 255)); y += int(w * 0.055)
        y += int(w * 0.02)
    if note:
        yy = max(y + 10, py0 + 70 + int(w * 0.36))
        for ln in wrap_text(note, tfs, px1 - px0 - 60):
            d.text((px0 + 30, yy), ln, font=tfs, fill=(60, 55, 50, 255)); yy += int(w * 0.045)
    return im


def stamp(text, size=60, col=RED, rot=-12):
    f = font(F_BEBAS, size); ti = text_img(text, f, col, tracking=4)
    w, h = ti.size; im = Image.new("RGBA", (w + 40, h + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([4, 4, w + 36, h + 20], outline=col + (255,), width=5); im.alpha_composite(ti, (20, 10))
    n = (smooth_noise(im.size[0], im.size[1], 4, 3, 1) > 0.35).astype(np.uint8) * 255
    a = np.minimum(np.asarray(im)[..., 3], n); arr = np.asarray(im).copy(); arr[..., 3] = (a * 0.85).astype(np.uint8)
    return Image.fromarray(arr, "RGBA").rotate(rot, expand=True, resample=Image.BICUBIC)


@scene("dossier")
class Dossier(Base):
    def setup(self):
        self.desk = desk_plate()
        p = self.p
        self.card = folder_card(980, 640, p["name"], p["alias"], p["role"], p.get("note", ""))
        self.st = stamp("CONVICTED 2005", 70)
    def frame(self, t):
        u = ease_in_out(self.u(t))
        fr = self.desk.copy()
        a = ramp(t, 0.0, 0.8)
        paste(fr, self.card, W / 2 + 40 * (1 - ease_out(clamp(t / 1.2))) + 80, H * 0.47, "cm", a)
        st0 = self.cue(3, 0.55)
        if t > st0:
            k = ease_out(clamp((t - st0) / 0.25)); s = 1.6 - 0.6 * k
            sti = self.st.resize((int(self.st.size[0] * s), int(self.st.size[1] * s)), Image.BILINEAR)
            paste(fr, sti, W / 2 + 330, H * 0.30, "cm", k)
        # lamp light
        fr = kb_transform(fr, u, 1.0, 1.12, (0.5, 0.5), (0.55, 0.45)).convert("RGBA")
        arr = np.asarray(fr, np.float32)[..., :3] * (0.55 + 0.6 * radial(W, H, W * 0.45, H * 0.3, W * 0.8)[..., None])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"), t)


@scene("crew")
class Crew(Base):
    def setup(self):
        self.desk = desk_plate(91)
        self.verdict = self.p.get("verdict", False)
        crew = [("ELIO D'ONORIO", "\"THE GENIUS\"", "Described as an alarms and electronics expert"),
                ("FERDINANDO FINOTTO", "\"THE MONSTER\"", "Described as a lock specialist, driver, strongman"),
                ("PIETRO TAVANO", "\"SPEEDY\"", "Described as Notarbartolo's longtime friend"),
                ("IDENTITY UNKNOWN", "\"THE KING OF KEYS\"", "Said to be a master key forger")]
        if self.verdict:
            crew = [("LEONARDO NOTARBARTOLO", "—", "Convicted of organizing the heist")] + crew
        self.cards = [folder_card(560, 520, n, a, r, "", i, True) for i, (n, a, r) in enumerate(crew)]
        if self.verdict:
            self.stamps = [stamp("10 YEARS", 56), stamp("5 YEARS", 56), stamp("5 YEARS", 56), stamp("5 YEARS", 56), stamp("NEVER IDENTIFIED", 46, (200, 170, 60))]
            self.st_t = [self.cue(0, 0.75), self.cue(1, 0.5), self.cue(1, 0.62), self.cue(1, 0.74), self.cue(2, 0.3)]
            self.card_t = [0.1 + 0.18 * i for i in range(5)]
            self.pos = [(W * (0.135 + 0.1825 * i), H * (0.44 + (0.04 if i % 2 else -0.02))) for i in range(5)]
            self.scale = 0.62
        else:
            self.card_t = [self.cue(i + 1, 0.0) for i in range(4)]
            self.pos = [(W * (0.15 + 0.235 * i), H * (0.45 + (0.035 if i % 2 else -0.02))) for i in range(4)]
            self.scale = 0.78
        self.cards = [c.resize((int(c.size[0] * self.scale), int(c.size[1] * self.scale)), Image.LANCZOS) for c in self.cards]
        self.rots = [random.Random(i).uniform(-4, 4) for i in range(5)]
        self.cards = [c.rotate(r, expand=True, resample=Image.BICUBIC) for c, r in zip(self.cards, self.rots)]
    def frame(self, t):
        fr = self.desk.copy()
        for i, c in enumerate(self.cards):
            a = ramp(t, self.card_t[i], 0.5)
            if a <= 0: continue
            x, y = self.pos[i]; y += 40 * (1 - ease_out(a))
            paste(fr, c, x, y, "cm", a)
            if self.verdict and t > self.st_t[i]:
                k = ease_out(clamp((t - self.st_t[i]) / 0.22)); s = 1.5 - 0.5 * k
                st = self.stamps[i]; sti = st.resize((int(st.size[0] * s), int(st.size[1] * s)), Image.BILINEAR)
                paste(fr, sti, x, y + 70, "cm", k)
        # emphasis: unknown man
        fr = kb_transform(fr, ease_in_out(self.u(t)), 1.0, 1.06).convert("RGBA")
        arr = np.asarray(fr, np.float32)[..., :3] * (0.6 + 0.55 * radial(W, H, W * 0.5, H * 0.3, W * 0.85)[..., None])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"), t)


# ───────────────────────── SECURITY LAYERS ─────────────────────────
LAYERS = [("COMBINATION DIAL", "100 million possible codes"), ("STEEL DOOR + KEY", "key reportedly ~1 ft long"),
          ("INFRARED HEAT DETECTORS", ""), ("SEISMIC SENSOR", "detects vibration"), ("DOPPLER RADAR", ""),
          ("LIGHT SENSOR", ""), ("MAGNETIC FIELD", "alarm if the door opens"), ("INDIVIDUAL BOX LOCKS", ""),
          ("GUARDS + CAMERAS", ""), ("DISTRICT POLICE + SECURITY", "")]

@scene("layers")
class Layers(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 100, (8, 10, 13), (22, 28, 36), 0.3, 0.5, 0.05))
        c = self.cue
        self.times = [c(2, 0.05), c(3, 0.05), c(4, 0.0), c(4, 0.22), c(4, 0.40), c(4, 0.52), c(4, 0.66), c(5, 0.05), c(6, 0.25), c(6, 0.6)]
    def frame(self, t):
        fr = self.plate.copy(); d = ImageDraw.Draw(fr, "RGBA")
        cx, cy = 520, 520
        # vault core
        a0 = ramp(t, 0.2, 0.8)
        d.rectangle([cx - 46, cy - 46, cx + 46, cy + 46], fill=GOLD + (int(230 * a0),))
        paste(fr, text_img("VAULT", font(F_OSW_B, 24), (20, 16, 8), tracking=3), cx, cy, "cm", a0)
        n_on = 0
        for i, t0 in enumerate(self.times):
            a = ramp(t, t0, 0.5)
            if a <= 0: continue
            n_on += 1
            r = 80 + i * 34
            pul = 1 + 0.03 * math.sin(t * 2 + i)
            col = GOLD if i == n_on - 1 and t - t0 < 2.0 else (110, 128, 150)
            d.ellipse([cx - r * pul, cy - r * pul, cx + r * pul, cy + r * pul], outline=col + (int(220 * a),), width=3 if col == GOLD else 2)
            # list item
            y = 150 + i * 76
            paste(fr, text_img(f"{i + 1:02d}", font(F_BEBAS, 50), GOLD, tracking=2), 1000 + 20 * (1 - a), y, "lm", a)
            paste(fr, text_img(LAYERS[i][0], font(F_OSW_B, 34), WHITE, tracking=4), 1080 + 20 * (1 - a), y - 6, "lm", a)
            if LAYERS[i][1]:
                paste(fr, text_img(LAYERS[i][1].upper(), font(F_OSW, 20), DIM, tracking=3), 1082 + 20 * (1 - a), y + 26, "lm", a)
        cnt = text_img(f"{n_on}", font(F_BEBAS, 140), GOLD, tracking=2)
        paste(fr, cnt, cx, 920, "cm", ramp(t, self.times[0], 0.4) * 0.0)  # (kept hidden; list is enough)
        paste(fr, text_img("AS DESCRIBED IN PUBLISHED ACCOUNTS", font(F_OSW, 22), DIM, tracking=5), 1000, 95, "lm", ramp(t, self.cue(1, 0), 0.6))
        return self.post(fr, t, tagtxt="DIAGRAM", dust=False)


# ───────────────────────── CORRIDOR (procedural 3D) ─────────────────────────
@scene("corridor")
class Corridor(Base):
    def setup(self):
        self.door = vault_door(900)
        self.f = 820; self.cam_h = 0.0
    def frame(self, t):
        u = self.u(t)
        door = self.p.get("door", False)
        if door:
            zc = lerp(0, 22, ease_out(u))   # approach; door at z=30
        else:
            zc = t * 2.0 * self.p.get("speed", 1.0)
        bob = 0.03 * math.sin(t * 5.2 * self.p.get("speed", 1.0))
        img = Image.new("RGB", (W, H), (6, 7, 9)); d = ImageDraw.Draw(img)
        glowl = Image.new("RGB", (W // 4, H // 4), (0, 0, 0)); gd = ImageDraw.Draw(glowl)
        hw, fl, ce = 1.7, -1.25 + bob, 1.35 + bob
        cx, cy = W / 2 + 20 * math.sin(t * 0.3), H / 2
        def P(x, y, z): return (cx + self.f * x / z, cy - self.f * y / z)
        def fog(z): return clamp(1 - z / 34) ** 1.4
        zmax = 32 if not door else 30 - zc
        seg = 3.0
        start = -((zc % seg))
        zs = [start + k * seg for k in range(1, 14)]
        zs = [z for z in [start] + zs if -seg < z < zmax + 0.01]
        # far wall
        zf = max(1.0, zmax)
        a = P(-hw, ce, zf); b = P(hw, fl, zf)
        fcol = int(8 + 10 * fog(zf))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=(fcol, fcol, fcol + 2))
        if door:
            ds = int(self.f * 2.3 / zf)
            if ds > 4:
                dimg = self.door.resize((ds, ds), Image.BILINEAR)
                arr = np.asarray(dimg).astype(np.float32); arr[..., :3] *= 0.4 + 0.6 * fog(zf) + 0.15
                img.paste(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"), (int(cx - ds / 2), int((a[1] + b[1]) / 2 - ds / 2)), Image.fromarray(arr[..., 3].astype(np.uint8)))
        for z in sorted(zs, reverse=True):
            z2 = z + seg
            z = max(z, 0.6)
            fz = fog(z); c = int(14 + 50 * fz)
            for side in (-1, 1):  # walls
                p = [P(side * hw, ce, z), P(side * hw, ce, min(z2, zf)), P(side * hw, fl, min(z2, zf)), P(side * hw, fl, z)]
                d.polygon(p, fill=(c, c, c + 3))
                # pillar rib
                pr = [P(side * hw, ce, z), P(side * (hw - 0.15), ce, z), P(side * (hw - 0.15), fl, z), P(side * hw, fl, z)]
                d.polygon(pr, fill=(int(c * 1.3), int(c * 1.3), int(c * 1.3) + 3))
            fp = [P(-hw, fl, z), P(hw, fl, z), P(hw, fl, min(z2, zf)), P(-hw, fl, min(z2, zf))]
            d.polygon(fp, fill=(int(c * 0.8), int(c * 0.8), int(c * 0.82)))
            cp = [P(-hw, ce, z), P(hw, ce, z), P(hw, ce, min(z2, zf)), P(-hw, ce, min(z2, zf))]
            d.polygon(cp, fill=(int(c * 0.6), int(c * 0.6), int(c * 0.65)))
            # ceiling light panel
            flick = 1.0 if (hash((int((z + zc) / seg), int(t * 8))) % 23) else 0.35
            lz0, lz1 = z + 0.8, z + 1.8
            if lz1 < zf:
                lp = [P(-0.35, ce - 0.01, lz0), P(0.35, ce - 0.01, lz0), P(0.35, ce - 0.01, lz1), P(-0.35, ce - 0.01, lz1)]
                lc = int(230 * (0.3 + 0.7 * fz) * flick)
                d.polygon(lp, fill=(lc, int(lc * 0.95), int(lc * 0.85)))
                gd.polygon([(x / 4, y / 4) for x, y in lp], fill=(int(lc * 0.8), int(lc * 0.72), int(lc * 0.6)))
                # floor reflection
                rp = [P(-0.3, fl, lz0), P(0.3, fl, lz0), P(0.3, fl, lz1), P(-0.3, fl, lz1)]
                gd.polygon([(x / 4, y / 4) for x, y in rp], fill=(int(lc * 0.18), int(lc * 0.17), int(lc * 0.15)))
        g = glowl.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
        arr = np.asarray(img, np.float32) + np.asarray(g, np.float32) * 0.9
        arr *= np.array([0.95, 0.98, 1.05])
        fr = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)).convert("RGBA")
        return self.post(fr, t, dust=True)


# ───────────────────────── BLUEPRINT ─────────────────────────
@scene("blueprint")
class Blueprint(Base):
    def setup(self):
        bg = Image.new("RGBA", (W, H), NAVY + (255,)); d = ImageDraw.Draw(bg)
        for x in range(0, W, 40): d.line([(x, 0), (x, H)], fill=(40, 70, 110, 70 if x % 200 else 140))
        for y in range(0, H, 40): d.line([(0, y), (W, y)], fill=(40, 70, 110, 70 if y % 200 else 140))
        self.bg = bg; self.mode = self.p["mode"]
    def frame(self, t):
        fr = self.bg.copy(); d = ImageDraw.Draw(fr, "RGBA")
        L = CYAN
        def circ(x, y, r, a, w=3): d.ellipse([x - r, y - r, x + r, y + r], outline=L + (int(255 * a),), width=w)
        if self.mode == "camera":
            cx, cy = 860, 600
            a = ramp(t, 0.2, 1.0)
            for r, w in ((330, 4), (300, 2), (230, 2), (70, 3), (85, 1)): circ(cx, cy, r * a ** 0.3, a, w)
            for i in range(100):
                an = i / 100 * 6.283; r0 = 90; r1 = 100 if i % 10 else 110
                d.line([(cx + math.cos(an) * r0, cy + math.sin(an) * r0), (cx + math.cos(an) * r1, cy + math.sin(an) * r1)], fill=L + (int(200 * a),), width=1)
            paste(fr, text_img("VAULT DOOR — FRONT ELEVATION", font(F_OSW, 24), L, tracking=5), cx, cy + 380, "cm", a)
            paste(fr, text_img("COMBINATION DIAL", font(F_OSW, 22), L, tracking=4), cx + 130, cy, "lm", ramp(t, 1.0, 0.8))
            # hidden camera above door
            ca = ramp(t, self.cue(1, 0.15), 0.8)
            kx, ky = cx, cy - 420
            d.rectangle([kx - 34, ky - 18, kx + 34, ky + 18], outline=(255, 210, 120, int(255 * ca)), width=3)
            d.ellipse([kx - 10, ky + 8, kx + 10, ky + 28], outline=(255, 210, 120, int(255 * ca)), width=3)
            cone = ramp(t, self.cue(1, 0.35), 1.0)
            if cone > 0:
                pul = 0.6 + 0.4 * math.sin(t * 3)
                cl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(cl).polygon([(kx, ky + 22), (cx - 110, cy - 20), (cx + 110, cy - 20)], fill=(255, 210, 120, int(45 * cone * pul))); fr.alpha_composite(cl); d = ImageDraw.Draw(fr, "RGBA")
                d.line([(kx, ky + 22), (cx - 110, cy - 20), (cx + 110, cy - 20), (kx, ky + 22)], fill=(255, 210, 120, int(200 * cone)), width=2)
                if int(t * 2) % 2 == 0: d.ellipse([kx + 50, ky - 30, kx + 66, ky - 14], fill=(230, 50, 40, int(255 * cone)))
                paste(fr, text_img("REC", font(F_OSW_B, 20), (230, 80, 70), tracking=3), kx + 74, ky - 22, "lm", cone)
            paste(fr, text_img("HIDDEN CAMERA — AS CLAIMED BY NOTARBARTOLO", font(F_OSW_B, 24), (255, 210, 120), tracking=4), kx + 60, ky + 18, "lm", ca)
            st = ramp(t, self.cue(2, 0.2), 0.8)
            if st > 0:
                paste(fr, text_img("LAYER 01 — DEFEATED?", font(F_BEBAS, 64), (255, 210, 120), tracking=4), 1290, 760, "lm", st)
        else:
            # replica rehearsal checklist
            a = ramp(t, 0.2, 1.0)
            x0, y0 = 300, 260
            # isometric room outline
            pts = [(x0, y0 + 200), (x0 + 380, y0), (x0 + 760, y0 + 200), (x0 + 380, y0 + 400)]
            d.polygon(pts, outline=L + (int(255 * a),))
            for p in pts: d.line([p, (p[0], p[1] + 220)], fill=L + (int(200 * a),), width=2)
            d.line([(x0, y0 + 420), (x0 + 380, y0 + 620), (x0 + 760, y0 + 420)], fill=L + (int(200 * a),), width=2)
            paste(fr, text_img("REPLICA — AS DESCRIBED BY NOTARBARTOLO", font(F_OSW_B, 26), L, tracking=4), x0 + 380, y0 + 700, "cm", a)
            steps = ["COMBINATION", "DOOR + KEY", "HEAT SENSOR", "LIGHT SENSOR", "MAGNETIC SENSOR", "BOX LOCKS"]
            for i, s in enumerate(steps):
                t0 = 0.8 + i * (self.cue(0, 1.0) - 0.8) / len(steps)
                sa = ramp(t, t0, 0.4)
                y = 260 + i * 88
                d.rectangle([1250, y - 18, 1286, y + 18], outline=L + (int(255 * sa),), width=3)
                if t > t0 + 0.4:
                    d.line([(1256, y), (1266, y + 12), (1284, y - 14)], fill=(255, 210, 120, 255), width=5)
                paste(fr, text_img(s, font(F_OSW_B, 34), L, tracking=4), 1310, y, "lm", sa)
            tl = text_img("REHEARSE  ·  REPEAT  ·  IN NEAR SILENCE", font(F_OSW, 24), (255, 210, 120), tracking=4)
            paste(fr, tl, 1250, 840, "lm", ramp(t, self.cue(0, 0.8), 0.8))
        fr = kb_transform(fr, ease_in_out(self.u(t)), 1.0, 1.06).convert("RGBA")
        return self.post(fr, t, dust=False, vig=0.55)


# ───────────────────────── HIGHWAY NIGHT ─────────────────────────
@scene("highway")
class Highway(Base):
    def setup(self):
        self.escape = self.p.get("variant") == "escape"
        sky = np.zeros((H, W, 3), np.float32); g = np.linspace(0, 1, H)[:, None]
        sky[:] = (np.array([3, 4, 8]) + np.array([22, 26, 40]) * (g * 1.9).clip(0, 1) ** 2)[:, None, :]
        self.sky = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert("RGBA")
        self.trees = forest_layer(W * 2, H, 31, 60, 60, 140, int(H * 0.535), (5, 6, 9, 255), 3, 6)
        self.vp = (W / 2, H * 0.53)
    def frame(self, t):
        fr = self.sky.copy()
        tx = int((t * 18) % W); fr.alpha_composite(self.trees.crop((tx, 0, tx + W, H)))
        d = ImageDraw.Draw(fr, "RGBA"); vx, vy = self.vp
        f = 700; hcam = 1.3; spd = 22 if not self.escape else 28
        def P(x, z): return (vx + f * x / z, vy + f * hcam / z)
        # road surface
        d.polygon([P(-6, 400), P(6, 400), P(6, 1.0), P(-6, 1.0)], fill=(14, 15, 18, 255))
        # headlight pool
        gl = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
        gd.polygon([(x / 4, y / 4) for x, y in [P(-2.4, 30), P(2.4, 30), P(3.5, 2), P(-3.5, 2)]], fill=(200, 190, 160, 34))
        zoff = (t * spd) % 12
        for k in range(40):
            z = 2 + k * 12 - zoff
            if z < 1.2: continue
            for lx in (-2.0, 2.0):
                a, b = P(lx - 0.07, z), P(lx + 0.07, z + 4)
                c = int(170 * clamp(1 - z / 300) + 20)
                d.polygon([P(lx - 0.07, z), P(lx + 0.07, z), P(lx + 0.07, z + 4), P(lx - 0.07, z + 4)], fill=(c, c, c - 10, 255))
            for sx in (-6.4, 6.4):  # reflector posts
                px, py = P(sx, z)
                hh = f * 1.0 / z
                d.line([(px, py), (px, py - hh)], fill=(40, 40, 44, 255), width=max(1, int(30 / z)))
                rc = (250, 140, 40) if sx > 0 else (240, 240, 240)
                gd.ellipse([px / 4 - 2, (py - hh * 0.9) / 4 - 2, px / 4 + 2, (py - hh * 0.9) / 4 + 2], fill=rc + (int(255 * clamp(8 / z)),))
        # edge lines
        d.line([P(-5.6, 400), P(-5.6, 1.0)], fill=(120, 120, 110, 255), width=3); d.line([P(5.6, 400), P(5.6, 1.0)], fill=(120, 120, 110, 255), width=3)
        if not self.escape:
            # overhead sodium lights passing
            loff = (t * spd) % 40
            for k in range(8):
                z = 3 + k * 40 - loff
                if z < 1.5: continue
                px, py = P(7.5, z); top = vy - f * 6 / z
                d.line([(px, py), (px, top)], fill=(30, 30, 34, 255), width=max(1, int(40 / z)))
                gd.ellipse([px / 4 - 60 / z - 2, top / 4 - 30 / z - 2, px / 4 + 2, top / 4 + 30 / z + 2], fill=(255, 150, 60, 230))
        # tail lights ahead
        zt = 60 + 15 * math.sin(t * 0.25) if not self.escape else 45 + 8 * math.sin(t * 0.4)
        for lx in (-0.45, 0.45):
            px, py = P(lx + 1.0, zt); py -= f * 0.6 / zt
            gd.ellipse([px / 4 - 2.5, py / 4 - 1.5, px / 4 + 2.5, py / 4 + 1.5], fill=(255, 30, 20, 255))
            d.ellipse([px - 4, py - 3, px + 4, py + 3], fill=(255, 60, 40, 255))
        g = gl.filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
        fr.alpha_composite(g); fr.alpha_composite(g)
        # windshield frame / dash silhouette for POV
        d2 = ImageDraw.Draw(fr); d2.rectangle([0, H * 0.9, W, H], fill=(3, 3, 4, 255))
        fr = Image.fromarray(np.asarray(fr)).filter(ImageFilter.GaussianBlur(0.8))
        return self.post(fr, t, dust=False)


# ───────────────────────── FOREST ─────────────────────────
@scene("forest")
class Forest(Base):
    def setup(self):
        v = self.p.get("variant", "plain"); self.v = v
        PW = W + 500; self.PW = PW
        night = v == "night"
        sky = np.zeros((H, PW, 3), np.float32); g = np.linspace(0, 1, H)[:, None]
        if night:
            sky[:] = (np.array([4, 6, 12]) + np.array([14, 18, 30]) * g)[:, None, :]
        else:
            sky[:] = (np.array([120, 130, 142]) - np.array([40, 40, 36]) * g)[:, None, :]
        self.sky = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert("RGBA")
        cols = [(70, 78, 90), (44, 50, 60), (18, 20, 24)] if not night else [(16, 20, 30), (10, 12, 18), (4, 5, 7)]
        self.layers = [forest_layer(PW, H, 40 + i, n, hmn, hmx, gy, c + (255,), wmn, wmx)
                       for i, (n, hmn, hmx, gy, c, wmn, wmx) in enumerate([(40, 300, 520, int(H * 0.72), cols[0], 6, 12),
                                                                         (22, 500, 800, int(H * 0.80), cols[1], 12, 22),
                                                                         (8, 900, 1300, int(H * 0.97), cols[2], 30, 55)])]
        fog = smooth_noise(PW * 2, H, 220, 9, 3)
        fa = np.zeros((H, PW * 2, 4), np.uint8); fa[..., :3] = (150, 158, 168) if not night else (40, 50, 70)
        fa[..., 3] = (np.clip(fog - 0.3, 0, 1) * (140 if not night else 90)).astype(np.uint8)
        self.fog = Image.fromarray(fa, "RGBA")
        # ground litter / trash
        self.trash = None
        if v == "trash" or night:
            rng = random.Random(5)
            tr = Image.new("RGBA", (PW, H), (0, 0, 0, 0)); d = ImageDraw.Draw(tr)
            gy = int(H * 0.80)
            for i in range(5):  # garbage bags
                x = 700 + i * 120 + rng.uniform(-30, 30); w_ = rng.uniform(130, 190); h_ = rng.uniform(90, 140)
                d.ellipse([x, gy - h_ + 20, x + w_, gy + 25], fill=(8, 8, 9, 255))
                d.arc([x + 15, gy - h_ + 30, x + w_ - 20, gy], 200, 280, fill=(90, 90, 96, 255), width=4)
                d.polygon([(x + w_ / 2 - 8, gy - h_ + 26), (x + w_ / 2, gy - h_ - 8), (x + w_ / 2 + 8, gy - h_ + 26)], fill=(8, 8, 9, 255))
            for i in range(40):  # papers/envelopes
                x = rng.uniform(560, 1500); y = rng.uniform(gy - 10, gy + 70); w_, h_ = rng.uniform(30, 70), rng.uniform(16, 34)
                c = rng.randint(170, 220); d.rectangle([x, y, x + w_, y + h_], fill=(c, c - 4, c - 14, 255))
                if rng.random() < 0.6: d.line([(x, y), (x + w_ / 2, y + h_ * 0.6), (x + w_, y)], fill=(120, 110, 100, 255), width=2)
            self.trash = tr
    def frame(self, t):
        u = ease_in_out(self.u(t))
        fr = self.sky.crop((int(60 * u), 0, int(60 * u) + W, H)).copy()
        for i, lay in enumerate(self.layers):
            ox = int((100 + 160 * i) * u)
            if i == 2 and self.trash is not None: fr.alpha_composite(self.trash.crop((int(130 * u), 0, int(130 * u) + W, H)))
            fr.alpha_composite(lay.crop((ox, 0, ox + W, H)))
            if i < 2:
                fx = int((t * (14 + 10 * i) + 400 * i) % self.PW); fr.alpha_composite(self.fog.crop((fx, 0, fx + W, H)))
        arr = np.asarray(fr, np.float32)[..., :3]
        if self.v == "night":
            # headlights sweeping through trunks from the right
            hx = W * (0.95 - 0.25 * u)
            arr = arr + radial(W, H, hx, H * 0.7, 900)[..., None] ** 2 * np.array([140, 120, 80])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"), t, dust=False)


# ───────────────────────── SENSOR ROOM ─────────────────────────
@scene("sensors")
class Sensors(Base):
    def setup(self):
        img = Image.new("RGBA", (W, H), (6, 7, 9, 255)); d = ImageDraw.Draw(img)
        self.vp = vp = (W / 2, H * 0.46)
        bw = (700, 250, 1220, 690)  # back wall
        d.rectangle(bw, fill=(20, 22, 26, 255))
        d.polygon([(0, 0), (bw[0], bw[1]), (bw[0], bw[3]), (0, H)], fill=(14, 15, 18, 255))
        d.polygon([(W, 0), (bw[2], bw[1]), (bw[2], bw[3]), (W, H)], fill=(14, 15, 18, 255))
        d.polygon([(0, H), (bw[0], bw[3]), (bw[2], bw[3]), (W, H)], fill=(18, 19, 22, 255))
        for k in range(-12, 13):
            d.line([(W / 2 + k * 160, H), (vp[0] + k * 22, bw[3])], fill=(34, 36, 42, 255), width=2)
        for k in range(8):
            y = bw[3] + (H - bw[3]) * (k / 8) ** 1.8
            x0 = lerp(bw[0], 0, (y - bw[3]) / (H - bw[3])); x1 = lerp(bw[2], W, (y - bw[3]) / (H - bw[3]))
            d.line([(x0, y), (x1, y)], fill=(34, 36, 42, 255), width=2)
        door = vault_door(400); img.alpha_composite(door, (int(W / 2 - 200), 270))
        self.room = img
    def frame(self, t):
        fr = self.room.copy()
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
        heat_off = t > self.cue(1, 0.6); light_off = t > self.cue(2, 0.6); mag_off = t > self.cue(3, 0.85)
        # IR beams
        if not heat_off or int(t * 10) % 7 == 0 and t < self.cue(1, 0.9):
            for k in range(6):
                y1 = 520 + k * 60 + 6 * math.sin(t * 2 + k); y2 = 560 + k * 52
                g.line([(0, y1), (W, y2)], fill=(255, 30, 30, 160), width=3)
        # radar arcs
        pr = (t * 0.6) % 1.0
        for k in range(3):
            rr = ((pr + k / 3) % 1.0) * 900
            g.arc([W / 2 - rr, 130 - rr * 0.5, W / 2 + rr, 130 + rr * 0.5], 10, 170, fill=(120, 200, 255, int(120 * (1 - rr / 900))), width=3)
        frg = gl.filter(ImageFilter.GaussianBlur(5)); fr.alpha_composite(frg); fr.alpha_composite(gl)
        d = ImageDraw.Draw(fr, "RGBA")
        def sensor(x, y, label, sub, t0, off, col):
            a = ramp(t, t0, 0.5)
            if a <= 0: return
            c = (90, 220, 120) if off else col
            d.rectangle([x - 22, y - 14, x + 22, y + 14], fill=(40, 42, 46, 255), outline=c + (255,), width=3)
            if not off and int(t * 3) % 2 == 0: d.ellipse([x + 10, y - 6, x + 18, y + 2], fill=col + (255,))
            paste(fr, text_img(label, font(F_OSW_B, 28), WHITE, tracking=4), x + 40, y - 14, "lm", a)
            paste(fr, text_img(sub, font(F_OSW, 22), c, tracking=3), x + 40, y + 18, "lm", a)
        sensor(260, 240, "HEAT SENSOR", "CLAIM: HAIRSPRAY COATING" if heat_off else "INFRARED — ACTIVE", self.cue(1, 0.0), heat_off, (255, 80, 70))
        sensor(1180, 150, "LIGHT SENSOR", "CLAIM: COVERED WITH TAPE" if light_off else "ACTIVE", self.cue(2, 0.0), light_off, (255, 80, 70))
        sensor(1300, 520, "MAGNETIC SENSOR", "CLAIM: HELD SHUT — ALUMINUM PLATE" if mag_off else "DOOR CIRCUIT — ACTIVE", self.cue(3, 0.0), mag_off, (255, 80, 70))
        fr = kb_transform(fr, ease_in_out(self.u(t)), 1.0, 1.08, (0.5, 0.5), (0.52, 0.46)).convert("RGBA")
        return self.post(fr, t)


# ───────────────────────── KEY ─────────────────────────
@scene("key")
class KeyScene(Base):
    def setup(self):
        self.bg = rgba(bg_plate(W, H, 120, (5, 5, 6), (40, 32, 22), 0.6, 0.35, 0.05))
        bk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(bk); rng = random.Random(2)
        for i in range(25):
            x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 80)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 140, rng.randint(8, 25)))
        self.bg.alpha_composite(bk.filter(ImageFilter.GaussianBlur(10)))
        self.key = big_key(1300)
    def frame(self, t):
        u = ease_in_out(self.u(t))
        fr = self.bg.copy()
        k = self.key.rotate(-18 + 8 * u, expand=True, resample=Image.BICUBIC)
        s = 1.0 + 0.12 * u
        k = k.resize((int(k.size[0] * s), int(k.size[1] * s)), Image.BILINEAR)
        sh = Image.new("RGBA", k.size, (0, 0, 0, 0)); sh.putalpha(k.getchannel("A").point(lambda v: v * 0.7))
        paste(fr, sh.filter(ImageFilter.GaussianBlur(18)), W / 2 + 30, H * 0.47 + 40, "cm")
        paste(fr, k, W / 2, H * 0.45, "cm", ramp(t, 0, 0.8))
        arr = light_sweep(np.asarray(fr, np.float32)[..., :3], t, period=max(6, self.dur), width=0.12, strength=0.7)
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"), t)


# ───────────────────────── TIMELINE ─────────────────────────
@scene("timeline")
class Timeline(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 130, (8, 9, 12), (24, 28, 36), 0.5, 0.3, 0.05))
        if self.p["mode"] == "weekend":
            self.ev = [("SAT 15 FEB", "WEEKEND BEGINS", "Offices closed", 0), ("SUN 16 FEB", "THE BREAK-IN", "Over the weekend", 1),
                       ("MON 17 FEB", "DISCOVERY", "Vault found open", 2), ("FRI 21 FEB", "ARREST", "Notarbartolo detained", 3)]
            self.times = [self.cue(0, 0.15), self.cue(0, 0.45), self.cue(1, 0.05), self.cue(1, 0.55)]
            self.hl = None
        else:
            self.ev = [("15–16 FEB", "THE BREAK-IN", "", 0), ("17 FEB", "DISCOVERY", "", 1), ("21 FEB 2003", "ARREST", "Notarbartolo returns to the centre", 2), ("2005", "SENTENCED", "", 3)]
            self.times = [0.2, 0.5, self.cue(0, 0.1), self.cue(1, 0.9)]
            self.hl = 2
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.04).convert("RGBA"); d = ImageDraw.Draw(fr, "RGBA")
        x0, x1, y = 220, 1700, 520
        la = ease_out(ramp(t, 0.0, 1.5))
        d.line([(x0, y), (lerp(x0, x1, la), y)], fill=(120, 128, 140, 255), width=3)
        n = len(self.ev)
        for i, (date, title, sub, _) in enumerate(self.ev):
            x = lerp(x0 + 80, x1 - 80, i / (n - 1)); a = ramp(t, self.times[i], 0.5)
            if a <= 0: continue
            hot = (self.hl == i) or (self.hl is None and i == max([j for j in range(n) if t >= self.times[j]] or [0]))
            col = GOLD if hot else (150, 156, 166)
            r = 14 if hot else 10
            d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(255 * a),))
            if hot:
                pul = (t * 0.8) % 1; rr = r + 30 * pul
                d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col + (int(200 * (1 - pul)),), width=2)
            paste(fr, text_img(date, font(F_BEBAS, 58), col, tracking=4), x, y - 70, "cm", a)
            paste(fr, text_img(title, font(F_OSW_B, 28), WHITE, tracking=5), x, y + 60, "cm", a)
            if sub: paste(fr, text_img(sub.upper(), font(F_OSW, 20), DIM, tracking=3), x, y + 98, "cm", a)
        paste(fr, text_img("2003", font(F_BEBAS, 34), DIM, tracking=10), W / 2, 300, "cm", ramp(t, 0.2, 0.8))
        return self.post(fr, t, tagtxt="TIMELINE", dust=False)


# ───────────────────────── BAR COMPARISON ─────────────────────────
@scene("bars")
class Bars(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 140, (8, 9, 12), (26, 28, 34), 0.3, 0.3, 0.05))
        if self.p["mode"] == "boxes":
            self.title = "SAFE-DEPOSIT BOXES OPENED — REPORTED FIGURES"
            self.bars = [("LOW ESTIMATE", 109, "109", (150, 160, 175)), ("HIGH ESTIMATE", 123, "123", GOLD), ("TOTAL BOXES (REPORTED RANGE)", 189, "160–189", (80, 88, 100))]
            self.maxv = 200; self.times = [self.cue(0, 0.1), self.cue(0, 0.3), self.cue(0, 0.62)]
            self.note = "Sources disagree. Figures shown as reported in different accounts."
        else:
            self.title = "VALUE OF THE HAUL — COMPETING CLAIMS"
            self.bars = [("WIDELY REPORTED ESTIMATE", 100, "$100 MILLION", GOLD), ("NOTARBARTOLO'S CLAIM (2009)", 20, "~$20 MILLION  (€18M)", (180, 70, 60))]
            self.maxv = 110; self.times = [0.3, 1.0]
            self.note = "Neither figure has been independently verified in full."
    def frame(self, t):
        fr = self.plate.copy(); d = ImageDraw.Draw(fr, "RGBA")
        paste(fr, text_img(self.title, font(F_OSW_B, 34), WHITE, tracking=5), 200, 190, "lm", ramp(t, 0.0, 0.6))
        x0, x1 = 200, 1720
        for i, (lab, v, txt, col) in enumerate(self.bars):
            y = 330 + i * 170; a = ramp(t, self.times[i], 0.4); g = ease_out(clamp((t - self.times[i]) / 1.4))
            if a <= 0: continue
            paste(fr, text_img(lab, font(F_OSW, 24), DIM, tracking=4), x0, y - 30, "lm", a)
            w = (x1 - x0) * v / self.maxv * g
            d.rectangle([x0, y, x0 + w, y + 64], fill=col + (int(235 * a),))
            paste(fr, text_img(txt, font(F_BEBAS, 62), WHITE, tracking=3), x0 + w + 24, y + 32, "lm", a * g)
        paste(fr, text_img(self.note, font(F_INTER, 22), DIM), 200, 860, "lm", ramp(t, 1.5, 0.8))
        return self.post(fr, t, tagtxt="DATA", dust=False)


# ───────────────────────── SPLIT: TWO VERSIONS ─────────────────────────
@scene("split")
class Split(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 150, (8, 9, 12), (26, 26, 30), 0.5, 0.3, 0.05))
        self.L = ["Convicted of organizing the robbery (2005)", "Sentenced to 10 years", "Most of the loot never recovered"]
        self.R = ["Says a diamond merchant hired the crew", "Says it was an insurance fraud", "Says the haul was only ~€18M (~$20M)"]
        self.rt = [self.cue(1, 0.1), self.cue(2, 0.1), self.cue(3, 0.2)]
    def frame(self, t):
        fr = self.plate.copy(); d = ImageDraw.Draw(fr, "RGBA")
        a0 = ramp(t, 0.1, 0.6)
        d.line([(W / 2, 200), (W / 2, 200 + 620 * ease_out(a0))], fill=(100, 104, 112, 255), width=2)
        paste(fr, text_img("THE COURT'S FINDINGS", font(F_BEBAS, 62), (170, 180, 195), tracking=5), W * 0.27, 240, "cm", a0)
        paste(fr, text_img("NOTARBARTOLO'S CLAIMS", font(F_BEBAS, 62), GOLD, tracking=5), W * 0.73, 240, "cm", ramp(t, self.cue(0, 0.4), 0.6))
        paste(fr, text_img("UNVERIFIED", font(F_OSW, 22), (220, 110, 100), tracking=8), W * 0.73, 290, "cm", ramp(t, self.cue(0, 0.6), 0.6))
        for i, s in enumerate(self.L):
            a = ramp(t, 0.4 + 0.35 * i, 0.5)
            for j, ln in enumerate(wrap_text(s, font(F_INTER_M, 32), 640)):
                paste(fr, text_img(ln, font(F_INTER_M, 32), WHITE), 170, 390 + i * 140 + j * 42, "lm", a)
        for i, s in enumerate(self.R):
            a = ramp(t, self.rt[i], 0.5)
            for j, ln in enumerate(wrap_text(s, font(F_INTER_M, 32), 640)):
                paste(fr, text_img(ln, font(F_INTER_M, 32), WHITE), W / 2 + 130, 390 + i * 140 + j * 42, "lm", a)
        return self.post(fr, t, tagtxt="", dust=False)


# ───────────────────────── EVIDENCE BOARD ─────────────────────────
def ev_card(kind, title, sub, seed):
    w, h = 400, 470
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([24, 28, w + 24, h + 28], fill=(0, 0, 0, 160)); im = im.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(im)
    d.rectangle([14, 14, w + 14, h + 14], fill=(232, 228, 216, 255))
    ix0, iy0, ix1, iy1 = 38, 38, w - 10, 330
    d.rectangle([ix0, iy0, ix1, iy1], fill=(26, 28, 32, 255))
    cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    if kind == "envelope":
        for k, (dx, dy, rot) in enumerate([(-40, -20, -8), (30, 25, 6)]):
            e = Image.new("RGBA", (220, 140), (0, 0, 0, 0)); ed = ImageDraw.Draw(e)
            ed.rectangle([0, 0, 219, 139], fill=(214, 200, 170, 255), outline=(120, 100, 70, 255), width=2)
            ed.line([(0, 0), (110, 80), (219, 0)], fill=(140, 120, 90, 255), width=3)
            ed.line([(150, 0), (200, 139)], fill=(26, 28, 32, 255), width=6)  # torn
            e = e.rotate(rot, expand=True, resample=Image.BICUBIC); im.alpha_composite(e, (int(cx + dx - e.size[0] / 2), int(cy + dy - e.size[1] / 2)))
    elif kind == "documents":
        for k in range(3):
            e = Image.new("RGBA", (170, 220), (0, 0, 0, 0)); ed = ImageDraw.Draw(e)
            ed.rectangle([0, 0, 169, 219], fill=(225, 222, 210, 255), outline=(150, 150, 140, 255))
            for ln in range(10): ed.line([(16, 24 + ln * 18), (150 - (ln % 3) * 20, 24 + ln * 18)], fill=(120, 120, 120, 255), width=3)
            e = e.rotate(-12 + k * 12, expand=True, resample=Image.BICUBIC); im.alpha_composite(e, (int(cx - 140 + k * 70 - e.size[0] / 2 + 70), int(cy - e.size[1] / 2)))
    elif kind == "sandwich":
        d.pieslice([cx - 150, cy - 70, cx + 150, cy + 110], 180, 360, fill=(200, 150, 90, 255))
        d.rectangle([cx - 150, cy + 18, cx + 150, cy + 34], fill=(150, 60, 60, 255))
        for k in range(6): d.ellipse([cx - 130 + k * 48, cy + 14, cx - 96 + k * 48, cy + 38], fill=(185, 80, 80, 255), outline=(230, 200, 190, 255))
        d.rectangle([cx - 150, cy + 34, cx + 150, cy + 64], fill=(215, 170, 110, 255))
        d.ellipse([cx + 70, cy - 60, cx + 200, cy + 80], fill=(26, 28, 32, 255))  # bite
    else:
        d.ellipse([cx - 60, cy - 90, cx + 60, cy + 30], fill=(10, 10, 12, 255)); d.pieslice([cx - 120, cy + 20, cx + 120, cy + 200], 180, 360, fill=(10, 10, 12, 255))
        d.text((cx, cy - 30), "?", font=font(F_BEBAS, 90), fill=(200, 170, 80, 255), anchor="mm")
    d.text((38, 350), title, font=font(F_OSW_B, 30), fill=(30, 28, 26, 255))
    for j, ln in enumerate(wrap_text(sub, font(F_TYPE, 22), w - 50)):
        d.text((38, 395 + j * 28), ln, font=font(F_TYPE, 22), fill=(80, 70, 60, 255))
    return im.rotate(random.Random(seed).uniform(-5, 5), expand=True, resample=Image.BICUBIC)


@scene("evidence")
class Evidence(Base):
    def setup(self):
        n = smooth_noise(W + 300, H + 200, 3, 8, 2)
        arr = np.array([26, 30, 28], np.float32) * (0.75 + 0.5 * n)[..., None]
        self.board = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
        self.cards = [ev_card("envelope", "ENVELOPES", "Marked with the Antwerp Diamond Centre's name", 1),
                      ev_card("documents", "DOCUMENTS & ITEMS", "Traced to the people who dumped them", 2),
                      ev_card("sandwich", "SALAMI SANDWICH", "Half-eaten. Carried DNA.", 3),
                      ev_card("suspect", "THE SUSPECTS", "Leads pointed to Notarbartolo", 4)]
        self.pos = [(470, 420), (1110, 390), (1750, 440), (1110, 990)]
        self.cards = [c.resize((int(c.size[0] * 0.85), int(c.size[1] * 0.85)), Image.LANCZOS) for c in self.cards]
        self.focus = self.p.get("focus")
        if self.focus is None:
            self.ct = [self.cue(1, 0.05), self.cue(2, 0.05), self.cue(3, 0.15), self.cue(3, 0.8)]
        else:
            self.ct = [-1, -1, -1, self.cue(1, 0.1)]
    def frame(self, t):
        fr = self.board.copy(); d = ImageDraw.Draw(fr, "RGBA")
        paste(fr, text_img("RECOVERED NEAR THE E19  ·  17 FEBRUARY 2003", font(F_OSW_B, 30), (210, 205, 195), tracking=6), (W + 300) / 2, 120, "cm", ramp(t, 0.2, 0.8))
        for i, c in enumerate(self.cards):
            a = ramp(t, self.ct[i], 0.4) if self.ct[i] >= 0 else 1.0
            if a <= 0: continue
            x, y = self.pos[i]
            s = 1.15 - 0.15 * ease_out(a)
            cc = c if s == 1 else c.resize((int(c.size[0] * s), int(c.size[1] * s)), Image.BILINEAR)
            paste(fr, cc, x, y, "cm", a)
            d.ellipse([x - 12, y - c.size[1] / 2 + 6, x + 12, y - c.size[1] / 2 + 30], fill=(190, 40, 30, int(255 * a)))
        # strings to suspects
        sx, sy = self.pos[3]
        for i in range(3):
            st = ramp(t, max(self.ct[3], 0) + 0.3 + i * 0.25, 0.8) if (self.ct[3] >= 0 and t > self.ct[3]) else 0
            if st <= 0: continue
            x, y = self.pos[i]; y -= self.cards[i].size[1] / 2 - 18
            ex, ey = lerp(x, sx, st), lerp(y, sy - 200, st)
            d.line([(x, y), (ex, ey)], fill=(200, 40, 30, 230), width=4)
        if self.focus is None:
            fr = kb_transform(fr, ease_in_out(self.u(t)), 1.0, 1.10).convert("RGBA")
        else:
            p = self.pos[self.focus]; cx, cy = p[0] / (W + 300), p[1] / (H + 200)
            fr = kb_transform(fr, ease_in_out(clamp(self.u(t) * 1.6)), 1.0, 2.0, (0.5, 0.5), (cx, cy + 0.05)).convert("RGBA")
        arr = np.asarray(fr, np.float32)[..., :3] * (0.55 + 0.6 * radial(W, H, W * 0.5, H * 0.35, W * 0.8)[..., None])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"), t)


# ───────────────────────── QUESTIONS ─────────────────────────
@scene("questions")
class Questions(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W + 200, H + 120, 160, (6, 6, 8), (30, 22, 20), 0.5, 0.4))
        self.q = ["$100 MILLION — OR $20 MILLION?", "A THEFT — OR A FRAUD?", "WHO WAS THE KING OF KEYS?", "WHO STOOD BEHIND THE CREW?"]
        self.imgs = [text_img(q, font(F_BEBAS, 88), WHITE, tracking=5) for q in self.q]
        self.gimgs = [glow(text_img(q, font(F_BEBAS, 88), GOLD, tracking=5), 16, 0.5) for q in self.q]
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.08).convert("RGBA")
        cur = max([i for i in range(4) if t >= self.cue(i, 0) - 0.1] or [0])
        for i in range(4):
            a = ramp(t, self.cue(i, 0) - 0.1, 0.5)
            if a <= 0: continue
            y = 260 + i * 140
            im = self.gimgs[i] if i == cur else self.imgs[i]
            paste(fr, im, W / 2, y, "cm", a * (1.0 if i == cur else 0.35))
        return self.post(fr, t, tagtxt="")


# ───────────────────────── END CARD ─────────────────────────
@scene("end")
class End(Base):
    def setup(self):
        self.plate = rgba(bg_plate(W, H, 170, (5, 5, 6), (24, 24, 28), 0.5, 0.4))
        logo = Image.open(os.path.join(ROOT, "assets", "war_files_logo_transparent.png")).convert("RGBA")
        self.logo = logo.resize((440, 440), Image.LANCZOS)
        self.t1 = text_img("SOURCES & CREDITS IN THE DESCRIPTION", font(F_OSW, 26), DIM, tracking=6)
        self.t2 = text_img("SUBSCRIBE FOR THE NEXT FILE", font(F_OSW_B, 30), GOLD, tracking=8)
    def frame(self, t):
        fr = self.plate.copy()
        a = ramp(t, 0.2, 1.2) * (1 - ramp(t, self.dur - 1.2, 1.1))
        s = 1.0 + 0.04 * self.u(t)
        lg = self.logo.resize((int(440 * s), int(440 * s)), Image.LANCZOS)
        gl = Image.new("RGBA", (700, 700), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([130, 130, 570, 570], fill=GOLD + (60,))
        paste(fr, gl.filter(ImageFilter.GaussianBlur(60)), W / 2, H * 0.40, "cm", a)
        paste(fr, lg, W / 2, H * 0.40, "cm", a)
        paste(fr, self.t2, W / 2, H * 0.70, "cm", a * ramp(t, self.cue(1, 0), 0.8))
        paste(fr, self.t1, W / 2, H * 0.755, "cm", a * ramp(t, 1.5, 0.8))
        return self.post(fr, t, tagtxt="")
