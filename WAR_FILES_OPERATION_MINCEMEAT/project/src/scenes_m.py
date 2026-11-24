"""Scene renderers for 'The Dead Man Who Fooled Hitler'. Each class: __init__(dur, cues, p) ; frame(t) -> RGBA PIL image."""
import os, json, math, random, functools, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from common import *
from props import diamond  # noqa (kept for parity)
from world import *

REG = {}
def scene(name):
    def deco(c): REG[name] = c; return c
    return deco

ARCH = os.path.join(ROOT, "assets", "archival")
CREDITS = json.load(open(os.path.join(ARCH, "credits.json"))) if os.path.exists(os.path.join(ARCH, "credits.json")) else {}


def label(fr, text, opacity=1.0):
    """top-left provenance label (ARCHIVAL PHOTO / RECREATION / ILLUSTRATION / MAP ...)"""
    if not text: return fr
    f = font(F_OSW, 20); ti = text_img(text, f, (228, 224, 214), tracking=3); w, h = ti.size
    box = Image.new("RGBA", (w + 28, h + 8), (0, 0, 0, 110)); ImageDraw.Draw(box).rectangle([0, 0, 2, h + 8], fill=GOLD + (255,))
    box.alpha_composite(ti, (16, 2)); paste(fr, box, 54, 46, opacity=0.9 * opacity); return fr


def credit(fr, text, opacity=1.0):
    """top-right archival credit"""
    if not text: return fr
    lines = wrap_text(text, font(F_INTER, 19), 640)
    y = 48
    for ln in lines:
        ti = text_img(ln, font(F_INTER, 19), (222, 220, 212))
        sh = Image.new("RGBA", (ti.size[0] + 20, ti.size[1] + 6), (0, 0, 0, 105)); sh.alpha_composite(ti, (10, 1))
        paste(fr, sh, W - 54, y, "rt", 0.92 * opacity); y += ti.size[1] + 6
    return fr


def name_tag(fr, name, sub, a):
    if a <= 0 or not name: return
    paste(fr, text_img(name, font(F_BEBAS, 58), WHITE, tracking=5), 120 + 30 * (1 - a), 790, "lm", a)
    ImageDraw.Draw(fr).rectangle([96, 770, 100, 840], fill=GOLD + (int(255 * a),))
    if sub: paste(fr, text_img(sub, font(F_OSW, 24), (214, 200, 160), tracking=3), 122 + 30 * (1 - a), 836, "lm", a)


class Base:
    TAG = None
    def __init__(self, dur, cues, p):
        self.dur, self.cues, self.p = dur, cues, p
        self.alt = p.get("alt", 0)
        self.dust = Dust(26, seed=abs(hash(str(sorted(p.items())))) % 997)
        self.setup()
    def setup(self): pass
    def u(self, t): return clamp(t / max(self.dur, 1e-3))
    def post(self, fr, t, dust=False, tagtxt=None):
        if dust: self.dust.draw(fr, t, 0.6)
        label(fr, self.p.get("tag", self.TAG) if tagtxt is None else tagtxt)
        return fr


# ═════════════════════════ OCEAN ═════════════════════════
@scene("ocean")
class Ocean(Base):
    def setup(self):
        v = self.p.get("variant", "night"); self.v = v
        self.sky = Image.fromarray(sky_plate(v).astype(np.uint8)).convert("RGBA") if True else None
        skyfull = np.zeros((H, W, 3), np.float32); sp = sky_plate(v); skyfull[:sp.shape[0]] = sp
        self.skyarr = skyfull
        self.sea = Sea(v, seed=3 + self.alt, calm=0.6 if self.p.get("still") else 1.0)
        self.yh = int(H * HOR[v])
        self.coast = coast_layer(v, "left" if self.alt % 2 == 0 else "right", lights=v in ("night", "predawn")) if self.p.get("coast") else None
        silc = {"night": (6, 8, 12), "predawn": (16, 18, 26), "dawn": (40, 34, 40), "day": (40, 44, 50), "overcast": (50, 54, 58), "dusk": (30, 24, 34)}[v]
        self.silc = silc
        sub = self.p.get("sub")
        self.subs = None
        if sub:
            L = {"surface": 820, "close": 1500, "deck": 2600, "wake": 1100, "periscope": 0}[sub]
            self.subs = submarine_sprite(L, silc) if L else None
        self.boat = boat_sprite(220, silc) if self.p.get("boat") else None
        self.plane = plane_sprite(190, (70, 74, 80) if v == "overcast" else silc) if self.p.get("plane") else None
        self.speed = 0.45 if self.p.get("still") else 0.8
    def frame(self, t):
        u = self.u(t); tt = t * self.speed
        sea = self.sea.render(tt + self.alt * 7)
        sea_img = Image.fromarray(np.clip(sea, 0, 255).astype(np.uint8)).resize((W, H - self.yh), Image.BILINEAR)
        arr = self.skyarr.copy()
        arr[self.yh:] = np.asarray(sea_img, np.float32)
        # horizon haze
        hz = np.exp(-((np.arange(H) - self.yh) / 14.0) ** 2)[:, None, None]
        arr = arr * (1 - 0.35 * hz) + hz * 0.35 * self.skyarr[max(0, self.yh - 3)].mean(0)[None, None]
        fr = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
        if self.coast is not None: fr.alpha_composite(self.coast)
        bob = math.sin(tt * 1.3) * 4
        sub = self.p.get("sub")
        if sub and self.subs is not None:
            sw, sh = self.subs.size
            if sub == "surface":
                rise = ease_out(clamp(t / 4.5)); x = W * 0.52 - sw / 2 + 30 * u; y = self.yh + 70 - sh * 0.78 + (1 - rise) * sh * 0.5 + bob
            elif sub == "close":
                x = W * 0.5 - sw / 2 - 80 * u; y = self.yh + 150 - sh * 0.78 + bob
            elif sub == "deck":
                x = -sw * 0.2 - 120 * u; y = H * 0.64 - sh * 0.78 + bob * 1.5
            else:  # wake
                x = W * 0.45 - sw / 2 + 120 * u; y = self.yh + 90 - sh * 0.78 + bob
            crop_y = int(self.yh - y) if sub == "surface" else None
            spr = self.subs
            if sub == "surface" and rise < 1:   # hide submerged part below the waterline
                spr = self.subs.copy(); a = np.asarray(spr).copy(); wl_row = int(sh * 0.78 + (self.yh + 70 - sh * 0.78) - y) if False else int(sh * 0.78 - (1 - rise) * sh * 0.5)
                a[max(0, wl_row):, :, 3] = 0; spr = Image.fromarray(a, "RGBA")
            fr.alpha_composite(spr, (int(x), int(y)))
            # foam at waterline
            fd = ImageDraw.Draw(fr, "RGBA"); wl = y + sh * 0.78
            rng = random.Random(int(t * 12))
            for k in range(60):
                fx = x + rng.uniform(0, sw); fw = rng.uniform(10, 60)
                fd.line([(fx, wl + rng.uniform(-3, 6)), (fx + fw, wl + rng.uniform(-3, 6))], fill=(200, 210, 220, rng.randint(40, 120)), width=2)
            if sub == "wake":
                for k in range(120):
                    fx = x + sw * 0.98 + rng.uniform(0, 600); fy = wl + rng.uniform(-10, 60) * (1 + (fx - x - sw) / 600)
                    fd.line([(fx, fy), (fx + rng.uniform(20, 70), fy)], fill=(210, 220, 230, rng.randint(40, 150)), width=2)
            if sub == "deck":   # officers' silhouettes on the casing
                for k, ox in enumerate((0.40, 0.44, 0.47)):
                    px = x + sw * ox; py = wl - sw * 0.022
                    fd.ellipse([px - 9, py - 74, px + 9, py - 56], fill=self.silc + (255,)); fd.rectangle([px - 13, py - 58, px + 13, py], fill=self.silc + (255,))
        elif sub == "periscope":
            px = W * 0.56 + 60 * u; py = self.yh + 120
            d = ImageDraw.Draw(fr, "RGBA"); d.rectangle([px - 5, py - 70 + bob, px + 5, py + 4], fill=self.silc + (255,)); d.rectangle([px - 9, py - 78 + bob, px + 9, py - 66 + bob], fill=self.silc + (255,))
            rng = random.Random(int(t * 10))
            for k in range(40):
                fx = px - rng.uniform(0, 280); d.line([(fx, py + rng.uniform(-2, 8)), (fx + 30, py + rng.uniform(-2, 8))], fill=(230, 220, 210, rng.randint(40, 140)), width=2)
        if self.boat is not None:
            bx = W * 0.30 + 60 * u; by = self.yh + 40 - self.boat.size[1] * 0.86 + bob * 0.7
            fr.alpha_composite(self.boat.rotate(math.sin(tt * 1.1) * 3, expand=False, resample=Image.BICUBIC), (int(bx), int(by)))
        if self.plane is not None:
            px = -200 + (W + 400) * u; py = H * 0.18 + 20 * math.sin(u * 3)
            fr.alpha_composite(self.plane, (int(px), int(py)))
        return self.post(fr, t)


# ═════════════════════════ ARCHIVAL PHOTO ═════════════════════════
@functools.lru_cache(None)
def load_arch(key):
    meta = CREDITS[key]; im = Image.open(os.path.join(ARCH, meta["file"])).convert("RGB")
    if meta.get("crop"):
        w, h = im.size; c = meta["crop"]; im = im.crop((int(c[0] * w), int(c[1] * h), int(c[2] * w), int(c[3] * h)))
    if meta.get("bw", True):
        g = ImageOps.grayscale(im); g = ImageOps.autocontrast(g, cutoff=0.5)
        a = np.asarray(g, np.float32)[..., None] / 255
        tone = a * np.array([236, 228, 212]) + (1 - a) * np.array([14, 13, 12]) * 0.6
        im = Image.fromarray(tone.clip(0, 255).astype(np.uint8))
    return im, meta


