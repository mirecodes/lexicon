"""Check syn/NN.json against sbatches/NN.jsonl. Usage: check_syn.py <D> [batch ...]"""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1])
names = sys.argv[2:] or sorted(p.stem for p in (D / "sbatches").glob("*.jsonl"))
errs, total = [], 0
for n in names:
    rows = {r["word"]: r for r in map(json.loads, open(D / "sbatches" / f"{n}.jsonl", encoding="utf-8"))}
    p = D / "syn" / f"{n}.json"
    if not p.exists():
        errs.append(f"{n}: file missing")
        continue
    got = json.loads(p.read_text(encoding="utf-8"))
    missing = set(rows) - set(got)
    if missing:
        errs.append(f"{n}: {len(missing)} missing, e.g. {sorted(missing)[:15]}")
    for w, v in got.items():
        total += 1
        if w not in rows:
            errs.append(f"{w}: not in batch")
            continue
        if not re.search("[가-힣]", v.get("ko", "")):
            errs.append(f"{w}: bad ko")
        if rows[w]["en"] is None and not v.get("en"):
            errs.append(f"{w}: needs en")
print("\n".join(errs[:60]))
print(f"{total} checked, {len(errs)} errors")
sys.exit(bool(errs))
