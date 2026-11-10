"""List synonyms missing from the DB, pick the OEWN gloss for the sense they were used in, split into sbatches/NN.jsonl."""
import collections, glob, gzip, json, sys, xml.etree.ElementTree as ET
from pathlib import Path

D = Path(sys.argv[1])
SIZE = 1000
POS = {"n": "noun", "v": "verb", "a": "adj", "s": "adj", "r": "adv"}
cur = {}
for f in glob.glob(str(D / "curated/*.json")):
    for e in json.loads(Path(f).read_text(encoding="utf-8")):
        cur[e["word"]] = e

lex = ET.parse(gzip.open(D / "oewn/oewn2025.xml.gz")).getroot()[0]
gloss = {s.get("id"): s.find("Definition").text for s in lex.findall("Synset")}
senses = collections.defaultdict(list)
for e in lex.findall("LexicalEntry"):
    l = e.find("Lemma")
    senses[l.get("writtenForm").lower()] += [(POS[l.get("partOfSpeech")], s.get("synset")) for s in e.findall("Sense")]

seen, rows = set(), []
for w, e in sorted(cur.items()):
    head = {sid for _, sid in senses.get(w, [])}
    for s in e["senses"]:
        for raw in s["synonyms"]:
            y = raw.lower()
            if y in cur or y in seen:
                continue
            seen.add(y)
            cands = senses.get(y, [])
            pick = next((c for c in cands if c[1] in head and c[0] == s["pos"]), None) \
                or next((c for c in cands if c[0] == s["pos"]), None) or (cands[0] if cands else None)
            rows.append({"word": y, "pos": pick[0] if pick else s["pos"], "en": gloss[pick[1]] if pick else None,
                         "context": f"{w}: {s['ko']}"})

(D / "syn_base.json").write_text(json.dumps({r["word"]: r for r in rows}, ensure_ascii=False))
out = D / "sbatches"
out.mkdir(exist_ok=True)
for i in range(0, len(rows), SIZE):
    with open(out / f"{i // SIZE + 1:02d}.jsonl", "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[i:i + SIZE])
print(len(rows), "synonyms;", sum(r["en"] is None for r in rows), "without OEWN gloss;", (len(rows) + SIZE - 1) // SIZE, "batches")
