"""Write en/<a>/<ab>.json from merged list + OEWN + Wiktionary, overlaying curated/<ab>.json. Also dumps cand/<ab>.json for curation."""
import collections, gzip, json, sys, unicodedata, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path

D, EN = Path(sys.argv[1]), Path(sys.argv[2])


def chapter(word):
    """Chapter file for a word: its first two letters (same rule as enChapter in scripts/data.ts)."""
    return "".join(c for c in word if "a" <= c <= "z")[:2]


POS = {"n": "noun", "v": "verb", "a": "adj", "s": "adj", "r": "adv"}
SKIP_TAGS = {"obsolete", "archaic", "rare", "dialectal", "historical"}


def fold(w):
    w = unicodedata.normalize("NFKD", w.strip().lower())
    return "".join(c for c in w if not unicodedata.combining(c))


merged = json.loads((D / "merged.json").read_text())
lex = ET.parse(gzip.open(D / "oewn/oewn2025.xml.gz")).getroot()[0]
entry_lemma, by_word = {}, collections.defaultdict(list)
for e in lex.findall("LexicalEntry"):
    lemma = e.find("Lemma")
    entry_lemma[e.get("id")] = lemma.get("writtenForm")
    if fold(lemma.get("writtenForm")) in merged:
        by_word[fold(lemma.get("writtenForm"))] += [(lemma.get("partOfSpeech"), s.get("synset")) for s in e.findall("Sense")]
synsets = {s.get("id"): s for s in lex.findall("Synset")}


def oewn_senses(w):
    out = []
    for pos, sid in by_word.get(w, []):
        s = synsets[sid]
        syn = [entry_lemma[m] for m in s.get("members", "").split() if fold(entry_lemma[m]) != w]
        out.append({
            "pos": POS[pos],
            "en": s.find("Definition").text,
            "synonyms": syn,
            "examples": [{"text": x.text, "source": "oewn"} for x in s.findall("Example")],
            "source": "oewn",
        })
    return out


def wikt_senses(w):
    p = D / "wikt" / (urllib.parse.quote(w, safe="") + ".json")
    if not p.exists():
        return []
    out = []
    for e in json.loads(p.read_text()):
        for s in e["senses"]:
            if not SKIP_TAGS & set(s["tags"]):
                out.append({
                    "pos": e["pos"],
                    "en": s["gloss"],
                    "synonyms": s["synonyms"],
                    "examples": [{"text": t, "source": "wiktionary"} for t in s["examples"]],
                    "source": "wiktionary",
                })
    return out


chapters, cand = collections.defaultdict(list), collections.defaultdict(list)
missing = []
for w, r in sorted(merged.items()):
    o, k = oewn_senses(w), wikt_senses(w)
    senses = o or k
    if not senses:
        missing.append(w)
        continue
    chapters[chapter(w)].append({"word": w, "score": r["score"], "zipf": r["zipf"], "lists": r["lists"], "curated": False, "senses": senses})
    cand[chapter(w)].append({"word": w, "score": r["score"], "oewn": o, "wiktionary": k})

(D / "cand").mkdir(exist_ok=True)
curated_n = 0
fixes = json.loads((Path(__file__).parent / "fixes.json").read_text())  # hand corrections kept in the repo
parts, canon = {}, {}
if (D / "roots_map.json").exists():
    # roots_map.json: list of {"form","ko","id"} mapping each raw (form, ko) pair to its canonical part id
    canon = {(m["form"], m["ko"]): m["id"] for m in json.loads((D / "roots_map.json").read_text(encoding="utf-8"))}
    for f in (D / "parts").glob("*.json"):
        parts.update({x["word"]: x for x in json.loads(f.read_text(encoding="utf-8"))})
for ch, entries in chapters.items():
    overlay_path = D / "curated" / f"{ch}.json"
    overlay = {x["word"]: x["senses"] for x in json.loads(overlay_path.read_text())} if overlay_path.exists() else {}
    for e in entries:
        if e["word"] in overlay:
            e["senses"], e["curated"] = overlay[e["word"]], True
            curated_n += 1
            for s, fix in zip(e["senses"], fixes.get(e["word"], [])):
                s.update(fix)
        if e["word"] in parts:
            x = parts[e["word"]]
            if x["parts"]:
                e["parts"] = list(dict.fromkeys(canon[(a["form"], a["ko"])] for a in x["parts"]))
            if x["origin"]:
                e["origin"] = {"ko": x["origin"], "source": "wiktionary", "ko_source": "generated"}
    path = EN / ch[0] / f"{ch}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (D / "cand" / f"{ch}.json").write_text(json.dumps(cand[ch], ensure_ascii=False))
print("chapters", len(chapters), "entries", sum(map(len, chapters.values())), "curated", curated_n, "missing", missing)
sizes = sorted((len(v), k) for k, v in chapters.items())
print("largest", sizes[-5:], "ab", len(chapters["ab"]))