@scene("photo")
class Photo(Base):
    def setup(self):
        self.im, self.meta = load_arch(self.p["key"])
        iw, ih = self.im.size
        self.mode = self.p.get("mode", "kb")
        if self.mode == "kb" and iw / ih < 1.25: self.mode = "framed"
        if self.mode == "kb":
            s = max(W / iw, H / ih) * 1.02
            self.plate = self.im.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
        else:
            bg = self.im.resize((W // 8, H // 8)).resize((W + 200, H + 120), Image.BILINEAR).filter(ImageFilter.GaussianBlur(14))
            bga = np.asarray(bg, np.float32) * 0.28
            self.bg = Image.fromarray(bga.astype(np.uint8)).convert("RGBA")
            s = min(860 / ih, 1300 / iw); self.ph = self.im.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
            pw, phh = self.ph.size
            card = Image.new("RGBA", (pw + 120, phh + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
            d.rectangle([60 + 14, 60 + 18, 60 + pw + 14, 60 + phh + 18], fill=(0, 0, 0, 170)); card = card.filter(ImageFilter.GaussianBlur(16))
            card.paste(self.ph, (60, 60)); self.card = card
        z = self.p.get("z", (1.0, 1.12)); self.z = z if not self.alt else (z[1], z[0])
        self.c0 = self.p.get("c0", (0.5, 0.5)); self.c1 = self.p.get("c1", (0.5, 0.5))
        if self.alt: self.c0, self.c1 = self.c1, (0.5 + (0.5 - self.c1[0]) * 0.6, self.c1[1])
        cr = self.meta.get("credit", ""); ex = self.p.get("credit_extra") or self.meta.get("caption", "")
        self.cred = (ex + "  ·  " if ex else "") + cr
    def frame(self, t):
        u = ease_in_out(self.u(t))
        if self.mode == "kb":
            fr = kb_transform(self.plate, u, self.z[0], self.z[1], self.c0, self.c1).convert("RGBA")
        else:
            fr = kb_transform(self.bg, u, 1.0, 1.04).convert("RGBA")
            s = lerp(self.z[0], self.z[1], u) * 0.98
            cw, ch = self.card.size; c = self.card.resize((int(cw * s), int(ch * s)), Image.BILINEAR)
            off = (self.c1[0] - 0.5) * 60 * u
            paste(fr, c, W / 2 + off, H * 0.46, "cm")
        arr = np.asarray(fr, np.float32)
        arr[..., :3] *= VIG[..., None] ** 0.6
        fr = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        name_tag(fr, self.p.get("name"), self.p.get("sub"), ramp(t, 0.5, 0.7) * (1 - ramp(t, self.dur - 0.6, 0.5)) if self.p.get("name") else 0)
        credit(fr, self.cred)
        return self.post(fr, t, tagtxt=self.meta.get("label", "ARCHIVAL PHOTO"))


# ═════════════════════════ MAPS ═════════════════════════
@functools.lru_cache(None)
def countries():
    tj = json.load(open("/home/user/npmassets/node_modules/world-atlas/countries-50m.json"))
    sc, tr = tj["transform"]["scale"], tj["transform"]["translate"]; arcs = []
    for arc in tj["arcs"]:
        x = y = 0; pts = []
        for dx, dy in arc: x += dx; y += dy; pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    def ring(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]; pts.extend(a[1:] if pts else a)
        return pts
    out = {}
    for g in tj["objects"]["countries"]["geometries"]:
        nm = g.get("properties", {}).get("name", "?")
        polys = [ring(g["arcs"][0])] if g["type"] == "Polygon" else ([ring(p[0]) for p in g["arcs"]] if g["type"] == "MultiPolygon" else [])
        polys = [np.array(p) for p in polys if any(-30 < q[0] < 50 and 25 < q[1] < 72 for q in p[::3] + [p[0]])]
        if polys: out[nm] = polys
    return out


def draw_map_into(img, cam, scale_unused=1, fill=(30, 34, 41), line=(78, 86, 98)):
    """small static map for wall props; cam=(lon,lat,scale px/deg)"""
    w, h = img.size; d = ImageDraw.Draw(img); cosl = math.cos(math.radians(45))
    cx, cy, s = cam[0], cam[1], w / 60
    for nm, polys in countries().items():
        for p in polys:
            xs = w / 2 + (p[:, 0] - cx) * cosl * s; ys = h / 2 - (p[:, 1] - cy) * s
            if len(xs) > 2: d.polygon(list(zip(xs.tolist(), ys.tolist())), fill=fill, outline=line)


PL = {"SICILY": (14.1, 37.55), "SARDINIA": (9.0, 40.05), "CORSICA": (9.1, 42.15), "GREECE": (22.0, 39.2), "CAPE ARAXOS": (21.38, 38.17),
      "KALAMATA": (22.11, 37.04), "DODECANESE": (27.2, 36.4), "TUNIS": (10.18, 36.8), "CAIRO": (31.24, 30.04), "SYRIA": (36.7, 34.8),
      "SALONIKA": (22.94, 40.64), "HUELVA": (-6.95, 37.26), "CÁDIZ": (-6.29, 36.53), "SAN FERNANDO": (-6.2, 36.46), "MADRID": (-3.70, 40.42),
      "BERLIN": (13.40, 52.52), "LONDON": (-0.13, 51.51), "GREENOCK": (-4.76, 55.95), "GIBRALTAR": (-5.35, 36.14), "TARIFA": (-5.6, 36.01),
      "PELOPONNESE": (22.2, 37.5), "ROME": (12.5, 41.9), "PARIS": (2.35, 48.85), "CASABLANCA": (-7.59, 33.57), "LISBON": (-9.14, 38.72)}
COUNTRY_LABELS = {"SPAIN": (-3.8, 39.6), "FRANCE": (2.4, 46.8), "ITALY": (12.6, 42.7), "GERMANY": (10.2, 51.0), "TUNISIA": (9.4, 34.4), "ALGERIA": (3.0, 33.0),
                  "LIBYA": (17.5, 28.5), "EGYPT": (29.5, 27.0), "TURKEY": (34.0, 39.0), "PORTUGAL": (-8.2, 39.7), "BRITAIN": (-1.8, 53.2), "MOROCCO": (-6.5, 32.0),
                  "MEDITERRANEAN SEA": (18.0, 34.4), "ATLANTIC OCEAN": (-14.5, 42.0), "IRELAND": (-8.0, 53.2)}
MAPS = {  # mode: (cam0, cam1)  cam=(lon, lat, px/deg)
    "europe_dark": ((8, 46, 34), (2, 41, 52)), "huelva": ((-5.0, 38.0, 140), (-6.8, 37.2, 420)), "docs_path": ((-2.0, 39.5, 120), (-1.0, 40.0, 110)),
    "med_1943": ((14, 38, 40), (12, 37, 48)), "channel": ((0, 50, 80), (0.5, 49.8, 95)), "two_choices": ((17, 38, 60), (17, 38.2, 64)),
    "sicily_zoom": ((14, 38, 60), (13.2, 37.3, 210)), "sicily_obvious": ((12.5, 36.8, 170), (12.6, 36.9, 185)), "barclay": ((27, 35, 52), (27.5, 34.5, 58)),
    "cadiz": ((-6.0, 37.0, 160), (-6.0, 36.6, 230)), "fake_targets": ((17, 38.5, 58), (18, 38.5, 64)), "sardinia": ((10, 40.5, 110), (9.2, 40.1, 160)),
    "currents": ((-7.4, 36.9, 300), (-7.1, 37.05, 380)), "london_greenock": ((-2.5, 53.7, 120), (-3.0, 54.0, 128)), "seraph_route": ((-6.5, 46.5, 34), (-7.0, 45.5, 38)),
    "madrid_berlin": ((5, 46, 40), (6, 46.5, 44)), "reinforce": ((16, 41, 46), (17, 40.5, 52)), "aircraft": ((11.5, 38.8, 120), (11.8, 38.8, 140)),
    "wrong_way": ((16, 39, 52), (16, 38.5, 58)),
}


@scene("map")
class MapScene(Base):
    TAG = "MAP"
    def setup(self):
        self.C = countries(); self.mode = self.p["mode"]
        self.sea = bg_plate(W, H, 61, (9, 13, 19), (20, 28, 38), 0.4, 0.3, 0.05).convert("RGBA")
        self.c0, self.c1 = MAPS[self.mode]
        if self.alt: self.c0, self.c1 = self.c1, self.c0
    def P(self, lon, lat, cam):
        cosl = math.cos(math.radians(cam[1]))
        return (W / 2 + (lon - cam[0]) * cosl * cam[2], H / 2 - (lat - cam[1]) * cam[2])
    def frame(self, t):
        u = ease_in_out(self.u(t)); c0, c1 = self.c0, self.c1
        cam = (lerp(c0[0], c1[0], u), lerp(c0[1], c1[1], u), c0[2] * (c1[2] / c0[2]) ** u)
        fr = self.sea.copy(); d = ImageDraw.Draw(fr, "RGBA")
        step = 5 if cam[2] < 60 else (2 if cam[2] < 200 else 1)
        for lon in range(-40, 60, step):
            x = self.P(lon, cam[1], cam)[0]
            if 0 <= x <= W: d.line([(x, 0), (x, H)], fill=(70, 90, 110, 22))
        for lat in range(20, 75, step):
            y = self.P(cam[0], lat, cam)[1]
            if 0 <= y <= H: d.line([(0, y), (W, y)], fill=(70, 90, 110, 22))
        hl = self.highlights(t)
        cosl = math.cos(math.radians(cam[1]))
        for nm, polys in self.C.items():
            for p in polys:
                xs = W / 2 + (p[:, 0] - cam[0]) * cosl * cam[2]; ys = H / 2 - (p[:, 1] - cam[1]) * cam[2]
                if xs.max() < -60 or xs.min() > W + 60 or ys.max() < -60 or ys.min() > H + 60 or len(xs) < 3: continue
                pts = list(zip(xs.tolist(), ys.tolist()))
                if nm in hl:
                    col, a = hl[nm]; base = np.array([34, 38, 46]); cc = tuple(int(v) for v in base + (np.array(col) - base) * a)
                    d.polygon(pts, fill=cc + (255,), outline=col + (int(120 + 120 * a),))
                else:
                    d.polygon(pts, fill=(34, 38, 46, 255), outline=(86, 94, 106, 255))
        if cam[2] < 260:
            for nm, (lo, la) in COUNTRY_LABELS.items():
                x, y = self.P(lo, la, cam)
                if 60 < x < W - 60 and 60 < y < H - 160:
                    sea = nm.endswith("SEA") or nm.endswith("OCEAN")
                    paste(fr, text_img(nm, font(F_OSW_L if sea else F_OSW, 22 if cam[2] < 80 else 28), (110, 130, 150) if sea else (130, 136, 146), tracking=8 if sea else 6), x, y, "cm", 0.75)
        self.overlay(fr, d, t, cam)
        return self.post(fr, t)
    # helpers
    def highlights(self, t):
        m = self.mode; R = (170, 50, 40); G = GOLD; Bl = (90, 120, 160)
        if m == "europe_dark": return {"Germany": (R, 0.5 + 0.3 * ramp(t, 0.5, 2)), "Spain": (G, ramp(t, 1.5, 1.5) * 0.6)}
        if m in ("huelva", "docs_path", "cadiz", "currents"): return {"Spain": (G, 0.25)}
        if m == "two_choices": return {"Italy": (G, 0.45 if self.p.get("hl") == "sicily" else 0.15), "Greece": (G, 0.45 if self.p.get("hl") == "greece" else 0.15)}
        if m in ("sicily_zoom", "sicily_obvious"): return {"Italy": (G, 0.35), "Tunisia": (Bl, 0.4)}
        if m in ("fake_targets", "reinforce"): return {"Greece": (R, 0.55), "Italy": (G, 0.18)}
        if m == "barclay": return {"Greece": (R, 0.45), "Egypt": (Bl, 0.35), "Syria": (Bl, 0.35)}
        if m == "madrid_berlin": return {"Spain": (G, 0.25), "Germany": (R, 0.45)}
        if m == "med_1943": return {"Tunisia": (Bl, 0.4), "Libya": (Bl, 0.3), "Egypt": (Bl, 0.3), "Algeria": (Bl, 0.3), "Morocco": (Bl, 0.3)}
        if m == "wrong_way": return {"Greece": (R, 0.5), "Italy": (G, 0.3)}
        if m == "channel": return {"France": (R, 0.35), "United Kingdom": (Bl, 0.4)}
        if m in ("london_greenock",): return {"United Kingdom": (Bl, 0.35)}
        return {}
    def dot(self, fr, d, nm, cam, a, col=GOLD, big=False, side="r", t=0.0, txt=None):
        if a <= 0: return
        x, y = self.P(*PL[nm], cam); r = 10 if big else 7
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(255 * a),))
        if big:
            pul = (t * 0.7) % 1; rr = r + 34 * pul; d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col + (int(200 * (1 - pul) * a),), width=2)
        ti = text_img(txt or nm, font(F_OSW_B, 30 if big else 24), WHITE, tracking=5)
        paste(fr, ti, x + (22 if side == "r" else -22), y, "lm" if side == "r" else "rm", a)
    def path(self, d, pts, prog, col, width=5, dash=True):
        L = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]; tot = sum(L) or 1; lim = tot * clamp(prog); acc = 0; last = pts[0]
        for i, l in enumerate(L):
            a, b = pts[i], pts[i + 1]; s = 0
            while s < l and acc + s < lim:
                e = min(l, s + (18 if dash else l), lim - acc)
                p1 = (lerp(a[0], b[0], s / l), lerp(a[1], b[1], s / l)); p2 = (lerp(a[0], b[0], e / l), lerp(a[1], b[1], e / l))
                d.line([p1, p2], fill=col + (240,), width=width); last = p2; s += 30 if dash else l
            acc += l
        return last
    def arrow(self, d, a, b, prog, col, width=6, bend=0.18):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2; nx, ny = -(b[1] - a[1]), b[0] - a[0]
        c = (mx + nx * bend, my + ny * bend)
        pts = [((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * c[0] + s * s * b[0], (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * c[1] + s * s * b[1]) for s in np.linspace(0, 1, 40)]
        k = max(1, int(len(pts) * clamp(prog)))
        d.line(pts[:k], fill=col + (235,), width=width)
        if prog >= 0.98:
            p, q = pts[-3], pts[-1]; ang = math.atan2(q[1] - p[1], q[0] - p[0])
            d.polygon([q, (q[0] - 26 * math.cos(ang - 0.45), q[1] - 26 * math.sin(ang - 0.45)), (q[0] - 26 * math.cos(ang + 0.45), q[1] - 26 * math.sin(ang + 0.45))], fill=col + (240,))
    def note(self, fr, text, a, y=210, x=None, col=(225, 222, 214), size=26):
        if a <= 0: return
        paste(fr, text_img(text, font(F_OSW, size), col, tracking=4), x if x is not None else W / 2, y, "cm", a)
    def overlay(self, fr, d, t, cam):
        m = self.mode; D = self.dur; R = (215, 70, 55)
        if m == "europe_dark":
            self.note(fr, "NAZI-OCCUPIED EUROPE  ·  1943", ramp(t, 0.6, 1), y=130, col=(220, 150, 140))
            self.dot(fr, d, "HUELVA", cam, ramp(t, D * 0.4, 0.8), big=True, t=t, side="l")
        elif m == "huelva":
            self.dot(fr, d, "HUELVA", cam, ramp(t, 0.4, 0.7), big=True, t=t)
            self.dot(fr, d, "CÁDIZ", cam, ramp(t, 0.9, 0.7)); self.dot(fr, d, "GIBRALTAR", cam, ramp(t, 1.2, 0.7) * (1 if cam[2] < 300 else 0))
            self.note(fr, "SOUTHWEST SPAIN  ·  ATLANTIC COAST", ramp(t, 0.5, 1), y=130)
        elif m == "docs_path":
            seq = ["HUELVA", "SAN FERNANDO", "MADRID"]; pts = [self.P(*PL[s], cam) for s in seq]
            for i, s in enumerate(seq): self.dot(fr, d, s, cam, ramp(t, 0.3 + i * D * 0.22, 0.6), big=(s == "MADRID"), t=t, side="l" if s == "SAN FERNANDO" else "r")
            self.path(d, pts, ramp(t, 0.5, D * 0.6), GOLD)
            self.note(fr, "THE BRIEFCASE'S ROUTE  ·  MAY 1943", ramp(t, 0.3, 1), y=130)
        elif m == "madrid_berlin":
            self.dot(fr, d, "MADRID", cam, ramp(t, 0.2, 0.6), big=True, t=t); self.dot(fr, d, "BERLIN", cam, ramp(t, D * 0.5, 0.6), col=R, big=True, t=t)
            self.arrow(d, self.P(*PL["MADRID"], cam), self.P(*PL["BERLIN"], cam), ramp(t, 0.6, D * 0.6), R)
            self.note(fr, "INFORMATION PASSED TO THE GERMANS  ·  8 MAY 1943", ramp(t, 0.5, 1), y=130)
        elif m == "med_1943":
            self.note(fr, "THE MEDITERRANEAN  ·  LATE 1942", ramp(t, 0.3, 1), y=130)
            a = self.P(29, 30.5, cam); b = self.P(12, 33.2, cam); self.arrow(d, a, b, ramp(t, 1.0, 2.5), (120, 170, 220), bend=0.08)
            a2 = self.P(1, 35.5, cam); b2 = self.P(8.8, 36.2, cam); self.arrow(d, a2, b2, ramp(t, 1.6, 2.2), (120, 170, 220), bend=-0.1)
            self.note(fr, "ALLIED ADVANCE ACROSS NORTH AFRICA", ramp(t, 2.0, 1), y=H - 230, col=(160, 200, 235))
        elif m == "channel":
            self.dot(fr, d, "LONDON", cam, ramp(t, 0.3, 0.6)); self.dot(fr, d, "PARIS", cam, ramp(t, 0.5, 0.6))
            self.note(fr, "CROSS-CHANNEL INVASION: NOT BEFORE 1944", ramp(t, 0.6, 1), y=130, col=(220, 150, 140))
        elif m == "two_choices":
            for nm, on in (("SICILY", self.p.get("hl") == "sicily"), ("GREECE", self.p.get("hl") == "greece")):
                x, y = self.P(*PL[nm], cam); a = 1.0 if on else 0.4; r = 70 + 6 * math.sin(t * 2)
                d.ellipse([x - r, y - r, x + r, y + r], outline=GOLD + (int(230 * a * ramp(t, 0.3, 0.6)),), width=4)
                paste(fr, text_img(("OPTION 1: " if nm == "SICILY" else "OPTION 2: ") + nm, font(F_OSW_B, 30), WHITE, tracking=4), x, y - r - 30, "cm", a * ramp(t, 0.4, 0.6))
        elif m in ("sicily_zoom", "sicily_obvious"):
            self.dot(fr, d, "SICILY", cam, ramp(t, 0.3, 0.7), big=True, t=t); self.dot(fr, d, "TUNIS", cam, ramp(t, 0.6, 0.7), col=(120, 170, 220))
            if m == "sicily_obvious":
                a = self.P(11.1, 37.05, cam); b = self.P(12.45, 37.8, cam)
                d.line([a, b], fill=WHITE + (int(200 * ramp(t, 0.8, 0.8)),), width=3)
                paste(fr, text_img("< 100 MILES", font(F_BEBAS, 54), GOLD, tracking=4), (a[0] + b[0]) / 2 - 30, (a[1] + b[1]) / 2 + 40, "rm", ramp(t, 1.0, 0.8))
                self.note(fr, "THE OBVIOUS TARGET", ramp(t, 1.2, 0.8), y=130, col=(220, 150, 140), size=30)
        elif m == "barclay":
            self.dot(fr, d, "CAIRO", cam, ramp(t, 0.3, 0.6), txt="CAIRO  ·  FICTIONAL 12TH ARMY", side="l")
            self.dot(fr, d, "SYRIA", cam, ramp(t, D * 0.3, 0.6), txt="DUMMY TANKS", side="l")
            self.arrow(d, self.P(*PL["CAIRO"], cam), self.P(*PL["GREECE"], cam), ramp(t, 0.8, D * 0.5), R)
            self.note(fr, "OPERATION BARCLAY  ·  THE WIDER DECEPTION", ramp(t, 0.3, 1), y=130)
        elif m == "cadiz":
            self.dot(fr, d, "CÁDIZ", cam, ramp(t, 0.3, 0.6)); self.dot(fr, d, "TARIFA", cam, ramp(t, 0.8, 0.6), txt="TARIFA  ·  BODY WASHED ASHORE")
            x, y = self.P(-6.6, 36.3, cam); a = ramp(t, 0.5, 0.6)
            d.line([x - 14, y - 14, x + 14, y + 14], fill=R + (int(255 * a),), width=5); d.line([x - 14, y + 14, x + 14, y - 14], fill=R + (int(255 * a),), width=5)
            paste(fr, text_img("AIR CRASH  ·  SEPTEMBER 1942", font(F_OSW_B, 24), (240, 150, 140), tracking=3), x - 26, y, "rm", a)
        elif m == "fake_targets":
            self.dot(fr, d, "CAPE ARAXOS", cam, ramp(t, 0.4, 0.6), col=R); self.dot(fr, d, "KALAMATA", cam, ramp(t, 0.8, 0.6), col=R)
            self.dot(fr, d, "SARDINIA", cam, ramp(t, 1.2, 0.6), col=R)
            self.dot(fr, d, "SICILY", cam, ramp(t, 1.6, 0.6), col=(150, 150, 150), txt="SICILY  ·  'COVER TARGET'")
            self.note(fr, "WHAT THE PLANTED LETTERS SUGGESTED", ramp(t, 0.3, 1), y=130, col=(240, 160, 150))
        elif m == "sardinia":
            self.dot(fr, d, "SARDINIA", cam, ramp(t, 0.3, 0.6), col=R, big=True, t=t, txt="SARDINIA  ·  'SARDINES'?")
        elif m == "currents":
            self.dot(fr, d, "HUELVA", cam, ramp(t, 0.3, 0.6), big=True, t=t)
            rng = random.Random(5)
            for k in range(26):
                sx, sy = rng.uniform(-8.6, -7.2), rng.uniform(36.6, 37.05); ph = (t * 0.25 + rng.random()) % 1
                a = self.P(sx, sy, cam); b = self.P(sx + 0.5, sy + 0.18, cam)
                p = (lerp(a[0], b[0], ph), lerp(a[1], b[1], ph)); q = (lerp(a[0], b[0], min(1, ph + 0.15)), lerp(a[1], b[1], min(1, ph + 0.15)))
                d.line([p, q], fill=(150, 200, 230, int(200 * math.sin(math.pi * ph))), width=3)
            self.note(fr, "TIDES & CURRENTS TOWARD THE SHORE  ·  SCHEMATIC", ramp(t, 0.5, 1), y=130)
        elif m == "london_greenock":
            pts = [self.P(*PL["LONDON"], cam), self.P(-1.6, 52.6, cam), self.P(-2.7, 53.8, cam), self.P(-3.3, 55.1, cam), self.P(*PL["GREENOCK"], cam)]
            self.dot(fr, d, "LONDON", cam, ramp(t, 0.2, 0.6)); self.dot(fr, d, "GREENOCK", cam, ramp(t, D * 0.6, 0.6), big=True, t=t)
            self.path(d, pts, ramp(t, 0.4, D * 0.7), GOLD)
            self.note(fr, "17–18 APRIL 1943  ·  400+ MILES BY ROAD  ·  ROUTE SCHEMATIC", ramp(t, 0.4, 1), y=130)
        elif m == "seraph_route":
            pts = [self.P(*PL["GREENOCK"], cam)] + [self.P(lo, la, cam) for lo, la in ((-5.2, 55.6), (-5.6, 54.6), (-5.3, 53.6), (-6.0, 52.3), (-6.8, 50.8), (-9.5, 47.0), (-10.3, 42.5), (-9.2, 38.2), (-7.1, 37.05))]
            self.dot(fr, d, "GREENOCK", cam, ramp(t, 0.2, 0.6)); self.dot(fr, d, "HUELVA", cam, ramp(t, D * 0.7, 0.6), big=True, t=t)
            self.path(d, pts, ramp(t, 0.3, D * 0.8), (150, 200, 230))
            self.note(fr, "HMS SERAPH  ·  19–29 APRIL 1943  ·  ROUTE SCHEMATIC", ramp(t, 0.4, 1), y=130)
        elif m == "reinforce":
            st = self.p.get("stage", 1)
            a = self.P(2.0, 47.0, cam); b = self.P(*PL["SALONIKA"], cam)
            self.arrow(d, a, b, ramp(t, 0.3, D * 0.5) if st == 1 else 1.0, R, bend=0.12)
            if (st == 1 and t > D * 0.4) or st == 2:
                paste(fr, text_img("1ST PANZER DIVISION: FRANCE TO GREECE", font(F_OSW_B, 26), (240, 160, 150), tracking=3), b[0] - 30, b[1] - 50, "rm", ramp(t, D * 0.4, 0.6) if st == 1 else 1)
            if st == 2:
                x, y = self.P(*PL["SARDINIA"], cam); a2 = ramp(t, 0.3, 0.6)
                d.ellipse([x - 60, y - 60, x + 60, y + 60], outline=R + (int(230 * a2),), width=4)
                paste(fr, text_img("SARDINIA: GERMAN STRENGTH DOUBLED, TO ABOUT 10,000", font(F_OSW_B, 26), (240, 160, 150), tracking=3), x + 80, y + 80, "lm", a2)
                s1, s2 = self.P(*PL["SICILY"], cam), self.P(23.5, 37.4, cam)
                self.arrow(d, s1, s2, ramp(t, 1.2, 2.0), (200, 200, 200), width=4, bend=-0.15)
                paste(fr, text_img("TORPEDO BOATS: SICILY TO GREEK ISLANDS", font(F_OSW, 22), (220, 220, 220), tracking=3), (s1[0] + s2[0]) / 2, (s1[1] + s2[1]) / 2 + 70, "cm", ramp(t, 2.6, 0.6))
            self.note(fr, "GERMAN MOVES, MAY–JUNE 1943", 1.0, y=130, col=(240, 160, 150))
        elif m == "aircraft":
            s, sa = self.P(*PL["SICILY"], cam), self.P(*PL["SARDINIA"], cam)
            self.dot(fr, d, "SICILY", cam, 1.0, big=True, t=t, txt="SICILY  ·  INVADED 9 JULY"); self.dot(fr, d, "SARDINIA", cam, 1.0, col=R)
            for k in range(7):
                ph = clamp((t - 0.5 - k * 0.35) / 3.0)
                if ph <= 0: continue
                x = lerp(s[0], sa[0], ph) + (k - 3) * 10; y = lerp(s[1], sa[1], ph) + (k % 3) * 12
                d.polygon([(x, y - 8), (x - 10, y + 6), (x + 10, y + 6)], fill=(230, 230, 230, 230))
            self.note(fr, "+4 HOURS: 21 AIRCRAFT LEAVE SICILY FOR SARDINIA", ramp(t, 0.6, 1), y=130, col=(240, 160, 150))
        elif m == "wrong_way":
            for tgt in ("GREECE", "SARDINIA"):
                self.arrow(d, self.P(10.0, 47.5, cam), self.P(*PL[tgt], cam), ramp(t, 0.3, 2.0), R, bend=0.1)
            self.dot(fr, d, "SICILY", cam, ramp(t, 1.0, 0.8), big=True, t=t, txt="SICILY  ·  THE REAL TARGET")
            self.note(fr, "GERMAN ATTENTION  ·  POINTED THE WRONG WAY", ramp(t, 0.5, 1), y=130, col=(240, 160, 150))


# ═════════════════════════ TYPOGRAPHY ═════════════════════════
@scene("statement")
class Statement(Base):
    def setup(self):
        st = self.p.get("style", "center"); self.st = st
        self.plate = bg_plate(W + 200, H + 120, 21 + len(self.p["lines"][0]), (7, 8, 10), (28, 30, 36), 0.5, 0.4).convert("RGBA")
        acc = set(self.p.get("accent", []))
        sizes = {"single": 150, "center": 104, "memorial": 92, "latin": 96}
        self.imgs = []
        for i, ln in enumerate(self.p["lines"]):
            if st == "memorial" and i > 0:
                im = text_img(ln, font(F_OSW, 34), (214, 200, 160), tracking=8)
            elif st == "latin":
                im = text_img(ln, font(F_SERIF_I, 100), GOLD if i in acc else WHITE)
            else:
                f = font(F_BEBAS, sizes[st] if len(ln) < 26 else int(sizes[st] * 26 / len(ln) * 1.05))
                im = text_img(ln, f, GOLD if i in acc else WHITE, tracking=6)
            self.imgs.append(glow(im, 18, 0.45) if i in acc else im)
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.05).convert("RGBA")
        n = len(self.imgs); gap = 125 if self.st != "memorial" else 95; y = H * 0.43 - (n - 1) * gap / 2
        for i, im in enumerate(self.imgs):
            a = ramp(t, 0.15 + i * 0.45, 0.8 if self.st != "single" else 1.2)
            sc = 1.0 + (0.05 * (1 - ease_out(clamp(t / 2.5))) if self.st == "single" else 0)
            img = im if sc == 1 else im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.BILINEAR)
            paste(fr, img, W / 2, y, "cm", a); y += gap
        if self.st == "memorial":
            d = ImageDraw.Draw(fr); lw = 420 * ease_out(ramp(t, 0.4, 1.5)); d.line([(W / 2 - lw / 2, H * 0.43 + 28), (W / 2 + lw / 2, H * 0.43 + 28)], fill=GOLD + (180,), width=2) if n > 1 else None
        return self.post(fr, t, dust=True, tagtxt="")


