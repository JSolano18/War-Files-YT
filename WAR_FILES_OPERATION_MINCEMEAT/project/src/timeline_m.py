"""Build the edit: paragraph placement, word-synced shot cuts, subtitle events."""
import json, os, sys, re, difflib
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCRIPT
from tts import spoken, norm
B = os.path.join(os.path.dirname(__file__), "..", "build")
ARCH = os.path.join(os.path.dirname(__file__), "..", "assets", "archival", "credits.json")
XF = 0.5            # cross-dissolve length (s)
MAXSHOT = 10.5      # longer shots are split into two compositions

FALLBACK = {  # used only if an archival image could not be obtained/licensed
    "north_africa": ("map", dict(mode="med_1943")), "casablanca": ("map", dict(mode="two_choices", hl="sicily")),
    "churchill": ("silhouette", dict(label="WINSTON CHURCHILL", sub="Prime Minister", tag="ILLUSTRATION")),
    "german_coast": ("map", dict(mode="sicily_obvious")), "dummy_tank": ("map", dict(mode="barclay")),
    "fleming": ("silhouette", dict(label="IAN FLEMING", sub="Personal assistant to the Director of Naval Intelligence", tag="ILLUSTRATION")),
    "canaris": ("silhouette", dict(label="ADM. WILHELM CANARIS", sub="Head of the Abwehr", tag="ILLUSTRATION")),
    "spilsbury": ("office", dict(variant="lamp", tag="ILLUSTRATION")), "welsh_mine": ("valleys", dict(variant="dusk", tag="ILLUSTRATION")),
    "alexander": ("doc", dict(kind="nye_env", tag="RECREATION — ILLUSTRATIVE")), "mountbatten": ("doc", dict(kind="sealed", tag="RECREATION — ILLUSTRATIVE")),
    "huelva": ("huelva_day", dict(tag="ILLUSTRATION")), "cabinet_war_rooms": ("office", dict(variant="lamp", tag="ILLUSTRATION")),
    "eisenhower": ("stamp", dict(text="APPROVED", sub="EISENHOWER'S HQ  ·  17 APRIL 1943")), "bletchley": ("office", dict(variant="lamp", tag="ILLUSTRATION")),
    "doenitz": ("silhouette", dict(label="GRAND ADM. KARL DÖNITZ", sub="Record of meeting with Hitler, 14 May 1943", tag="ILLUSTRATION")),
    "hitler": ("map", dict(mode="europe_dark")), "hitler_mussolini": ("map", dict(mode="fake_targets")), "panzer": ("map", dict(mode="reinforce")),
    "husky1": ("fleet", dict(variant="dawn", tag="ILLUSTRATION")), "husky2": ("fleet", dict(variant="dawn", tag="ILLUSTRATION", alt=1)),
    "husky3": ("map", dict(mode="sicily_zoom")), "rommel": ("silhouette", dict(label="FIELD MARSHAL ERWIN ROMMEL", sub="Sent to Greece, late July 1943", tag="ILLUSTRATION")),
    "mussolini": ("statement", dict(lines=["25 JULY 1943", "MUSSOLINI REMOVED FROM POWER"], accent=[1], style="center")),
    "dasher": ("ocean", dict(variant="overcast", tag="ILLUSTRATION")), "cholmondeley": ("photo", dict(key="montagu_cholmondeley", mode="kb")),
    "montagu": ("photo", dict(key="montagu_cholmondeley", mode="kb")),
    "seraph_officers": ("photo", dict(key="seraph_underway", mode="kb", z=(1.25, 1.5), c0=(0.45, 0.3), c1=(0.6, 0.28), credit_extra="HMS Seraph's bridge, December 1943")),
    "seraph_helm": ("ocean", dict(variant="dusk", sub="close", tag="DRAMATIZATION")),
    "grave": ("statement", dict(lines=["MAJOR WILLIAM MARTIN", "BURIED IN HUELVA  ·  2 MAY 1943  ·  FULL MILITARY HONOURS"], accent=[0], style="memorial")),
    "grave2": ("huelva_day", dict(tag="ILLUSTRATION")),
    "aberbargoed": ("valleys", dict(variant="dusk", tag="ILLUSTRATION")),
    "nye": ("doc", dict(kind="nye_env", tag="RECREATION — ILLUSTRATIVE")),
}


def word_times(meta):
    """map spoken-word index -> start time using difflib alignment of script vs whisper words"""
    ref = [norm(w) for w in meta["spoken"].split()]; hyp = [norm(w[0]) for w in meta["words"]]
    times = [None] * len(ref)
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1): times[i1 + k] = meta["words"][j1 + k][1]
        elif j2 > j1:
            for k in range(i2 - i1): times[i1 + k] = meta["words"][j1 + min(j2 - j1 - 1, int(k * (j2 - j1) / max(1, i2 - i1)))][1]
    # interpolate gaps
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    for i in range(len(times)):
        if times[i] is None:
            prev = max([k for k in known if k[0] < i], default=(0, 0.0), key=lambda k: k[0]); nxt = min([k for k in known if k[0] > i], default=(len(times), meta["dur"]), key=lambda k: k[0])
            times[i] = prev[1] + (nxt[1] - prev[1]) * (i - prev[0]) / max(1, nxt[0] - prev[0])
    ends = times[1:] + [meta["dur"]]
    for i, w in enumerate(meta["words"]): pass
    return times, ends


def anchor_time(meta, times, anchor):
    sp_words = [norm(w) for w in meta["spoken"].split()]; a_words = [norm(w) for w in spoken(anchor).split()]
    for i in range(len(sp_words) - len(a_words) + 1):
        if sp_words[i:i + len(a_words)] == a_words: return times[i]
    raise ValueError(f"anchor not found: {anchor!r} in {meta['text'][:60]!r}")


