import json, sys, time, urllib.request, urllib.parse
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research)"}
def api(**kw):
    kw.update(format="json")
    for i in range(12):
        try:
            with urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(kw), headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            print("retry", e, file=sys.stderr); time.sleep(10 + 10 * i)
def catmembers(cat):
    d = api(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit=200, cmtype="file|subcat")
    return [m["title"] for m in d["query"]["categorymembers"]]
def search(q, n=30):
    d = api(action="query", list="search", srsearch=q, srnamespace=6, srlimit=n)
    return [m["title"] for m in d.get("query", {}).get("search", [])] if d else (print("ERR", d) or [])
def info(titles):
    out = {}
    for i in range(0, len(titles), 40):
        d = api(action="query", titles="|".join(titles[i:i + 40]), prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=2400)
        for p in d["query"]["pages"].values():
            ii = (p.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
            g = lambda k: (em.get(k, {}).get("value") or "")
            out[p["title"]] = dict(url=ii.get("url"), thumb=ii.get("thumburl"), w=ii.get("width"), h=ii.get("height"), license=g("LicenseShortName"),
                                   artist=g("Artist"), credit=g("Credit"), desc=g("ImageDescription")[:300], date=g("DateTimeOriginal"), usage=g("UsageTerms"))
        time.sleep(1)
    return out
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "cat": print("\n".join(catmembers(sys.argv[2])))
    elif mode == "search": print("\n".join(search(sys.argv[2])))
