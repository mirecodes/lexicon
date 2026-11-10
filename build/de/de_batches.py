"""Pick the Wiktionary entry matching each Goethe lemma -> de_pick.json, and write dbatches/NN.jsonl."""
import json, sys, urllib.parse
from pathlib import Path

D = Path(sys.argv[1])
SIZE = 200
ORDER = ["verb", "adj", "adv", "prep", "conj", "pron", "det", "num", "intj", "particle", "phrase", "noun", "name"]
merged = json.loads((D / "de_merged.json").read_text())


def pick(w, m, ents):
    if not ents:
        return None
    if m["articles"] or w[0].isupper():
        nouns = [e for e in ents if e["pos"] == "noun"]
        if nouns:
            return nouns[0]
    return sorted(ents, key=lambda e: ORDER.index(e["pos"]) if e["pos"] in ORDER else 99)[0]


picks, rows = {}, []
for w, m in sorted(merged.items(), key=lambda kv: (kv[1]["level"], kv[0].lower())):
    ents = json.loads((D / "de_wikt" / (urllib.parse.quote(w, safe="") + ".json")).read_text())
    p = pick(w, m, ents)
    picks[w] = p
    rows.append({"word": w, "level": m["level"], "pos": p["pos"] if p else ("noun" if m["articles"] else None),
                 "head": p["head"] if p else None, "goethe": m["raw"],
                 "senses": [{"gloss": s["gloss"]} for s in (p["senses"] if p else [])][:8],
                 "etym": p["etym"][:250] if p else ""})
(D / "de_pick.json").write_text(json.dumps(picks, ensure_ascii=False))
out = D / "dbatches"
out.mkdir(exist_ok=True)
for i in range(0, len(rows), SIZE):
    with open(out / f"{i // SIZE + 1:02d}.jsonl", "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[i:i + SIZE])
print(len(rows), "words", (len(rows) + SIZE - 1) // SIZE, "batches; no wiktionary:", sum(p is None for p in picks.values()))