@scene("quote")
class Quote(Base):
    def setup(self):
        self.plate = bg_plate(W + 200, H + 120, 77, (8, 8, 10), (34, 30, 28), 0.3, 0.3).convert("RGBA")
        if self.p.get("style") == "psalm":
            self.lines = [text_img("PSALM 39", font(F_BEBAS, 150), GOLD, tracking=12)]; self.who = text_img(self.p["who"].upper(), font(F_OSW, 28), (210, 206, 196), tracking=6)
        else:
            f = font(F_SERIF_I, 70); self.lines = [text_img(l, f, WHITE) for l in wrap_text(self.p["text"], f, 1380)]
            self.who = text_img("— " + self.p["who"], font(F_OSW, 28), GOLD, tracking=5)
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.05).convert("RGBA")
        n = len(self.lines); y = H * 0.40 - (n - 1) * 46
        for i, im in enumerate(self.lines): paste(fr, im, W / 2, y + i * 92, "cm", ramp(t, 0.2 + i * 0.25, 0.8))
        paste(fr, self.who, W / 2, y + n * 92 + 30, "cm", ramp(t, 0.6 + n * 0.25, 0.8))
        return self.post(fr, t, dust=True, tagtxt="")


@scene("stamp")
class Stamp(Base):
    def setup(self):
        self.desk = desk(91)
        self.paper = paper_sheet(1100, 640, 3)
        f = font(F_BEBAS, 120 if len(self.p["text"]) < 16 else 96); ti = text_img(self.p["text"], f, RED, tracking=8)
        w, h = ti.size; st = Image.new("RGBA", (w + 60, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
        d.rectangle([5, 5, w + 54, h + 34], outline=RED + (255,), width=8); st.alpha_composite(ti, (30, 18))
        n = (smooth_noise(st.size[0], st.size[1], 5, 2, 1) > 0.33).astype(np.float32)
        a = np.asarray(st).copy(); a[..., 3] = (a[..., 3] * n * 0.88).astype(np.uint8); self.stamp = Image.fromarray(a, "RGBA").rotate(-6, expand=True, resample=Image.BICUBIC)
        self.sub = text_img(self.p.get("sub", ""), font(F_TYPE, 34), (60, 50, 40))
    def frame(self, t):
        fr = kb_transform(self.desk, self.u(t), 1.0, 1.08).convert("RGBA")
        paste(fr, self.paper, W / 2, H * 0.47, "cm")
        k = ease_out(clamp((t - 0.35) / 0.22)); s = 1.6 - 0.6 * k
        st = self.stamp.resize((int(self.stamp.size[0] * s), int(self.stamp.size[1] * s)), Image.BILINEAR)
        if t > 0.35: paste(fr, st, W / 2, H * 0.42, "cm", k)
        paste(fr, self.sub, W / 2, H * 0.62, "cm", ramp(t, 0.8, 0.6))
        return self.post(fr, t, tagtxt="RECREATION")


@scene("datecard")
class DateCard(Base):
    def setup(self):
        self.plate = bg_plate(W + 200, H + 120, 88, (6, 7, 9), (26, 30, 36), 0.5, 0.5).convert("RGBA")
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.05).convert("RGBA")
        date = self.p["date"]; shown = date[:int(len(date) * clamp((t - 0.2) / 1.0))]
        paste(fr, text_img(shown, font(F_BEBAS, 150), WHITE, tracking=10), W / 2, H * 0.42, "cm")
        paste(fr, text_img(self.p["place"], font(F_OSW, 36), GOLD, tracking=12), W / 2, H * 0.55, "cm", ramp(t, 1.0, 0.7))
        if self.p.get("time"): paste(fr, text_img(self.p["time"], font(F_TYPE, 40), (200, 196, 186)), W / 2, H * 0.62, "cm", ramp(t, 1.4, 0.7))
        return self.post(fr, t, tagtxt="")


@scene("questions")
class Questions(Base):
    def setup(self):
        self.plate = bg_plate(W + 200, H + 120, 160, (6, 6, 8), (30, 26, 24), 0.5, 0.4).convert("RGBA")
        self.q = self.p["q"]; n = len(self.q); self.times = [self.dur * 0.05 + i * self.dur * 0.3 for i in range(n)]
        self.imgs = [text_img(q, font(F_BEBAS, 84), WHITE, tracking=5) for q in self.q]
        self.g = [glow(text_img(q, font(F_BEBAS, 84), GOLD, tracking=5), 14, 0.5) for q in self.q]
    def frame(self, t):
        fr = kb_transform(self.plate, self.u(t), 1.0, 1.06).convert("RGBA")
        cur = max([i for i in range(len(self.q)) if t >= self.times[i]] or [0])
        for i in range(len(self.q)):
            a = ramp(t, self.times[i], 0.5)
            paste(fr, self.g[i] if i == cur else self.imgs[i], W / 2, 300 + i * 150, "cm", a * (1 if i == cur else 0.35))
        return self.post(fr, t, tagtxt="")


@scene("chapter")
class Chapter(Base):
    def setup(self):
        self.plate = bg_plate(W, H, 40, (5, 6, 8), (24, 24, 28), 0.5, 0.5).convert("RGBA")
        self.num = text_img("CHAPTER " + self.p["num"], font(F_OSW, 30), GOLD, tracking=12)
        self.title = text_img(self.p["title"], font(F_BEBAS, 150 if len(self.p["title"]) < 20 else 124), WHITE, tracking=10)
    def frame(self, t):
        fr = self.plate.copy(); a = ramp(t, 0.1, 0.6) * (1 - ramp(t, self.dur - 0.5, 0.5))
        paste(fr, self.num, W / 2, H * 0.36, "cm", a * ramp(t, 0.2, 0.6))
        sc = 1.04 - 0.04 * ease_out(t / self.dur); ti = self.title.resize((int(self.title.size[0] * sc), int(self.title.size[1] * sc)), Image.BILINEAR)
        paste(fr, ti, W / 2, H * 0.47, "cm", a * ramp(t, 0.35, 0.7))
        d = ImageDraw.Draw(fr); lw = 600 * ease_out(ramp(t, 0.4, 1.4)); d.line([(W / 2 - lw / 2, H * 0.58), (W / 2 + lw / 2, H * 0.58)], fill=GOLD + (int(220 * a),), width=2)
        return self.post(fr, t, dust=True, tagtxt="")


@scene("title")
class Title(Base):
    def setup(self):
        self.oc = Ocean(self.dur, [], dict(variant="predawn", still=True))
        self.l0 = text_img("WAR FILES PRESENTS", font(F_OSW, 30), GOLD, tracking=14)
        self.l1 = text_img("THE DEAD MAN", font(F_BEBAS, 190), WHITE, tracking=10)
        self.l2 = glow(text_img("WHO FOOLED HITLER", font(F_BEBAS, 118), GOLD, tracking=12), 20, 0.5)
        self.l3 = text_img("OPERATION MINCEMEAT  ·  1943", font(F_OSW, 30), (200, 196, 188), tracking=10)
        self.disc = text_img("Scenes marked DRAMATIZATION, ILLUSTRATION or RECREATION are reconstructions, not archival material.", font(F_INTER, 21), (170, 168, 160))
    def frame(self, t):
        fr = self.oc.frame(t)
        arr = np.asarray(fr, np.float32); arr[..., :3] *= 0.45; fr = Image.fromarray(arr.astype(np.uint8), "RGBA")
        paste(fr, self.l0, W / 2, H * 0.27, "cm", ramp(t, 0.2, 0.8))
        paste(fr, self.l1, W / 2, H * 0.39, "cm", ramp(t, 0.5, 1.0)); paste(fr, self.l2, W / 2, H * 0.52, "cm", ramp(t, 1.0, 1.0))
        paste(fr, self.l3, W / 2, H * 0.62, "cm", ramp(t, 1.6, 0.8)); paste(fr, self.disc, W / 2, H * 0.71, "cm", 0.85 * ramp(t, 2.2, 0.8))
        label(fr, "")
        return fr


@scene("end")
class End(Base):
    def setup(self):
        self.oc = Ocean(self.dur, [], dict(variant="dawn", still=True, coast=True))
        logo = Image.open(os.path.join(ROOT, "assets", "war_files_logo_transparent.png")).convert("RGBA"); self.logo = logo.resize((300, 300), Image.LANCZOS)
        self.t1 = text_img("IN MEMORY OF GLYNDWR MICHAEL", font(F_OSW, 34), (230, 224, 210), tracking=10)
        self.t2 = text_img("ABERBARGOED, WALES  ·  'Y DYN NA FU ERIOED'", font(F_OSW, 24), GOLD, tracking=8)
        self.t3 = text_img("Sources and archival credits in the description", font(F_INTER, 22), (190, 188, 180))
    def frame(self, t):
        fr = self.oc.frame(t); arr = np.asarray(fr, np.float32); arr[..., :3] *= lerp(0.8, 0.35, ramp(t, 2.0, 3.0)); fr = Image.fromarray(arr.astype(np.uint8), "RGBA")
        a = ramp(t, 3.2, 1.2) * (1 - ramp(t, self.dur - 1.2, 1.1))
        paste(fr, self.t1, W / 2, H * 0.36, "cm", ramp(t, 0.6, 1.2) * (1 - ramp(t, 2.8, 0.6)))
        paste(fr, self.t2, W / 2, H * 0.42, "cm", ramp(t, 1.0, 1.2) * (1 - ramp(t, 2.8, 0.6)))
        paste(fr, self.logo, W / 2, H * 0.42, "cm", a); paste(fr, self.t3, W / 2, H * 0.62, "cm", a)
        if t > self.dur - 1.0:
            arr = np.asarray(fr, np.float32); arr[..., :3] *= clamp((self.dur - t) / 1.0); fr = Image.fromarray(arr.astype(np.uint8), "RGBA")
        return fr


# ═════════════════════════ PAPER / DOCUMENTS ═════════════════════════
@functools.lru_cache(None)
def desk(seed=90, warm=True):
    n = smooth_noise(W + 200, H + 120, 40, seed, 3); grain = smooth_noise(W + 200, H + 120, 3, seed + 1, 1)
    base = np.array([34, 24, 16] if warm else [22, 24, 28], np.float32)
    yy = np.linspace(0, 1, H + 120)[:, None]
    stripes = 0.08 * np.sin(yy * 90 + n * 6)
    arr = base * (0.6 + 0.6 * n + 0.15 * grain + stripes)[..., None] * (0.35 + 1.1 * radial(W + 200, H + 120, (W + 200) * 0.45, (H + 120) * 0.35, 1500) ** 1.2)[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")


@functools.lru_cache(None)
def paper_sheet(w, h, seed=0, tone=(228, 220, 198)):
    n = smooth_noise(w, h, 30, seed, 3); f = smooth_noise(w, h, 2, seed + 3, 1)
    arr = np.array(tone, np.float32) * (0.9 + 0.12 * n + 0.04 * f)[..., None]
    edge = np.minimum.outer(np.minimum(np.arange(h), np.arange(h)[::-1]), np.minimum(np.arange(w), np.arange(w)[::-1])).astype(np.float32)
    arr *= (0.86 + 0.14 * np.clip(edge / 40, 0, 1))[..., None]
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    out = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0)); sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([48, 52, w + 48, h + 52], fill=(0, 0, 0, 150)); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18))); out.paste(im, (40, 40))
    return out


