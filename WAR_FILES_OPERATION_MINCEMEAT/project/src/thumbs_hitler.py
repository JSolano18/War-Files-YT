"""Thumbnail V4 — 'famous face' + simple object + bold statement (WAR_FILES_PLAYBOOK).
Hitler (photo supplied by the channel owner) on the right third, the fake identity card on the left third,
statement text in the lower right. Swastika armband cropped out. Red accent = this video's accent colour."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from common import font, text_img, paste, radial, smooth_noise, F_TYPE
from thumbs_m import TW, TH, grade
from thumbs_v2 import word, burn, GOLD, WHT, ACC, X3, Y3
P = os.path.join(os.path.dirname(__file__), ".."); OUT = os.path.join(P, "..", "thumbnails")


def hitler_layer():
    im = Image.open(os.path.join(P, "assets", "user", "hitler_speech_user.webp")).convert("RGB")
    w, h = im.size
    im = im.crop((60, 0, int(w * 0.86), int(h * 0.80)))          # removes the armband (bottom-right) and the left edge
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    a = np.asarray(g, np.float32) / 255
    a = np.clip((a - 0.5) * 1.25 + 0.5, 0, 1)                    # punchier contrast
    rgb = np.stack([a * 236 + 10, a * 226 + 4, a * 214 + 2], -1)  # warm monochrome
    s = TH * 1.05 / im.size[1]
    lay = Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).resize((int(im.size[0] * s), int(im.size[1] * s)), Image.LANCZOS).convert("RGBA")
    lw, lh = lay.size
    # soft left / bottom fade so the photo melts into the dark background
    xx = np.linspace(0, 1, lw)[None, :]; yy = np.linspace(0, 1, lh)[:, None]
    m = np.clip(xx / 0.30, 0, 1) ** 1.4 * np.clip((1 - yy) / 0.22, 0, 1) ** 0.8
    arr = np.asarray(lay).copy(); arr[..., 3] = (m * 255).astype(np.uint8)
    # red rim / side light from the right
    rl = np.clip((xx - 0.55) / 0.45, 0, 1) ** 2
    arr[..., 0] = np.clip(arr[..., 0] + rl * 70 * a.mean(), 0, 255)
    return Image.fromarray(arr, "RGBA")


def id_card(angle=5, scale=0.78):
    card = Image.new("RGBA", (1500, 1000), (226, 214, 184, 255)); d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 1499, 999], outline=(120, 100, 70), width=10)
    d.text((60, 50), "IDENTITY  ·  ROYAL MARINES", font=font(F_TYPE, 64), fill=(110, 40, 30))
    for i, (k, v) in enumerate([("NAME", "WILLIAM MARTIN"), ("RANK", "CAPT. (A/MAJOR)"), ("POSTED", "COMBINED OPS HQ")]):
        d.text((600, 200 + i * 150), k, font=font(F_TYPE, 46), fill=(90, 80, 66)); d.text((600, 255 + i * 150), v, font=font(F_TYPE, 70), fill=(30, 28, 26))
    ph = Image.new("RGBA", (440, 560), (40, 40, 42, 255)); pd = ImageDraw.Draw(ph)
    pd.ellipse([140, 120, 300, 300], fill=(16, 16, 18)); pd.pieslice([60, 280, 380, 700], 180, 360, fill=(16, 16, 18))
    card.alpha_composite(ph.filter(ImageFilter.GaussianBlur(14)), (80, 200)); d.rectangle([80, 380, 520, 470], fill=(12, 12, 12))
    card.alpha_composite(word("FICTITIOUS", 190, ACC, track=10).rotate(-12, expand=True, resample=Image.BICUBIC), (330, 470))
    card = card.resize((int(1500 * scale), int(1000 * scale)), Image.LANCZOS).rotate(angle, expand=True, resample=Image.BICUBIC)
    return card


def compose(line1, line2):
    n = smooth_noise(TW, TH, 50, 5, 3); bg = np.array([22, 16, 12], np.float32) * (0.55 + 0.7 * n)[..., None]
    bg *= (0.30 + 0.9 * radial(TW, TH, TW * 0.3, TH * 0.5, TW * 0.6) ** 1.2)[..., None]
    cv = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
    hl = hitler_layer()
    # face lands near the top-right rule-of-thirds intersection
    paste(cv, hl, TW + 40, -20, "rt")
    cv = burn(cv, TW * 0.74, TH * 0.76, TW * 0.30, TH * 0.22, 0.75)     # dark bed for the text
    card = id_card()
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").point(lambda v: v * 0.8))
    paste(cv, sh.filter(ImageFilter.GaussianBlur(30)), X3 - 20, TH * 0.60, "cm"); paste(cv, card, X3 - 60, TH * 0.56, "cm")
    cv = grade(cv, red=0.15)
    paste(cv, word(line1, 220, WHT, track=8), TW * 0.725, TH * 0.635, "cm")
    paste(cv, word(line2, 250, ACC, track=8, glow_col=(255, 80, 60)), TW * 0.725, TH * 0.785, "cm")
    return cv


if __name__ == "__main__":
    for nm, (a, b) in (("V4_HITLER_NEVER_EXISTED", ("HE NEVER", "EXISTED")), ("V5_HITLER_BELIEVED_IT", ("AND HE", "BELIEVED IT"))):
        im = compose(a, b).convert("RGB").resize((1280, 720), Image.LANCZOS); im.save(os.path.join(OUT, f"THUMBNAIL_{nm}.png")); print(nm)