def build():
    credits = json.load(open(ARCH)) if os.path.exists(ARCH) else {}
    T = 0.0; paras = []; shots = []; subs = []; chapters = []
    for i, p in enumerate(SCRIPT):
        if "text" not in p:
            if "dur" in p:
                shots.append(dict(kind="chapter", p=dict(num=p["num"], title=p["title"]), start=T, end=T + p["dur"], chapter=True))
                chapters.append((T, p["chapter"])); T += p["dur"]
            else:
                chapters.append((T, p["chapter"]))
            continue
        meta = json.load(open(os.path.join(B, "tts", f"p{i:03d}.wav.json")))
        lead = 0.6 if not paras else 0.3
        a0 = T + lead; times, ends = word_times(meta)
        paras.append(dict(i=i, file=os.path.join(B, "tts", f"p{i:03d}.wav"), start=a0, dur=meta["dur"], text=p["text"], pause=p["pause"]))
        seg_end = a0 + meta["dur"] + p["pause"]
        # shots
        local = []
        for k, (anc, kind, prm) in enumerate(p["shots"]):
            st = T if anc is None else a0 + max(0.0, anchor_time(meta, times, anc) - 0.12)
            local.append([st, kind, dict(prm)])
        for k, (st, kind, prm) in enumerate(local):
            en = local[k + 1][0] if k + 1 < len(local) else seg_end
            if kind == "photo" and prm.get("key") in ("montagu", "cholmondeley"):
                foc = (0.66, 0.36) if prm["key"] == "montagu" else (0.50, 0.36)
                prm = dict(prm, key="montagu_cholmondeley", mode="kb", z=(1.05, 1.45), c0=(0.55, 0.45), c1=foc)
            if kind == "photo" and prm.get("key") in ("montagu", "cholmondeley"):
                foc = (0.66, 0.36) if prm["key"] == "montagu" else (0.50, 0.36)
                prm = dict(prm, key="montagu_cholmondeley", mode="kb", z=(1.05, 1.45), c0=(0.55, 0.45), c1=foc)
            if kind == "photo" and prm.get("key") not in credits:
                fb = FALLBACK.get(prm.get("key")) or ("ocean", dict(variant="overcast", tag="ILLUSTRATION"))
                kind, prm2 = fb; prm = dict(prm2) | ({"name": prm["name"], "sub": prm.get("sub")} if prm.get("name") and kind == "photo" else {})
                if kind == "photo" and prm.get("key") in ("montagu", "cholmondeley"):
                    foc = (0.66, 0.36) if prm["key"] == "montagu" else (0.50, 0.36)
                    prm = dict(prm, key="montagu_cholmondeley", mode="kb", z=(1.05, 1.45), c0=(0.55, 0.45), c1=foc)
            if kind == "photo" and prm.get("key") not in credits: kind, prm = "ocean", dict(variant="overcast", tag="ILLUSTRATION")
            if en - st > MAXSHOT and kind not in ("statement", "quote", "end", "title", "datecard", "questions", "stamp", "bars", "split"):
                mid = (st + en) / 2
                shots.append(dict(kind=kind, p=prm, start=st, end=mid)); shots.append(dict(kind=kind, p=dict(prm, alt=1), start=mid, end=en))
            else:
                shots.append(dict(kind=kind, p=prm, start=st, end=en))
        # subtitles: sentence-level, word-timed
        sents = re.split(r"(?<=[.?!])\s+", p["text"].strip()); spw = meta["spoken"].split(); si = 0
        for s in sents:
            n_sp = len(spoken(s).split()); idx0, idx1 = si, min(len(spw), si + n_sp); si = idx1
            if idx0 >= len(times): break
            t_s = a0 + times[idx0]; t_e = a0 + (ends[idx1 - 1] if idx1 - 1 < len(ends) else meta["dur"])
            words = s.split(); nd = len(words)
            def wt(j):  # display word j -> time
                k = idx0 + min(n_sp - 1, int(j * n_sp / max(1, nd))); return a0 + times[min(k, len(times) - 1)]
            chunks = []; cur = []
            for w in words:
                cur.append(w)
                if len(" ".join(cur)) > 72 or (len(" ".join(cur)) > 44 and re.search(r"[,;:]$", w)): chunks.append(cur); cur = []
            if cur:
                if chunks and len(" ".join(cur)) < 16: chunks[-1] += cur
                else: chunks.append(cur)
            j = 0
            for ci, c in enumerate(chunks):
                cs = wt(j); j += len(c); ce = wt(j) if j < nd else t_e
                subs.append([cs, ce, " ".join(c)])
        T = seg_end
    # extend last shot
    shots[-1]["end"] = T
    for k in range(len(subs)):
        nxt = subs[k + 1][0] if k + 1 < len(subs) else subs[k][1] + 2
        subs[k][1] = min(max(subs[k][1] + 0.15, subs[k][0] + 0.9), nxt - 0.03)
    return dict(total=T, paras=paras, shots=shots, subs=subs, chapters=chapters)


if __name__ == "__main__":
    tl = build(); json.dump(tl, open(os.path.join(B, "timeline.json"), "w"), indent=0)
    d = [s["end"] - s["start"] for s in tl["shots"]]
    print("total %.1f s (%d:%04.1f)  shots %d  mean %.1f s  max %.1f s  subs %d" % (tl["total"], tl["total"] // 60, tl["total"] % 60, len(d), sum(d) / len(d), max(d), len(tl["subs"])))
    from collections import Counter; print(Counter(s["kind"] for s in tl["shots"]).most_common())
