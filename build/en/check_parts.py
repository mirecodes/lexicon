"""Check parts/NN.json against ebatches/NN.jsonl. Usage: check_parts.py <D> [batch ...] (no batch = all)."""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1])
names = sys.argv[2:] or sorted(p.stem for p in (D / "ebatches").glob("*.jsonl"))
SHAPE = {"prefix": r"[a-z]+-", "suffix": r"-[a-z]+", "root": r"[a-z]+"}
errs, total, with_parts, with_origin = [], 0, 0, 0
for n in names:
    want = [json.loads(l)["word"] for l in open(D / "ebatches" / f"{n}.jsonl", encoding="utf-8")]
    p = D / "parts" / f"{n}.json"
    if not p.exists():
        errs.append(f"{n}: file missing")
        continue
    got = json.loads(p.read_text(encoding="utf-8"))
    if sorted(x["word"] for x in got) != sorted(want):
        errs.append(f"{n}: words differ: missing {sorted(set(want) - {x['word'] for x in got})[:20]}")
    for x in got:
        total += 1
        w = x["word"]
        with_parts += bool(x.get("parts"))
        with_origin += bool(x.get("origin"))
        if not isinstance(x.get("parts"), list):
            errs.append(f"{w}: parts must be a list")
            continue
        for a in x["parts"]:
            if a.get("type") not in SHAPE or not re.fullmatch(SHAPE[a["type"]], a.get("form", "")):
                errs.append(f"{w}: bad part {a}")
            if not re.search("[가-힣]", a.get("ko", "")):
                errs.append(f"{w}: part without Korean meaning {a}")
        o = x.get("origin", "missing")
        if o is not None and (not isinstance(o, str) or not re.search("[가-힣]", o)):
            errs.append(f"{w}: origin must be Korean text or null")
print("\n".join(errs[:80]))
print(f"{total} words, {with_parts} with parts, {with_origin} with origin, {len(errs)} errors")
sys.exit(bool(errs))
