import sys, json, re, time, os
sys.path.insert(0, os.path.dirname(__file__))
from commons import info, search
Q=["Operation Husky landing Sicily July 1943 IWM","invasion of Sicily 1943 landing craft beach","Casablanca Conference January 1943 Churchill Roosevelt",
   "Hitler Doenitz 1943","Wilhelm Canaris Bundesarchiv","Huelva puerto","Huelva muelle Rio Tinto","Bletchley Park mansion","Archibald Nye",
   "Mountbatten 1943","Eisenhower 1943 Algiers","Allied convoy Sicily 1943","Syracuse Sicily 1943 British troops",
   "German troops Greece 1943 Bundesarchiv","Bernard Spilsbury","Punta Umbria playa","Royal Marines 1943 officer battledress","London Blitz street 1943","Admiralty Arch London 1940s","Gibraltar 1943"]
res = json.load(open("research/commons_search.json")) if os.path.exists("research/commons_search.json") else {}
for q in Q:
    if q in res: continue
    r = search(q); res[q] = (r or [])[:10]; json.dump(res, open("research/commons_search.json", "w"), indent=1); time.sleep(8)
allf = sorted({f for v in res.values() for f in v})
I = info(allf); json.dump(I, open("research/commons_context.json", "w"), indent=1)
print("DONE", len(allf))
