"""Patient Commons fetcher for the Short's NEW images (not used in the long video)."""
import json, os, re, sys, time, urllib.request, urllib.parse
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research)"}
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "short"); CF = os.path.join(OUT, "credits.json")
strip = lambda s: re.sub(r"\s+", " ", re.sub("<[^>]+>", "", s or "")).strip()
def get(url):
    for i in range(30):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503): print("wait", e.code, 60 + 30 * i, flush=True); time.sleep(60 + 30 * i); continue
            raise
        except Exception as e: print("err", e, flush=True); time.sleep(20)
    raise SystemExit("gave up " + url)
W = json.load(open(os.path.join(OUT, "wanted.json")))
q = urllib.parse.urlencode(dict(action="query", titles="|".join(W.values()), prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=1920, format="json", redirects=1))
d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q)); info = {}
norm = {n["from"]: n["to"] for n in d["query"].get("normalized", []) + d["query"].get("redirects", [])}
for p in d["query"]["pages"].values():
    if "missing" in p: print("MISSING", p["title"]); continue
    ii = p["imageinfo"][0]; em = ii.get("extmetadata", {}); g = lambda k: em.get(k, {}).get("value", "")
    info[p["title"]] = dict(url=ii["url"], thumb=ii.get("thumburl"), w=ii.get("width"), license=g("LicenseShortName"), artist=strip(g("Artist")), desc=strip(g("ImageDescription"))[:300], date=strip(g("DateTimeOriginal")))
credits = json.load(open(CF)) if os.path.exists(CF) else {}
for key, t in W.items():
    v = info.get(norm.get(t, t))
    if not v: print("no info", key, t); continue
    lic = v["license"]
    if "NC" in lic or "ND" in lic or not any(x in lic for x in ("Public domain", "CC BY", "CC0", "PD")): print("SKIP licence", key, lic); continue
    url = v["thumb"] if v.get("w") and v["w"] > 1920 and v.get("thumb") else v["url"]
    url = url.split("?")[0].replace("://thumb.wikimedia.org/", "://upload.wikimedia.org/")
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"; fn = key + ext
    if not os.path.exists(os.path.join(OUT, fn)): data = get(url); open(os.path.join(OUT, fn), "wb").write(data); time.sleep(20)
    credits[key] = dict(file=fn, title=t, source="https://commons.wikimedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")), license=lic, artist=v["artist"], date=v["date"], desc=v["desc"],
                        credit=f"Photo: {v['artist'][:60] or 'Unknown'} / Wikimedia Commons / {lic}")
    json.dump(credits, open(CF, "w"), indent=1); print("ok", key, "|", lic, "|", v["artist"][:40], "|", v["desc"][:80], flush=True)
print("ALL DONE", flush=True)
