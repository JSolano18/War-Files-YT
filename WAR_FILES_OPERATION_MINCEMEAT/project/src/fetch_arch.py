"""Download chosen Commons files (thumb <=2400px) and record credits. Usage: fetch_arch.py <json with title->info> key=Title ..."""
import json, sys, os, re, time, urllib.request
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research)"}
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "archival"); os.makedirs(OUT, exist_ok=True)
CF = os.path.join(OUT, "credits.json"); credits = json.load(open(CF)) if os.path.exists(CF) else {}
strip = lambda s: re.sub(r"\s+", " ", re.sub("<[^>]+>", "", s or "")).strip()
info = {}
for f in sys.argv[1].split(","): info.update(json.load(open(f)))
for kv in sys.argv[2:]:
    key, title = kv.split("=", 1); v = info[title]; url = v["url"]
    if v.get("w") and v["w"] > 3000 and v.get("thumb"): url = re.sub(r"/\d+px-", "/1920px-", v["thumb"])
    ext = os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"; fn = key + ext
    if not os.path.exists(os.path.join(OUT, fn)):
        for i in range(8):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: open(os.path.join(OUT, fn), "wb").write(r.read()); break
            except Exception as e: print("retry", e); time.sleep(5 + 5 * i)
    artist = strip(v.get("artist")); lic = v.get("license", "")
    credits.setdefault(key, {}).update(dict(file=fn, title=title, source="https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"), license=lic, artist=artist,
                         desc=strip(v.get("desc")), credit=f"Photo: {artist[:60] or 'Unknown'} / Wikimedia Commons / {lic}"))
    print(key, fn, lic, artist[:50], flush=True); json.dump(credits, open(CF, "w"), indent=1); time.sleep(3)
json.dump(credits, open(CF, "w"), indent=1)