def abstract_lines(d, x0, y0, x1, n, seed, col=(110, 104, 96), gap=34, width=3):
    rng = random.Random(seed)
    for i in range(n):
        ln = (x1 - x0) * (rng.uniform(0.55, 1.0) if i % 6 != 5 else rng.uniform(0.2, 0.5)); x = x0
        while x < x0 + ln:
            wl = rng.uniform(20, 90); d.line([(x, y0 + i * gap), (min(x + wl, x0 + ln), y0 + i * gap)], fill=col, width=width); x += wl + 12


DOCS = {
 "trout": dict(title="NAVAL INTELLIGENCE DIVISION", head="MEMORANDUM  ·  29 SEPTEMBER 1939", body=None, lines=16),
 "trout28": dict(title="ITEM No. 28", head="A Suggestion (not a very nice one)", body="The following suggestion is used in a book by Basil Thomson: a corpse dressed as an airman, with despatches in his pockets, could be dropped on the coast, supposedly from a parachute that has failed.", lines=0),
 "plan": dict(title="MOST SECRET", head="OPERATION MINCEMEAT  ·  4 FEBRUARY 1943", body=None, lines=15),
 "ring": dict(title="BOND STREET, LONDON W.1", head="RECEIPT", body="One diamond single-stone ring  ......  £53  10s  6d", lines=5, small=True),
 "bank": dict(title="LLOYDS BANK LIMITED", head="Re: your account", body="Overdraft: £79  19s  2d", lines=10),
 "nye_env": dict(title="", head="", env=True, to="General Sir Harold Alexander"),
 "nye": dict(title="PERSONAL AND MOST SECRET", head="My dear Alex,", body="We have recent information that the Boche have been reinforcing and strengthening their defences in Greece and Crete and C.I.G.S. felt that our forces for the assault were insufficient. It was agreed by the Chiefs of Staff that the 5th Division should be reinforced by one Brigade Group for the assault on the beach south of CAPE ARAXOS and that a similar reinforcement should be made for the 56th Division at KALAMATA.", lines=0, partial=True),
 "signal": dict(title="NAVAL SIGNAL", head="FROM: H.M. SUBMARINE SERAPH    TO: ADMIRALTY", body="MINCEMEAT COMPLETED", lines=0, big=True),
 "cable": dict(title="CIPHER TELEGRAM", head="HUELVA — MADRID  ·  MAY 1943", body=None, lines=9, redact=True),
 "cable2": dict(title="CIPHER TELEGRAM", head="FOR ONWARD TRANSMISSION  ·  MAY 1943", body=None, lines=9, redact=True),
 "decrypt": dict(title="ULTRA  ·  DECRYPT SUMMARY", head="GERMAN MESSAGE OF 12 MAY 1943", body="Invasion expected in the BALKANS, with a feint toward the DODECANESE.", lines=6, teletype=True),
 "sealed": dict(env=True, to="", title="", head=""),
 "photographed": dict(title="", head="", body=None, lines=14, flash=True),
}


