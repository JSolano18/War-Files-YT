"""WAR FILES — homepage simulation (thumbsup.tv-style test).
Usage: python3 homepage_test.py OUT.png "Title" thumb1.png [thumb2.png ...]
Renders, for each candidate thumbnail: a YouTube-like dark desktop grid (real ~360px thumbnails) and a mobile feed
column, surrounded by generic placeholder 'competitor' thumbnails typical of history channels. Placeholders are
invented and only for contrast testing."""
import sys, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
FD = os.path.join(os.path.dirname(__file__), "..", "WAR_FILES_OPERATION_MINCEMEAT", "project", "fonts")
def F(n, s): return ImageFont.truetype(os.path.join(FD, n), s)
BEB, INT, INTB = "bebas-neue-latin-400-normal.ttf", "inter-latin-400-normal.ttf", "inter-latin-600-normal.ttf"
COMP = [("THE LAST STAND", "The Last Stand Nobody Talks About", (120, 96, 60), (250, 210, 40)), ("D-DAY", "D-Day: Hour by Hour", (70, 80, 90), (255, 255, 255)),
        ("SECRET BASE", "The Secret Base Hidden for 80 Years", (40, 60, 50), (250, 210, 40)), ("GHOST ARMY", "The Army Made of Balloons", (90, 70, 50), (255, 255, 255)),
        ("1,000 TANKS", "The Biggest Tank Battle in History", (110, 70, 40), (255, 90, 60)), ("LOST SUB", "The Submarine That Vanished", (30, 50, 70), (250, 210, 40)),
        ("WHY?", "Why Stalin Ignored the Warnings", (100, 40, 40), (255, 255, 255)), ("THE BUNKER", "Inside Hitler's Last Bunker", (60, 60, 60), (250, 210, 40))]
def comp_thumb(i, w, h):
    rng = random.Random(i); txt, title, base, tc = COMP[i % len(COMP)]
    a = np.random.default_rng(i).random((h // 8, w // 8)); im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    arr = np.asarray(im, np.float32)[..., None] / 255 * np.array(base) * 1.6 + 20
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([w * 0.05, h * 0.2, w * 0.45, h * 1.2], fill=tuple(int(c * 0.4) for c in base))
    d.text((w * 0.72, h * 0.45), txt, font=F(BEB, int(h * 0.26)), fill=tc, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    return im, title
def card(img, title, chan, w, small=False):
    th = int(w * 9 / 16); im = img.resize((w, th), Image.LANCZOS)
    c = Image.new("RGB", (w, th + (96 if not small else 88)), (15, 15, 15)); m = Image.new("L", (w, th), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, th - 1], 12, fill=255)
    c.paste(im, (0, 0), m); d = ImageDraw.Draw(c)
    d.rounded_rectangle([w - 58, th - 26, w - 6, th - 6], 4, fill=(0, 0, 0)); d.text((w - 32, th - 16), "21:00", font=F(INTB, 13), fill=(255, 255, 255), anchor="mm")
    d.ellipse([0, th + 12, 36, th + 48], fill=(60, 60, 60))
    f = F(INTB, 16 if not small else 15); words = title.split(); lines = []; cur = ""
    for wd in words:
        if d.textlength((cur + " " + wd).strip(), font=f) < w - 50: cur = (cur + " " + wd).strip()
        else: lines.append(cur); cur = wd
    lines.append(cur); lines = lines[:2]
    if len(lines) == 2 and d.textlength(lines[1], font=f) > w - 60: lines[1] = lines[1][:28] + "…"
    for k, l in enumerate(lines): d.text((46, th + 12 + k * 21), l, font=f, fill=(241, 241, 241))
    d.text((46, th + 14 + len(lines) * 21), chan + " · 12K views · 2 days ago", font=F(INT, 13), fill=(170, 170, 170))
    return c
def page(target, title):
    W = 3 * 360 + 4 * 16; out = Image.new("RGB", (W + 40 + 390, 3 * 300 + 120), (15, 15, 15)); d = ImageDraw.Draw(out)
    d.text((20, 20), "DESKTOP HOME (simulation)", font=F(INTB, 18), fill=(150, 150, 150)); d.text((W + 40, 20), "MOBILE FEED (simulation)", font=F(INTB, 18), fill=(150, 150, 150))
    k = 0
    for r in range(3):
        for col in range(3):
            if (r, col) == (1, 1): c = card(target, title, "WAR FILES", 360)
            else: im, t = comp_thumb(k, 640, 360); c = card(im, t, "History Channel", 360); k += 1
            out.paste(c, (16 + col * 376, 60 + r * 300))
    y = 60
    for i in range(3):
        if i == 1: c = card(target, title, "WAR FILES", 390, True)
        else: im, t = comp_thumb(10 + i, 640, 360); c = card(im, t, "History Channel", 390, True)
        out.paste(c, (W + 40, y)); y += c.size[1] + 10
    return out
if __name__ == "__main__":
    outp, title, thumbs = sys.argv[1], sys.argv[2], sys.argv[3:]
    pages = [page(Image.open(t).convert("RGB"), title) for t in thumbs]
    sheet = Image.new("RGB", (pages[0].size[0], sum(p.size[1] for p in pages)), (0, 0, 0)); y = 0
    for p in pages: sheet.paste(p, (0, y)); y += p.size[1]
    sheet.save(outp); print("saved", outp)
