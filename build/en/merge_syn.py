"""Combine syn_base.json + syn/*.json into en/synonyms.json: {word: [{pos, en, ko, source, ko_source}]}."""
import json, sys
from pathlib import Path

D, EN = Path(sys.argv[1]), Path(sys.argv[2])
base = json.loads((D / "syn_base.json").read_text())
ko = {}
for f in sorted((D / "syn").glob("*.json")):
    ko.update(json.loads(f.read_text(encoding="utf-8")))
out = {}
for w, b in sorted(base.items()):
    k = ko[w]
    out[w] = [{"pos": b["pos"], "en": b["en"] or k["en"], "ko": k["ko"],
               "source": "oewn" if b["en"] else "generated", "ko_source": "generated"}]
assert len(out) == len(base) and all(v[0]["en"] and v[0]["ko"] for v in out.values())
(EN / "synonyms.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(len(out), "synonyms,", (EN / "synonyms.json").stat().st_size // 1024, "KB;", "sample:", out.get("slake"), out.get("let up"))
