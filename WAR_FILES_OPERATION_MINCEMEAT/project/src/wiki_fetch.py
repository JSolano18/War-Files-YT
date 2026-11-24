import json, sys, time, urllib.request, urllib.parse, os
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research; contact via YouTube channel)"}
def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return r.read()
        except Exception as e:
            print("retry", i, e, file=sys.stderr); time.sleep(3 + 4 * i)
    raise SystemExit("failed " + url)
def extract(title):
    q = urllib.parse.urlencode(dict(action="query", prop="extracts", explaintext=1, format="json", redirects=1, titles=title))
    d = json.loads(get("https://en.wikipedia.org/w/api.php?" + q)); pg = list(d["query"]["pages"].values())[0]
    return pg.get("extract", "")
if __name__ == "__main__":
    out = sys.argv[1]
    for t in sys.argv[2:]:
        fn = os.path.join(out, t.replace(" ", "_").replace("/", "_") + ".txt")
        if os.path.exists(fn) and os.path.getsize(fn) > 100: continue
        x = extract(t); open(fn, "w").write(x); print(t, len(x)); time.sleep(2)
