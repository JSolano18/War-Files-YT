"""WAR FILES — licensed real-photo finder (Openverse + Library of Congress).
Only returns images that can be used on a monetized channel and edited (crop/grade/text):
  Openverse: CC0, Public Domain Mark, CC BY, CC BY-SA   (excludes NC and ND licences)
  Library of Congress: items flagged "unrestricted" by the LOC API
Usage:
  python3 photo_search.py search "invasion of sicily 1943"            # list candidates
  python3 photo_search.py get ov:<openverse_id> OUTDIR KEY             # download + record credit
  python3 photo_search.py get loc:<item_number> OUTDIR KEY
Credits are appended to OUTDIR/credits.json (same format as the documentary projects).
Be gentle: one request at a time, small pauses (APIs are rate-limited)."""
import json, os, re, sys, time, urllib.parse, urllib.request
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research)"}
OK_OV = {"cc0", "pdm", "by", "by-sa"}


def get(url, binary=False):
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read(); return data if binary else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500: time.sleep(15 * (i + 1)); continue
            raise
    raise SystemExit("rate-limited: " + url)


def search(q, n=12):
    out = []
    d = get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(dict(q=q, license_type="commercial,modification", page_size=n)))
    for r in d.get("results", []):
        if r["license"] not in OK_OV: continue
        out.append(dict(id="ov:" + r["id"], title=r["title"], license=f"{r['license'].upper()} {r.get('license_version') or ''}".strip(),
                        creator=r.get("creator") or "Unknown", source=r.get("foreign_landing_url"), w=r.get("width"), h=r.get("height"), via=r.get("source")))
    time.sleep(1)
    d = get("https://www.loc.gov/photos/?" + urllib.parse.urlencode(dict(q=q, fo="json", c=n)))
    for r in d.get("results", []):
        m = re.search(r"/item/([^/]+)/", r.get("url", ""))
        if not m or not any("tile.loc.gov" in u for u in r.get("image_url", [])): continue
        out.append(dict(id="loc:" + m.group(1), title=r.get("title", ""), license="LOC (check unrestricted)", creator=", ".join(r.get("contributor", []) or ["Library of Congress"]),
                        source=r.get("url"), w=None, h=None, via="loc"))
    return out


def fetch(item, outdir, key):
    os.makedirs(outdir, exist_ok=True); src, ident = item.split(":", 1)
    if src == "ov":
        r = get(f"https://api.openverse.org/v1/images/{ident}/")
        if r["license"] not in OK_OV: raise SystemExit("licence not allowed: " + r["license"])
        url = r["url"]; lic = f"CC {r['license'].upper()} {r.get('license_version') or ''}".replace("CC CC0", "CC0").replace("CC PDM", "Public Domain Mark").strip()
        creator = r.get("creator") or "Unknown"; landing = r.get("foreign_landing_url"); title = r["title"]
    else:
        d = get(f"https://www.loc.gov/item/{ident}/?fo=json")
        if not d.get("unrestricted"): raise SystemExit("LOC item is not flagged unrestricted — check rights manually")
        thumb = (d["item"].get("image_url") or [""])[-1].split("#")[0]
        url = re.sub(r"_\d+px\.jpg$", "v.jpg", thumb)
        lic = "No known restrictions (Library of Congress)"; creator = ", ".join(d["item"].get("contributor_names", []) or ["Library of Congress"])
        landing = f"https://www.loc.gov/item/{ident}/"; title = d["item"].get("title", "")
    data = get(url, binary=True); ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".jpg"
    fn = key + ext.lower(); open(os.path.join(outdir, fn), "wb").write(data)
    cf = os.path.join(outdir, "credits.json"); credits = json.load(open(cf)) if os.path.exists(cf) else {}
    credits[key] = dict(file=fn, title=title, source=landing, license=lic, artist=creator, credit=f"Photo: {creator[:70]} / {lic}")
    json.dump(credits, open(cf, "w"), indent=1); print("saved", fn, "|", lic, "|", creator)


if __name__ == "__main__":
    if sys.argv[1] == "search":
        for r in search(" ".join(sys.argv[2:])):
            print(f"{r['id']:48s} | {r['license']:26s} | {str(r['creator'])[:28]:28s} | {r['title'][:70]}")
    elif sys.argv[1] == "get":
        fetch(sys.argv[2], sys.argv[3], sys.argv[4])
