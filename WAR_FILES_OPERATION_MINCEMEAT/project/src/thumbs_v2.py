"""Thumbnails v2 — built with WAR_FILES_PLAYBOOK/TITULOS_Y_MINIATURAS.md
Rule of thirds · channel palette (gold/black/off-white/steel) + accent RED for this video · Bebas/Oswald · 3 different types."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import font, text_img, paste, radial, smooth_noise, F_BEBAS, F_OSW_B, F_OSW, F_TYPE
from thumbs_m import sea_scene, officer, grade, europe_ghost, TW, TH
GOLD = (201, 165, 76); BLK = (10, 11, 14); WHT = (242, 239, 232); STEEL = (118, 128, 138); ACC = (232, 52, 42)
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "thumbnails")
X3, Y3 = TW / 3, TH / 3     # rule-of-thirds lines


def burn(cv, cx, cy, rx, ry, strength=0.6):
    """dodge/burn: soft darkening behind text/subject"""
    arr = np.asarray(cv, np.float32).copy(); yy, xx = np.mgrid[:TH, :TW]
    m = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    arr[..., :3] *= (1 - strength * m)[..., None]; return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")


def word(txt, size, col, track=None, glow_col=None):
    f = font(F_BEBAS, size); ti = text_img(txt, f, col, tracking=int(size * 0.035) if track is None else track)
    w, h = ti.size; out = Image.new("RGBA", (w + 160, h + 160), (0, 0, 0, 0))
    a = ti.getchannel("A"); sh = Image.new("RGBA", ti.size, (0, 0, 0, 255)); sh.putalpha(a)
    out.alpha_composite(sh, (80, 94)); out = out.filter(ImageFilter.GaussianBlur(size * 0.06))
    if glow_col:
        g = Image.new("RGBA", ti.size, glow_col + (255,)); g.putalpha(a); gl = Image.new("RGBA", out.size, (0, 0, 0, 0)); gl.alpha_composite(g, (80, 80))
        out.alpha_composite(gl.filter(ImageFilter.GaussianBlur(size * 0.09)))
    out.alpha_composite(ti, (80, 80)); return out


def civilian(h, rim=(255, 170, 110), side=1):
    """flat-cap civilian in a worn overcoat — silhouette (no face, no likeness)"""
    w = int(h * 0.62); m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m); c = w * 0.5; s = h
    d.ellipse([c - 0.045 * s, 0.06 * s, c + 0.045 * s, 0.155 * s], fill=255)
    d.ellipse([c - 0.052 * s, 0.045 * s, c + 0.05 * s, 0.10 * s], fill=255)                                       # flat cap crown
    d.polygon([(c + 0.02 * s, 0.085 * s), (c + 0.085 * s, 0.092 * s), (c + 0.03 * s, 0.10 * s)], fill=255)          # short brim
    d.polygon([(c - 0.03 * s, 0.14 * s), (c + 0.03 * s, 0.14 * s), (c + 0.035 * s, 0.18 * s), (c - 0.035 * s, 0.18 * s)], fill=255)
    coat = [(-0.07, 0.17), (0.07, 0.17), (0.14, 0.21), (0.15, 0.32), (0.16, 0.58), (0.13, 0.6), (0.15, 0.84), (0.05, 0.86), (0.045, 1.0), (-0.045, 1.0), (-0.05, 0.86), (-0.15, 0.84), (-0.13, 0.6), (-0.16, 0.58), (-0.15, 0.32), (-0.14, 0.21)]
    d.polygon([(c + x * s, y * s) for x, y in coat], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.5)); ma = np.asarray(m, np.float32) / 255
    sh = np.roll(ma, -side * int(h * 0.007), axis=1); rimm = np.clip(ma - sh, 0, 1)
    rimm = np.asarray(Image.fromarray((rimm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(h * 0.003)), np.float32) / 255
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = np.array([7, 7, 9]) + rimm[..., None] * np.array(rim) * 1.7; out[..., 3] = np.maximum(ma, rimm) * 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def v1_officer():
    """Type: target emotion + header. Officer on left third line, head near top-left intersection; text on right two thirds."""
    cv, yh = sea_scene("dawn", 0.62, (0.78, 0.55))
    paste(cv, europe_ghost(1600, 950), TW * 0.80, TH * 0.30, "cm", 0.35)
    cv = burn(cv, TW * 0.68, TH * 0.36, TW * 0.40, TH * 0.32, 0.82)
    fig = officer(1180, side=-1); paste(cv, fig, X3, TH * 1.03, "cb")       # figure centred on the left third line
    cv = grade(cv, red=0.22)
    paste(cv, word("SECRET MISSION  ·  1943", 92, GOLD, track=10), TW * 0.68, Y3 * 0.42, "cm")
    paste(cv, word("HE WAS", 260, WHT), TW * 0.68, Y3 * 0.95, "cm")
    paste(cv, word("ALREADY DEAD", 300, ACC, glow_col=(255, 80, 60)), TW * 0.68, Y3 * 1.72, "cm")
    return cv


def v2_dossier():
    """Type: simple + hidden + bold statement. One object (the fake identity file), redacted photo, red stamp."""
    n = smooth_noise(TW, TH, 50, 5, 3); arr = np.array([30, 22, 16], np.float32) * (0.55 + 0.7 * n)[..., None]
    arr *= (0.35 + 1.1 * radial(TW, TH, TW * 0.36, TH * 0.48, TW * 0.6) ** 1.2)[..., None]
    cv = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    card = Image.new("RGBA", (1500, 1000), (226, 214, 184, 255)); d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 1499, 999], outline=(120, 100, 70), width=10)
    d.text((60, 50), "IDENTITY  ·  ROYAL MARINES", font=font(F_TYPE, 64), fill=(110, 40, 30))
    rows = [("NAME", "WILLIAM MARTIN"), ("RANK", "CAPT. (A/MAJOR)"), ("POSTED", "COMBINED OPS HQ")]
    for i, (k, v) in enumerate(rows):
        d.text((600, 200 + i * 150), k, font=font(F_TYPE, 46), fill=(90, 80, 66)); d.text((600, 255 + i * 150), v, font=font(F_TYPE, 70), fill=(30, 28, 26))
    ph = Image.new("RGBA", (440, 560), (40, 40, 42, 255)); pd = ImageDraw.Draw(ph)
    pd.ellipse([140, 120, 300, 300], fill=(16, 16, 18)); pd.pieslice([60, 280, 380, 700], 180, 360, fill=(16, 16, 18))
    ph = ph.filter(ImageFilter.GaussianBlur(14)); card.alpha_composite(ph, (80, 200))
    d.rectangle([80, 380, 520, 470], fill=(12, 12, 12))                                  # redaction bar over the "face"
    st = word("FICTITIOUS", 190, ACC, track=10).rotate(-12, expand=True, resample=Image.BICUBIC)
    card.alpha_composite(st, (330, 470))
    card = card.rotate(4, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").point(lambda v: v * 0.75))
    paste(cv, sh.filter(ImageFilter.GaussianBlur(30)), X3 + 60, TH * 0.56, "cm"); paste(cv, card, X3 + 20, TH * 0.53, "cm")   # object on left third
    cv = burn(cv, TW * 0.84, TH * 0.45, TW * 0.22, TH * 0.5, 0.5)
    cv = grade(cv)
    paste(cv, word("HE", 300, WHT), TW * 0.835, Y3 * 0.95, "cm")
    paste(cv, word("NEVER", 300, WHT), TW * 0.835, Y3 * 1.65, "cm")
    paste(cv, word("EXISTED", 270, ACC, glow_col=(255, 80, 60)), TW * 0.835, Y3 * 2.30, "cm")
    return cv


def v3_same_man():
    """Type: comparison + header. Officer vs civilian silhouettes on the two vertical thirds; 'SAME MAN' in the top third."""
    yy, xx = np.mgrid[:TH, :TW].astype(np.float32)
    left = np.array([18, 30, 52], np.float32); right = np.array([40, 30, 26], np.float32)
    mix = np.clip((xx - TW * 0.45) / (TW * 0.1), 0, 1)[..., None]
    arr = left * (1 - mix) + right * mix
    arr += radial(TW, TH, X3, TH * 0.62, TW * 0.32)[..., None] ** 1.5 * np.array([60, 90, 130])
    arr += radial(TW, TH, 2 * X3, TH * 0.62, TW * 0.32)[..., None] ** 1.5 * np.array([140, 90, 50])
    cv = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    paste(cv, officer(960, rim=(150, 190, 255), side=1, case=False), X3, TH * 1.03, "cb")
    paste(cv, civilian(960, rim=(255, 180, 110), side=-1), 2 * X3, TH * 1.03, "cb")
    d = ImageDraw.Draw(cv, "RGBA"); d.line([(TW / 2, TH * 0.34), (TW / 2, TH)], fill=GOLD + (200,), width=6)
    cv = grade(cv)
    paste(cv, word("SAME MAN", 300, ACC, glow_col=(255, 80, 60)), TW / 2, Y3 * 0.50, "cm")
    for x, nm, sub in ((X3, "MAJOR WILLIAM MARTIN", "ROYAL MARINES"), (2 * X3, "GLYNDWR MICHAEL", "HOMELESS · WALES")):
        paste(cv, word(nm, 96, WHT, track=6), x, TH * 0.86, "cm"); paste(cv, word(sub, 64, GOLD, track=8), x, TH * 0.93, "cm")
    return cv


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for nm, fn in (("V1_SHOCK_OFFICER", v1_officer), ("V2_NEVER_EXISTED", v2_dossier), ("V3_SAME_MAN", v3_same_man)):
        im = fn().convert("RGB").resize((1280, 720), Image.LANCZOS); im.save(os.path.join(OUT, f"THUMBNAIL_{nm}.png")); print(nm)
