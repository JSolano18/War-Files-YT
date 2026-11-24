import urllib.request, time, sys, os
UA = {"User-Agent": "WarFilesResearch/1.0 (documentary research)"}
url, out = sys.argv[1], sys.argv[2]
for i in range(12):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        open(out, "wb").write(data); print("OK", len(data), flush=True); break
    except Exception as e:
        print(i, e, flush=True); time.sleep(600)