@scene("doc")
class Doc(Base):
    def setup(self):
        k = self.p["kind"]; self.k = k; self.spec = DOCS[k]
        self.desk = desk(93 + len(k))
        if self.spec.get("env"):
            self.sheet = self.envelope(self.spec.get("to", ""))
        else:
            big = self.spec.get("small"); w, h = (900, 560) if big else (1100, 1400)
            self.sheet = paper_sheet(w, h, len(k), tone=(232, 226, 204) if not self.spec.get("teletype") else (236, 228, 190)).copy()
            d = ImageDraw.Draw(self.sheet); x0 = 140; y = 150
            if self.spec["title"]: d.text((w / 2 + 40, y), self.spec["title"], font=font(F_TYPE, 40), fill=(120, 34, 28) if "SECRET" in self.spec["title"] or "ULTRA" in self.spec["title"] else (40, 36, 32), anchor="mm"); y += 80
            if self.spec["head"]: d.text((x0, y), self.spec["head"], font=font(F_TYPE, 38 if not big else 34), fill=(36, 32, 30)); y += 90
            self.body_y = y; self.x0 = x0; self.w = w
            if self.spec.get("lines"): abstract_lines(d, x0, y + (130 if self.spec.get("body") else 0), w - 60, self.spec["lines"], len(k) * 7)
            if self.spec.get("redact"):
                for i in range(4): d.rectangle([x0, y + i * 68, x0 + random.Random(i).uniform(300, 760), y + i * 68 + 30], fill=(30, 28, 26))
        self.body = self.spec.get("body")
        if self.body:
            f = font(F_TYPE, 74 if self.spec.get("big") else 38); self.bf = f
            self.blines = wrap_text(self.body, f, self.sheet.size[0] - 260)
        self.zoom = (1.0, 1.25) if self.spec.get("partial") or self.k in ("trout28",) else (1.0, 1.12)
    def envelope(self, to):
        w, h = 1300, 760; im = paper_sheet(w, h, 9, tone=(214, 198, 160)).copy(); d = ImageDraw.Draw(im)
        d.line([(40, 40), (40 + w / 2, 40 + h * 0.55), (40 + w, 40)], fill=(150, 132, 96), width=4)
        cx, cy = 40 + w / 2, 40 + h * 0.55
        d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(140, 24, 20)); d.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], outline=(100, 14, 12), width=6)
        if to: d.text((cx, cy + 190), to, font=font(F_TYPE, 46), fill=(40, 34, 30), anchor="mm")
        return im
    def frame(self, t):
        u = ease_in_out(self.u(t))
        fr = kb_transform(self.desk, u, 1.0, 1.06).convert("RGBA")
        sh = self.sheet.copy()
        if self.body:
            d = ImageDraw.Draw(sh); total = sum(len(l) for l in self.blines); shown = int(total * clamp((t - 0.4) / max(1.5, self.dur * 0.55))); y = self.body_y + (0 if not self.spec.get("big") else 120)
            for l in self.blines:
                part = l[:max(0, shown)]; shown -= len(l)
                col = (150, 30, 24) if any(k in part for k in ("ARAXOS", "KALAMATA", "BALKANS", "DODECANESE", "MINCEMEAT")) and self.k != "decrypt" else (30, 28, 26)
                d.text((self.x0 if not self.spec.get("big") else self.sheet.size[0] / 2, y), part, font=self.bf, fill=col, anchor="la" if not self.spec.get("big") else "ma"); y += int(self.bf.size * 1.45)
        sw, shh = sh.size; s = min(1100 / shh, 1500 / sw) * lerp(self.zoom[0], self.zoom[1], u)
        sh2 = sh.resize((int(sw * s), int(shh * s)), Image.BILINEAR).rotate(-1.5 + u, expand=True, resample=Image.BICUBIC)
        ty = H * 0.5 + (sh2.size[1] * 0.22 * u if self.spec.get("partial") else 0)
        paste(fr, sh2, W / 2, ty, "cm")
        arr = np.asarray(fr, np.float32); arr[..., :3] *= (0.5 + 0.65 * radial(W, H, W * 0.45, H * 0.35, W * 0.85)[..., None])
        if self.spec.get("flash"):
            fl = sum(max(0, 1 - abs(t - ft) / 0.12) for ft in (1.0, 2.6, 4.0)); arr[..., :3] += fl * 160
        fr = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
        return self.post(fr, t)


