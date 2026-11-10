"""Split all words into ebatches/NN.jsonl for the roots and origins pass."""
import glob, json, sys, urllib.parse
from pathlib import Path

D = Path(sys.argv[1])
SIZE = 275
entries = []
for f in sorted(glob.glob(str(D / "curated/*.json"))):
    entries += json.loads(Path(f).read_text(encoding="utf-8"))
entries.sort(key=lambda e: e["word"])
out = D / "ebatches"
out.mkdir(exist_ok=True)
for i in range(0, len(entries), SIZE):
    with open(out / f"{i // SIZE + 1:02d}.jsonl", "w", encoding="utf-8") as fh:
        for e in entries[i:i + SIZE]:
            p = D / "etym" / (urllib.parse.quote(e["word"], safe="") + ".json")
            etym = json.loads(p.read_text()) if p.exists() else []
            s = e["senses"][0]
            fh.write(json.dumps({"word": e["word"], "meaning": f"{s['pos']}: {s['ko']} ({s['en'][:80]})", "etym": etym[:3]}, ensure_ascii=False) + "\n")
print(len(entries), "words", (len(entries) + SIZE - 1) // SIZE, "batches")
