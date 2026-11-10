"""Validate roots_norm.json and derive roots_map.json (raw form+ko -> id) and roots.json ({id: {type, ko}}).
Usage: norm.py <D> [EN dir to also write en/roots.json]"""
import collections, json, sys
from pathlib import Path

D = Path(sys.argv[1])
raw = [json.loads(l) for l in open(D / "roots_raw.jsonl", encoding="utf-8")]
norm = json.loads((D / "roots_norm.json").read_text(encoding="utf-8"))
merge, split, kos = norm.get("merge_forms", {}), norm.get("split", {}), norm.get("ko", {})
errs = []
types = {r["form"]: r["type"] for r in raw}

canon_raw = collections.defaultdict(set)  # canonical form -> raw meanings
for r in raw:
    c = merge.get(r["form"], r["form"])
    if types.get(c, r["type"]) != r["type"]:
        errs.append(f"merge {r['form']} -> {c} changes type")
    canon_raw[c].update(r["meanings"])

mapping, roots = [], {}
for r in raw:
    c = merge.get(r["form"], r["form"])
    for m in r["meanings"]:
        if c in split:
            hit = [g for g in split[c] if m in g["members"]]
            if len(hit) != 1:
                errs.append(f"{c}: raw meaning {m!r} is in {len(hit)} groups")
                continue
            g = hit[0]
            pid, ko = f"{c}({g['label']})", g["ko"]
        else:
            pid, ko = c, kos.get(c)
            if not ko:
                errs.append(f"{c}: no ko")
                continue
        mapping.append({"form": r["form"], "ko": m, "id": pid})
        roots[pid] = {"type": r["type"], "ko": ko}
for c, groups in split.items():
    extra = {m for g in groups for m in g["members"]} - canon_raw.get(c, set())
    if extra:
        errs.append(f"{c}: members not found in raw data: {sorted(extra)[:5]}")
if errs:
    print("\n".join(errs[:80]))
    print(len(errs), "problems")
    sys.exit(1)
(D / "roots_map.json").write_text(json.dumps(mapping, ensure_ascii=False))
if len(sys.argv) > 2:
    (Path(sys.argv[2]) / "roots.json").write_text(json.dumps(dict(sorted(roots.items())), ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
print(f"OK: {len(raw)} raw forms -> {len(roots)} parts ({len(split)} split, {len(merge)} merged)")