@scene("envelope")
class Envelope(Base):
    def setup(self):
        self.desk = desk(95, warm=self.p["variant"] not in ("lab", "eyelash_gone"))
        self.env = Doc.envelope(self, "")
    def frame(self, t):
        v = self.p["variant"]; u = ease_in_out(self.u(t))
        fr = kb_transform(self.desk, u, 1.0, 1.06).convert("RGBA")
        z = lerp(1.0, 1.6, u) if v in ("eyelash", "eyelash_gone") else 1.0
        e = self.env.resize((int(self.env.size[0] * z), int(self.env.size[1] * z)), Image.BILINEAR)
        ex, ey = W / 2, H * 0.5 + (120 * u if z > 1 else 0)
        paste(fr, e, ex, ey, "cm"); d = ImageDraw.Draw(fr, "RGBA")
        if v == "probe":
            k = clamp((t - 0.8) / max(1, self.dur - 2))
            x0 = ex - 520; y0 = ey - e.size[1] / 2 + 80
            d.line([(x0 - 200 + 500 * k, y0 - 20), (x0 + 700 + 500 * k, y0 - 20)], fill=(170, 172, 176, 255), width=6)
            d.rounded_rectangle([x0 + 100 + 500 * k, y0 - 42, x0 + 520 + 500 * k, y0 + 2], 20, fill=(232, 226, 204, 255), outline=(150, 140, 120))
        if v in ("eyelash", "eyelash_gone", "lab"):
            mx, my, mr = W * 0.52, H * 0.42, 210
            lens = fr.crop((int(mx - mr / 1.6), int(my - mr / 1.6), int(mx + mr / 1.6), int(my + mr / 1.6))).resize((mr * 2, mr * 2), Image.BICUBIC)
            if v == "eyelash" or (v == "lab" and t < self.dur * 0.5):
                ld = ImageDraw.Draw(lens); ld.arc([mr - 90, mr - 30, mr + 90, mr + 120], 200, 290, fill=(20, 16, 14), width=4)
            if v == "eyelash_gone":
                ld = ImageDraw.Draw(lens); ld.text((mr, mr), "?", font=font(F_BEBAS, 160), fill=(150, 30, 24, 200), anchor="mm")
            m = Image.new("L", lens.size, 0); ImageDraw.Draw(m).ellipse([0, 0, mr * 2, mr * 2], fill=255)
            fr.paste(lens, (int(mx - mr), int(my - mr)), m)
            d = ImageDraw.Draw(fr, "RGBA"); d.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=(30, 30, 30, 255), width=14)
            d.line([(mx + mr * 0.7, my + mr * 0.7), (mx + mr * 1.5, my + mr * 1.6)], fill=(30, 24, 20, 255), width=30)
        arr = np.asarray(fr, np.float32); arr[..., :3] *= (0.5 + 0.65 * radial(W, H, W * 0.5, H * 0.35, W * 0.85)[..., None])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"), t)


