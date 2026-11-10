"""Collect every (type, form, Korean meaning) found in parts/*.json -> roots_raw.jsonl, the input for NORM.md."""
import collections, json, sys
from pathlib import Path

D = Path(sys.argv[1])
pairs = collections.defaultdict(list)
for f in sorted((D / "parts").glob("*.json")):
    for x in json.loads(f.read_text(encoding="utf-8")):
        for a in x["parts"]:
            pairs[(a["type"], a["form"], a["ko"])].append(x["word"])
forms = collections.defaultdict(set)
for t, form, ko in pairs:
    forms[(t, form)].add(ko)
with open(D / "roots_raw.jsonl", "w", encoding="utf-8") as fh:
    for (t, form), kos in sorted(forms.items()):
        meanings = {}
        for ko in sorted(kos):
            ws = pairs[(t, form, ko)]
            meanings[ko] = ws[:4] + ([f"+{len(ws) - 4}"] if len(ws) > 4 else [])
        fh.write(json.dumps({"type": t, "form": form, "meanings": meanings}, ensure_ascii=False) + "\n")
print(len(forms), "forms,", len(pairs), "form+meaning pairs")
