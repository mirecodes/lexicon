"""Check dcurated/NN.json against dbatches/NN.jsonl. Usage: check_de.py <D> [batch ...]"""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1])
names = sys.argv[2:] or sorted(p.stem for p in (D / "dbatches").glob("*.jsonl"))
TYPES = {"sep", "insep", "stem", "suffix"}
errs, total = [], 0
norm = lambda t: re.sub(r"\s+", " ", t).strip()
for n in names:
    rows = {r["word"]: r for r in map(json.loads, open(D / "dbatches" / f"{n}.jsonl", encoding="utf-8"))}
    p = D / "dcurated" / f"{n}.json"
    if not p.exists():
        errs.append(f"{n}: file missing")
        continue
    got = json.loads(p.read_text(encoding="utf-8"))
    words = [x["word"] for x in got]
    if sorted(words) != sorted(rows):
        errs.append(f"{n}: words differ: missing {sorted(set(rows) - set(words))[:15]} extra {sorted(set(words) - set(rows))[:15]}")
    for x in got:
        r = rows.get(x["word"])
        if not r:
            continue
        total += 1
        w = x["word"]
        glosses = {norm(s["gloss"]) for s in r["senses"]}
        if not 1 <= len(x.get("senses", [])) <= 3:
            errs.append(f"{w}: need 1-3 senses")
        for s in x.get("senses", []):
            if s.get("en_source") != "generated" and norm(s.get("en", "")) not in glosses:
                errs.append(f"{w}: en not verbatim and not marked generated: {s.get('en')}")
            if not s.get("en"):
                errs.append(f"{w}: empty en")
            if not re.search("[가-힣]", s.get("ko", "")):
                errs.append(f"{w}: bad ko")
            ex = s.get("example") or {}
            if not ex.get("de") or not re.search("[가-힣]", ex.get("ko", "")):
                errs.append(f"{w}: bad example")
        for a in x.get("parts", []):
            if a.get("type") not in TYPES or not a.get("form") or not re.search("[가-힣]", a.get("ko", "")):
                errs.append(f"{w}: bad part {a}")
print("\n".join(errs[:80]))
print(f"{total} checked, {len(errs)} errors")
sys.exit(bool(errs))