@scene("briefcase")
class Briefcase(Base):
    def setup(self):
        v = self.p.get("variant", "day"); self.v = v
        self.bg = desk(97) if v in ("desk", "chain", "day") else bg_plate(W + 200, H + 120, 33, (4, 6, 10), (24, 32, 44), 0.6, 0.3).convert("RGBA")
        S = 1000; im = Image.new("RGBA", (S + 200, int(S * 0.8)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        bx0, by0, bx1, by1 = 100, 140, 100 + S, 140 + S * 0.58
        d.rounded_rectangle([bx0 + 20, by0 + 30, bx1 + 20, by1 + 30], 40, fill=(0, 0, 0, 160)); im = im.filter(ImageFilter.GaussianBlur(18)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([bx0, by0, bx1, by1], 40, fill=(52, 34, 22)); d.rounded_rectangle([bx0 + 14, by0 + 14, bx1 - 14, by1 - 14], 30, outline=(74, 50, 32), width=4)
        d.rectangle([bx0, by0 + 90, bx1, by0 + 104], fill=(40, 26, 16))
        d.rounded_rectangle([bx0 + S * 0.38, by0 - 80, bx0 + S * 0.62, by0 + 10], 30, outline=(46, 30, 20), width=26)
        for cx in (bx0 + S * 0.28, bx0 + S * 0.72): d.rectangle([cx - 30, by0 + 80, cx + 30, by0 + 120], fill=(170, 150, 100)); d.rectangle([cx - 8, by0 + 96, cx + 8, by0 + 112], fill=(60, 50, 30))
        arr = np.asarray(im).astype(np.float32); n = smooth_noise(im.size[0], im.size[1], 6, 4, 2)
        arr[..., :3] *= (0.85 + 0.3 * n[..., None]); self.case = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    def frame(self, t):
        u = ease_in_out(self.u(t)); fr = kb_transform(self.bg, u, 1.0, 1.08).convert("RGBA")
        s = lerp(0.95, 1.08, u); c = self.case.resize((int(self.case.size[0] * s), int(self.case.size[1] * s)), Image.BILINEAR)
        paste(fr, c, W / 2 + 40 * (u - 0.5), H * 0.56, "cm")
        d = ImageDraw.Draw(fr, "RGBA")
        if self.v in ("chain", "day", "night"):
            hx, hy = W / 2 - 20, H * 0.56 - c.size[1] * 0.42
            for k in range(26):
                x = hx - k * 30; y = hy + k * 3 + 26 * math.sin(k * 0.16)
                d.ellipse([x - 16, y - 10, x + 16, y + 10], outline=(120, 92, 60, 255), width=6)
        arr = np.asarray(fr, np.float32)
        if self.v == "night": arr[..., :3] *= (0.25 + 0.9 * radial(W, H, W * 0.5, H * 0.45, W * 0.55)[..., None]) * np.array([0.8, 0.9, 1.1])
        else: arr[..., :3] *= (0.5 + 0.7 * radial(W, H, W * 0.5, H * 0.35, W * 0.8)[..., None])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"), t)


@scene("canister")
class Canister(Base):
    def setup(self):
        self.bg = bg_plate(W + 200, H + 120, 35, (8, 9, 11), (40, 44, 48), 0.5, 0.25).convert("RGBA")
        w, h = 760, 900; arr = np.zeros((h, w, 4), np.float32); x = np.linspace(-1, 1, w)[None, :]
        shade = 0.35 + 0.65 * np.clip(1 - (x + 0.35) ** 2, 0, 1); arr[..., :3] = (shade * 150)[..., None] * np.array([0.95, 1.0, 1.05]); arr[..., 3] = 255
        im = Image.fromarray(arr.astype(np.uint8), "RGBA"); d = ImageDraw.Draw(im)
        for y in (60, h - 60): d.rectangle([0, y - 14, w, y + 14], fill=(90, 94, 98))
        for i, line in enumerate(["HANDLE WITH CARE", "OPTICAL", "INSTRUMENTS"]):
            d.text((w / 2, 340 + i * 110), line, font=font(F_BEBAS, 96), fill=(30, 30, 30), anchor="mm")
        self.can = im
    def frame(self, t):
        u = ease_in_out(self.u(t)); fr = kb_transform(self.bg, u, 1.0, 1.06).convert("RGBA")
        paste(fr, self.can, W / 2, H * 0.52, "cm")
        vap = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(vap); rng = random.Random(4)
        for k in range(40):
            ph = (t * 0.12 + rng.random()) % 1; x = W / 2 + rng.uniform(-420, 420); y = H * 0.9 - ph * 300
            r = 40 + 80 * ph; d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=(220, 230, 240, int(60 * math.sin(math.pi * ph))))
        fr.alpha_composite(vap.filter(ImageFilter.GaussianBlur(20)))
        return self.post(fr, t)


# ═════════════════════════ ENVIRONMENTS ═════════════════════════
@scene("london")
class London(Base):
    def setup(self):
        self.v = self.p.get("variant", "day"); self.sky, self.bl, self.st, self.lamp = london_layers(self.v)
    def frame(self, t):
        u = ease_in_out(self.u(t)); ox = int((60 + 300 * u) if not self.alt else (360 - 300 * u))
        fr = self.sky.crop((ox // 3, 0, ox // 3 + W, H)).copy()
        fr.alpha_composite(self.bl.crop((ox // 2, 0, ox // 2 + W, H))); fr.alpha_composite(self.st.crop((ox, 0, ox + W, H)))
        if self.v.startswith("night"):
            arr = np.asarray(fr, np.float32); lx = self.lamp[0] - ox
            arr[..., :3] += radial(W, H, lx, self.lamp[1] + 40, 380)[..., None] ** 2 * np.array([90, 70, 40])
            arr[int(H * 0.75):, :, :3] += (radial(W, H, lx, H * 0.95, 300)[int(H * 0.75):] ** 2)[..., None] * np.array([60, 50, 30])
            fr = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"); fr.alpha_composite(rain_layer(3, t))
        return self.post(fr, t)


@scene("valleys")
class Valleys(Base):
    def setup(self):
        self.v = self.p.get("variant", "day"); self.sky, self.layers, self.smoke = valley_layers(self.v)
    def frame(self, t):
        u = ease_in_out(self.u(t)); fr = self.sky.crop((int(40 * u), 0, int(40 * u) + W, H)).copy()
        for i, lay in enumerate(self.layers):
            ox = int((60 + 90 * i) * u); fr.alpha_composite(lay.crop((ox, 0, ox + W, H)))
            if i == 2: sx = int((t * 18) % 400); fr.alpha_composite(self.smoke.crop((sx, 0, sx + W, 400)), (0, int(H * 0.28)))
        return self.post(fr, t)


@scene("office")
class Office(Base):
    def setup(self): self.plate = office_plate(self.p.get("variant", "day"))
    def frame(self, t):
        u = ease_in_out(self.u(t)); c1 = (0.56, 0.48) if not self.alt else (0.44, 0.52)
        fr = kb_transform(self.plate, u, 1.0, 1.12, (0.5, 0.5), c1).convert("RGBA")
        return self.post(fr, t, dust=True)


@scene("huelva_day")
class HuelvaDay(Base):
    def setup(self): self.plate = huelva_plate()
    def frame(self, t):
        fr = kb_transform(self.plate, ease_in_out(self.u(t)), 1.0, 1.1, (0.45, 0.5), (0.55, 0.48)).convert("RGBA")
        return self.post(fr, t, dust=True)


@scene("road")
class Road(Base):
    def setup(self):
        self.trees = forest_hedge()
    def frame(self, t):
        fr = Image.new("RGBA", (W, H), (3, 4, 7, 255)); d = ImageDraw.Draw(fr, "RGBA"); vx, vy = W / 2, H * 0.5
        d.polygon([(vx - 8, vy), (vx + 8, vy), (W * 0.85, H), (W * 0.15, H)], fill=(16, 16, 18, 255))
        ox = int((t * 140) % 1000); fr.alpha_composite(self.trees.crop((ox, 0, ox + W, H)))
        # masked headlights: two narrow slit beams
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
        g.polygon([(W * 0.3, H), (vx - 60, vy + 120), (vx + 60, vy + 120), (W * 0.7, H)], fill=(200, 190, 150, 50))
        fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(30)))
        rng = random.Random(int(t * 3))
        for k in range(8):
            z = ((t * 12 + k * 6) % 48) + 2; y = vy + 800 / z; ww = 3 + 60 / z
            d.line([(vx - ww, y), (vx + ww, y)], fill=(70, 70, 64, 160), width=max(1, int(12 / z)))
        d.rectangle([0, H * 0.86, W, H], fill=(4, 4, 5, 255)); d.rectangle([0, 0, W, H * 0.07], fill=(4, 4, 5, 255))
        return self.post(fr, t)


@functools.lru_cache(None)
def forest_hedge():
    from props import forest_layer
    return forest_layer(W * 2, H, 33, 70, 80, 220, int(H * 0.52), (8, 10, 12, 255), 3, 8)


@scene("fleet")
class Fleet(Base):
    def setup(self):
        self.oc = Ocean(self.dur, [], dict(variant="dawn", still=False))
        rng = random.Random(7); sil = (46, 40, 48, 255)
        self.ships = [(rng.uniform(-100, W), HOR["dawn"] * H + rng.uniform(2, 30), ship_sprite(int(rng.uniform(140, 320)), rng.choice(["lst", "destroyer", "transport"]), sil)) for _ in range(22)]
        self.lcs = [(rng.uniform(0, W), H * rng.uniform(0.66, 0.82), landing_craft(int(rng.uniform(160, 300)), (24, 22, 26, 255))) for _ in range(6)]
    def frame(self, t):
        fr = self.oc.frame(t); u = self.u(t)
        for x, y, s in sorted(self.ships, key=lambda q: q[1]):
            fr.alpha_composite(s, (int(x + 30 * u), int(y - s.size[1] * 0.9)))
        for x, y, s in self.lcs:
            xx = x - 140 * t * 0.3; fr.alpha_composite(s, (int(xx) % (W + 300) - 300, int(y - s.size[1] * 0.85 + math.sin(t * 1.4 + x) * 5)))
        return self.post(fr, t)


@scene("silhouette")
class Silhouette(Base):
    def setup(self):
        self.bg = bg_plate(W + 200, H + 120, 55, (6, 6, 8), (40, 34, 28), 0.5, 0.3).convert("RGBA")
        S = 900; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = S / 2
        d.ellipse([c - 70, 160, c + 70, 330], fill=(4, 4, 5)); d.polygon([(c - 150, 210), (c + 150, 210), (c + 110, 180), (c - 110, 180)], fill=(4, 4, 5))
        d.polygon([(c - 60, 170), (c + 60, 170), (c + 50, 110), (c - 50, 110)], fill=(4, 4, 5))
        d.polygon([(c - 70, 320), (c + 70, 320), (c + 220, 400), (c + 250, S), (c - 250, S), (c - 220, 400)], fill=(4, 4, 5))
        self.fig = im
    def frame(self, t):
        u = ease_in_out(self.u(t)); fr = kb_transform(self.bg, u, 1.0, 1.06).convert("RGBA")
        paste(fr, self.fig, W * 0.32, H * 0.62, "cm")
        name_tag(fr, self.p.get("label"), self.p.get("sub"), ramp(t, 0.4, 0.7))
        return self.post(fr, t)


# ═════════════════════════ OBJECTS / RECREATIONS ═════════════════════════
@scene("litter")
class Litter(Base):
    def setup(self):
        self.d = desk(99); rng = random.Random(3); self.items = []
        P = Image.new("RGBA", (W + 200, H + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(P)
        def item(img, x, y, rot): P.alpha_composite(img.rotate(rot, expand=True, resample=Image.BICUBIC), (int(x - img.size[0] / 2), int(y - img.size[1] / 2)))
        # letters
        for k, (x, y, r) in enumerate([(520, 380, 8), (640, 450, -5)]):
            s = paper_sheet(380, 480, 20 + k, tone=(226, 222, 236)).copy(); dd = ImageDraw.Draw(s); abstract_lines(dd, 80, 110, 360, 10, k, col=(60, 70, 140), gap=34, width=2); item(s, x, y, r)
        # tickets
        for k in range(2):
            tk = Image.new("RGBA", (300, 130), (196, 160, 120, 255)); dd = ImageDraw.Draw(tk); dd.rectangle([6, 6, 293, 123], outline=(120, 80, 50), width=3)
            dd.text((150, 45), "THEATRE", font=font(F_OSW_B, 34), fill=(90, 40, 30), anchor="mm"); dd.text((150, 92), "STALLS  ·  ADMIT ONE", font=font(F_OSW, 22), fill=(90, 40, 30), anchor="mm")
            item(tk, 1180 + k * 60, 330 + k * 40, -12 + k * 18)
        # keys, cross, medallion, cigarettes, stamps
        for k in range(3): d.ellipse([1300 + k * 30, 700, 1340 + k * 30, 740], outline=(170, 150, 100), width=8); d.rectangle([1336 + k * 30, 714, 1420 + k * 30, 726], fill=(170, 150, 100))
        d.rectangle([900, 760, 1060, 860], fill=(200, 40, 34)); d.text((980, 810), "CIGARETTES", font=font(F_OSW_B, 22), fill=(240, 230, 200), anchor="mm")
        d.ellipse([1560, 620, 1640, 700], fill=(190, 190, 194)); d.text((1600, 660), "S", font=font(F_SERIF, 40), fill=(90, 90, 96), anchor="mm")
        d.rectangle([1700, 560, 1716, 680], fill=(200, 200, 206)); d.rectangle([1670, 590, 1746, 606], fill=(200, 200, 206))
        d.rectangle([700, 800, 830, 880], fill=(170, 40, 40)); d.text((765, 840), "STAMPS", font=font(F_OSW_B, 20), fill=(250, 240, 220), anchor="mm")
        self.layer = P
        try:
            pam, _ = load_arch("pam"); s = 330 / pam.size[0]; pm = pam.resize((330, int(pam.size[1] * s)))
            fr_ = Image.new("RGBA", (pm.size[0] + 30, pm.size[1] + 30), (240, 236, 226, 255)); fr_.paste(pm, (15, 15)); item(fr_, 920, 420, 4)
        except Exception: pass
        self.focus = {"all": ((0.5, 0.5), 1.0, 1.1), "tickets": ((0.62, 0.32), 1.3, 1.6), "items": ((0.72, 0.62), 1.3, 1.6)}[self.p.get("focus", "all")]
    def frame(self, t):
        u = ease_in_out(self.u(t)); base = self.d.copy(); base.alpha_composite(self.layer)
        (cx, cy), z0, z1 = self.focus
        fr = kb_transform(base, u, z0, z1, (0.5, 0.5) if z0 == 1 else (cx - 0.05, cy), (cx, cy)).convert("RGBA")
        arr = np.asarray(fr, np.float32); arr[..., :3] *= (0.5 + 0.65 * radial(W, H, W * 0.5, H * 0.4, W * 0.8)[..., None])
        return self.post(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"), t)


@scene("calendar")
class Calendar(Base):
    def setup(self): self.d = desk(101)
    def frame(self, t):
        fr = kb_transform(self.d, self.u(t), 1.0, 1.06).convert("RGBA")
        sh = paper_sheet(1200, 760, 11, tone=(236, 230, 214)).copy(); d = ImageDraw.Draw(sh)
        d.text((640, 120), "APRIL 1943", font=font(F_BEBAS, 90), fill=(40, 34, 30), anchor="mm")
        for i, dn in enumerate("MTWTFSS"): d.text((170 + i * 150, 210), dn, font=font(F_OSW_B, 30), fill=(120, 110, 100), anchor="mm")
        day = 1; start = 3  # 1 April 1943 was a Thursday
        for wk in range(5):
            for dw in range(7):
                idx = wk * 7 + dw - start + 1
                if 1 <= idx <= 30:
                    x, y = 170 + dw * 150, 290 + wk * 92
                    hot = 18 <= idx <= 24 and t > 0.8 + (idx - 18) * 0.35
                    if hot: d.ellipse([x - 36, y - 36, x + 36, y + 36], outline=(150, 30, 24), width=5)
                    d.text((x, y), str(idx), font=font(F_OSW, 36), fill=(30, 28, 26) if not hot else (150, 30, 24), anchor="mm")
        paste(fr, sh, W / 2, H * 0.46, "cm")
        return self.post(fr, t)


@scene("dossier")
class Dossier(Base):
    def setup(self):
        self.d = desk(103); sh = paper_sheet(1150, 820, 13, tone=(222, 206, 164)).copy(); d = ImageDraw.Draw(sh)
        rows = [("NAME", "WILLIAM MARTIN"), ("RANK", "CAPTAIN (ACTING MAJOR)"), ("SERVICE", "ROYAL MARINES"), ("POSTING", "COMBINED OPERATIONS HQ"), ("STATUS", "FICTITIOUS")]
        d.text((120, 110), "THE 'LEGEND'  ·  AS DESIGNED BY MONTAGU & CHOLMONDELEY", font=font(F_TYPE, 30), fill=(120, 34, 28))
        self.rows = rows; self.sheet = sh
    def frame(self, t):
        fr = kb_transform(self.d, self.u(t), 1.0, 1.06).convert("RGBA"); sh = self.sheet.copy(); d = ImageDraw.Draw(sh)
        for i, (k, v) in enumerate(self.rows):
            a = ramp(t, 0.3 + i * 0.5, 0.3)
            if a <= 0: continue
            d.text((140, 220 + i * 100), k + ":", font=font(F_TYPE, 36), fill=(90, 80, 66)); d.text((420, 220 + i * 100), v, font=font(F_TYPE, 44), fill=(150, 30, 24) if k == "STATUS" else (30, 28, 26))
        paste(fr, sh, W / 2, H * 0.47, "cm")
        return self.post(fr, t)


@scene("uniform")
class Uniform(Base):
    def setup(self):
        self.bg = office_plate("day")
        im = Image.new("RGBA", (700, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 350; col = (78, 74, 52)
        d.line([(c - 160, 120), (c, 40), (c + 160, 120)], fill=(70, 50, 30), width=12); d.arc([c - 20, 0, c + 20, 50], 180, 360, fill=(140, 140, 140), width=6)
        d.polygon([(c - 200, 130), (c + 200, 130), (c + 230, 620), (c - 230, 620)], fill=col)
        d.polygon([(c - 200, 130), (c - 300, 520), (c - 250, 540), (c - 170, 260)], fill=col); d.polygon([(c + 200, 130), (c + 300, 520), (c + 250, 540), (c + 170, 260)], fill=col)
        d.rectangle([c - 230, 560, c + 230, 620], fill=(66, 62, 44)); d.line([(c, 160), (c, 620)], fill=(54, 50, 36), width=4)
        for y in (230, 330, 430): d.ellipse([c - 12, y - 12, c + 12, y + 12], fill=(40, 38, 28))
        for sx in (-1, 1): d.rectangle([c + sx * 140 - 40, 260, c + sx * 140 + 40, 330], outline=(54, 50, 36), width=4)
        d.text((c - 170, 160), "ROYAL MARINES", font=font(F_OSW_B, 18), fill=(200, 60, 50))
        self.u_ = im
    def frame(self, t):
        u = ease_in_out(self.u(t)); fr = kb_transform(self.bg, u, 1.05, 1.15).convert("RGBA")
        arr = np.asarray(fr, np.float32); arr[..., :3] *= 0.6; fr = Image.fromarray(arr.astype(np.uint8), "RGBA")
        paste(fr, self.u_.rotate(math.sin(t * 0.8) * 1.2, resample=Image.BICUBIC), W * 0.5, H * 0.52, "cm")
        return self.post(fr, t)


@scene("books")
class Books(Base):
    def setup(self):
        self.d = desk(105); self.covers = []
        for title, author, yr, col in (("OPERATION HEARTBREAK", "DUFF COOPER", "1950", (60, 30, 30)), ("THE MAN WHO NEVER WAS", "EWEN MONTAGU", "1953", (24, 34, 54))):
            im = Image.new("RGBA", (520, 780), col + (255,)); d = ImageDraw.Draw(im); d.rectangle([20, 20, 500, 760], outline=(200, 180, 120), width=3)
            for i, ln in enumerate(wrap_text(title, font(F_BEBAS, 84), 440)): d.text((260, 200 + i * 90), ln, font=font(F_BEBAS, 84), fill=(230, 210, 150), anchor="mm")
            d.text((260, 600), author, font=font(F_OSW, 34), fill=(220, 214, 200), anchor="mm"); d.text((260, 680), yr, font=font(F_OSW, 30), fill=(200, 180, 120), anchor="mm")
            self.covers.append(im)
    def frame(self, t):
        fr = kb_transform(self.d, self.u(t), 1.0, 1.08).convert("RGBA")
        for i, c in enumerate(self.covers):
            a = ramp(t, 0.3 + i * 1.2, 0.6); paste(fr, c.rotate(-5 + i * 9, expand=True, resample=Image.BICUBIC), W * (0.36 + 0.28 * i), H * 0.5 + 30 * (1 - a), "cm", a)
        return self.post(fr, t)


@scene("archive")
class Archive(Base):
    def setup(self):
        img = Image.new("RGB", (W + 200, H + 120), (20, 18, 16)); d = ImageDraw.Draw(img); rng = random.Random(9)
        for row in range(6):
            y = 80 + row * 190; d.rectangle([0, y + 150, W + 200, y + 166], fill=(60, 48, 36))
            x = 20
            while x < W + 180:
                bw = rng.uniform(90, 150); c = rng.choice([(110, 96, 70), (130, 110, 80), (96, 84, 62)])
                d.rectangle([x, y + 20, x + bw, y + 150], fill=c, outline=(50, 40, 30)); d.rectangle([x + bw * 0.2, y + 50, x + bw * 0.8, y + 80], fill=(220, 210, 186)); x += bw + 6
        arr = np.asarray(img, np.float32) * (0.35 + 0.9 * radial(W + 200, H + 120, (W + 200) * 0.5, (H + 120) * 0.45, W * 0.7)[..., None])
        self.plate = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    def frame(self, t):
        return self.post(kb_transform(self.plate, ease_in_out(self.u(t)), 1.0, 1.15, (0.4, 0.5), (0.6, 0.5)).convert("RGBA"), t, dust=True)


@scene("bars")
class Bars(Base):
    def setup(self): self.plate = bg_plate(W, H, 140, (8, 9, 12), (26, 28, 34), 0.3, 0.3, 0.05).convert("RGBA")
    def frame(self, t):
        fr = self.plate.copy(); d = ImageDraw.Draw(fr, "RGBA")
        paste(fr, text_img("OPERATION HUSKY  ·  EXPECTED vs. ACTUAL", font(F_OSW_B, 34), WHITE, tracking=5), 200, 170, "lm", ramp(t, 0, 0.6))
        rows = [("CASUALTIES, FIRST WEEK", 10000, 10000 / 7, "ABOUT 10,000", "ABOUT ONE-SEVENTH"), ("SHIPS LOST", 300, 12, "UP TO 300", "12"), ("CAMPAIGN LENGTH (DAYS)", 90, 38, "90", "38")]
        cues = [c["s"] for c in self.cues] if self.cues else [0.5, 3, 6]
        for i, (lab, exp, act, te, ta) in enumerate(rows):
            y = 300 + i * 190; t0 = 0.4 + i * self.dur * 0.25; a = ramp(t, t0, 0.5)
            if a <= 0: continue
            paste(fr, text_img(lab, font(F_OSW, 24), DIM, tracking=4), 200, y - 34, "lm", a)
            g = ease_out(clamp((t - t0) / 1.2)); w = 1250 * g
            d.rectangle([200, y, 200 + w, y + 40], fill=(90, 96, 108, int(220 * a))); paste(fr, text_img("EXPECTED " + te, font(F_OSW_B, 24), WHITE, tracking=3), 210 + w + 14, y + 20, "lm", a)
            g2 = ease_out(clamp((t - t0 - 1.0) / 1.0)); w2 = 1250 * act / exp * g2
            d.rectangle([200, y + 52, 200 + w2, y + 92], fill=GOLD + (int(235 * a),)); paste(fr, text_img("ACTUAL " + ta, font(F_OSW_B, 24), GOLD, tracking=3), 210 + w2 + 14, y + 72, "lm", a * g2)
        paste(fr, text_img("Figures as given by Ben Macintyre, 'Operation Mincemeat' (2010).", font(F_INTER, 22), DIM), 200, 900, "lm", ramp(t, 1.5, 0.8))
        return self.post(fr, t, tagtxt="DATA")


@scene("split")
class Split(Base):
    def setup(self): self.plate = bg_plate(W, H, 150, (8, 9, 12), (26, 26, 30), 0.5, 0.3, 0.05).convert("RGBA")
    def frame(self, t):
        fr = self.plate.copy(); d = ImageDraw.Draw(fr, "RGBA")
        d.line([(W / 2, 220), (W / 2, 220 + 560 * ease_out(ramp(t, 0, 0.8)))], fill=(100, 104, 112, 255), width=2)
        paste(fr, text_img("THE DECEPTION", font(F_BEBAS, 64), GOLD, tracking=6), W * 0.27, 260, "cm", ramp(t, 0.1, 0.6))
        paste(fr, text_img("OTHER FACTORS", font(F_BEBAS, 64), (170, 180, 195), tracking=6), W * 0.73, 260, "cm", ramp(t, 0.5, 0.6))
        L = ["Operation Mincemeat", "Operation Barclay (wider deception)"]; R = ["Hitler's long-standing Balkan obsession", "Hitler's distrust of his Italian allies", "Allied strength and planning"]
        for i, s in enumerate(L): paste(fr, text_img(s, font(F_INTER_M, 34), WHITE), 190, 400 + i * 90, "lm", ramp(t, 0.5 + i * 0.4, 0.5))
        for i, s in enumerate(R): paste(fr, text_img(s, font(F_INTER_M, 34), WHITE), W / 2 + 110, 400 + i * 90, "lm", ramp(t, 1.2 + i * 0.5, 0.5))
        return self.post(fr, t, tagtxt="ANALYSIS")
