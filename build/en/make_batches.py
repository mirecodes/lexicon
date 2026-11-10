"""Pack chapters into batches/NN.jsonl (one trimmed candidate word per line), keeping chapters whole."""
import json, sys
from pathlib import Path

D = Path(sys.argv[1])
LIMIT = 130
out = D / "batches"
out.mkdir(exist_ok=True)


def trim(s):
    return {
        "pos": s["pos"], "en": s["en"], "syn": s["synonyms"][:8],
        "ex": [x["text"] for x in s["examples"][:2] if len(x["text"]) <= 170],
    }


batches, cur, n = [], [], 0
for f in sorted((D / "cand").glob("*.json")):
    words = json.loads(f.read_text())
    if n and n + len(words) > LIMIT:
        batches.append(cur)
        cur, n = [], 0
    cur.append((f.stem, words))
    n += len(words)
batches.append(cur)

index = {}
for i, b in enumerate(batches, 1):
    name = f"{i:02d}"
    index[name] = [ch for ch, _ in b]
    with open(out / f"{name}.jsonl", "w", encoding="utf-8") as fh:
        for ch, words in b:
            for w in words:
                fh.write(json.dumps({"chapter": ch, "word": w["word"], "score": w["score"],
                                     "oewn": [trim(s) for s in w["oewn"]],
                                     "wiktionary": [trim(s) for s in w["wiktionary"][:12]]}, ensure_ascii=False) + "\n")
(D / "batches/index.json").write_text(json.dumps(index))
print(len(batches), "batches", [sum(1 for _ in open(out / f"{k}.jsonl")) for k in index])
