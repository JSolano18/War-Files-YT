"""Patient Commons fetcher: respects 429s with long waits; records credits only for files on disk."""
import json, os, re, sys, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research)"}
P = os.path.join(os.path.dirname(__file__), ".."); OUT = os.path.join(P, "assets", "archival"); CF = os.path.join(OUT, "credits.json")
strip = lambda s: re.sub(r"\s+", " ", re.sub("<[^>]+>", "", s or "")).strip()
def get(url, binary=True):
    for i in range(30):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429: print("429, waiting", 60 + 30 * i, flush=True); time.sleep(60 + 30 * i); continue
            raise
        except Exception as e: print("err", e, flush=True); time.sleep(20)
    raise SystemExit("gave up " + url)
time.sleep(int(os.environ.get("INITIAL_WAIT", "240")))
W = json.load(open(os.path.join(P, "research", "wanted.json")))
info = json.load(open(os.path.join(P, "research", "commons_candidates.json")))
newt = list(W["new"].values())
q = urllib.parse.urlencode(dict(action="query", titles="|".join(newt), prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=1920, format="json"))
d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))
for p in d["query"]["pages"].values():
    ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {}); g = lambda k: em.get(k, {}).get("value", "")
    info[p["title"]] = dict(url=ii.get("url"), thumb=ii.get("thumburl"), w=ii.get("width"), h=ii.get("height"), license=g("LicenseShortName"), artist=g("Artist"), desc=g("ImageDescription")[:400], usage=g("UsageTerms"))
json.dump(info, open(os.path.join(P, "research", "commons_candidates.json"), "w"), indent=1)
print("metadata ok", flush=True)
credits = json.load(open(CF)) if os.path.exists(CF) else {}
for key, title in list(W["old"].items()) + list(W["new"].items()):
    v = info.get(title)
    if not v or not v.get("url"): print("no info", key); continue
    lic = v.get("license", "")
    if not any(x in lic for x in ("Public domain", "CC BY", "CC0", "GFDL", "PD")): print("SKIP license", key, lic); continue
    url = v["url"] if not (v.get("w") and v["w"] > 3000 and v.get("thumb")) else re.sub(r"/\d+px-", "/1920px-", v["thumb"])
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"; fn = key + ext
    if not os.path.exists(os.path.join(OUT, fn)):
        data = get(url); open(os.path.join(OUT, fn), "wb").write(data)
    artist = strip(v.get("artist"))
    credits[key] = dict(file=fn, title=title, source="https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")), license=lic, artist=artist,
                        desc=strip(v.get("desc")), credit=f"Photo: {artist[:70] or 'Unknown'} / Wikimedia Commons / {lic}")
    json.dump(credits, open(CF, "w"), indent=1); print("ok", key, lic, artist[:40], flush=True); time.sleep(25)
print("ALL FETCHED", flush=True)
