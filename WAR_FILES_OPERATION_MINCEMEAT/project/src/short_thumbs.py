"""Vertical covers (1080x1920) for the Short — playbook rules: thirds, ≤4 words, channel palette + red accent,
text kept in the central safe zone (Shorts UI covers top/bottom)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from short_render import (photo, cover, print_card, shadowed, stamp, marker_circle, base_bg, bg_blur, rotated, glow,
                          font, text_img, paste, F_BEBAS, F_OSW_B, SW, SH, GOLD, OFF, RED, CRED)
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "SHORT")

def finish(fr):
    arr = np.asarray(fr.convert("RGB")).astype(np.float32)
    yy, xx = np.mgrid[0:SH, 0:SW]; r = np.sqrt(((xx - SW / 2) / (SW * .75)) ** 2 + ((yy - SH / 2) / (SH * .7)) ** 2)
    arr *= (1 - 0.5 * np.clip(r - .35, 0, 1) ** 1.3)[..., None]
    arr += np.random.default_rng(1).normal(0, 5, arr.shape[:2])[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))

def head(fr, text, y):
    t = text_img(text, font(F_OSW_B, 40), fill=GOLD, tracking=8); paste(fr, t, 80, y)
    ImageDraw.Draw(fr).line((80, y + 58, 80 + t.width, y + 58), fill=GOLD + (230,), width=4)

def big(fr, lines, y, size=210):
    for txt, col in lines:
        t = text_img(txt, font(F_BEBAS, size), fill=col, tracking=4)
        sh = text_img(txt, font(F_BEBAS, size), fill=(0, 0, 0), tracking=4).filter(ImageFilter.GaussianBlur(10))
        paste(fr, sh, 86, y + 8, opacity=0.9)
        if col == RED: paste(fr, glow(t, 22, 1.2), 80, y, opacity=0.45)
        paste(fr, t, 80, y); y += int(size * 0.9)
    return y

# A — the grave, name circled + NEVER EXISTED
def thumb_A():
    fr = Image.new("RGBA", (SW, SH), (10, 11, 14, 255)); fr.alpha_composite(bg_blur("grave", False))
    W_, H_ = 940, 880; img = cover(photo("grave"), W_, H_, 1.5, (0.565, 0.258))
    card = rotated(shadowed(print_card(img, W_, H_, CRED["grave"]["credit"])), -1.5)
    paste(fr, card, SW / 2, 380 + H_ / 2, "cm")
    marker_circle(fr, SW / 2, 380 + H_ / 2 + 20, 270, 62, 1.0, width=12)
    head(fr, "HUELVA · SPAIN · 1943", 250)
    big(fr, [("HE NEVER", OFF), ("EXISTED", RED)], 1290)
    return finish(fr)

# B — Hitler + BELIEVED IT stamp
def thumb_B():
    fr = Image.new("RGBA", (SW, SH), (10, 11, 14, 255)); fr.alpha_composite(bg_blur("hitler", True))
    W_, H_ = 940, 880; img = cover(photo("hitler", True), W_, H_, 1.6, (0.42, 0.24))
    card = rotated(shadowed(print_card(img, W_, H_, CRED["hitler"]["credit"])), 1.5)
    paste(fr, card, SW / 2, 380 + H_ / 2, "cm")
    st = stamp("FOOLED", 190, rot=-12, seed=4); paste(fr, st, SW / 2 + 140, 1080, "cm")
    head(fr, "SECRET MISSION · 1943", 250)
    big(fr, [("BY A", OFF), ("DEAD MAN", RED)], 1290)
    return finish(fr)

if __name__ == "__main__":
    for n, f in (("A_NEVER_EXISTED", thumb_A), ("B_HITLER_FOOLED", thumb_B)):
        im = f()
        im.convert("RGB").save(os.path.join(OUT, f"SHORT_COVER_{n}.jpg"), quality=92); print("ok", n)
