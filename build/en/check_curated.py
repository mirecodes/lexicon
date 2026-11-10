"""Check curated/<chapter>.json against candidates. Usage: check_curated.py <D> [batch ...] (no batch = all)."""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1])
index = json.loads((D / "batches/index.json").read_text())
names = sys.argv[2:] or sorted(index)
errs, warns, total = [], [], 0


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


for b in names:
    for ch in index[b]:
        cand = {w["word"]: w for w in json.loads((D / "cand" / f"{ch}.json").read_text())}
        p = D / "curated" / f"{ch}.json"
        if not p.exists():
            errs.append(f"{ch}: file missing")
            continue
        got = json.loads(p.read_text(encoding="utf-8"))
        words = [x["word"] for x in got]
        if sorted(words) != sorted(cand):
            errs.append(f"{ch}: words differ: missing {sorted(set(cand) - set(words))} extra {sorted(set(words) - set(cand))}")
        for x in got:
            c = cand.get(x["word"])
            if not c:
                continue
            total += 1
            w = x["word"]
            if not 1 <= len(x["senses"]) <= 4:
                errs.append(f"{w}: {len(x['senses'])} senses")
            allowed = {"oewn": {norm(s["en"]) for s in c["oewn"]}, "wiktionary": {norm(s["en"]) for s in c["wiktionary"]}}
            pool = {norm(e["text"]) for k in ("oewn", "wiktionary") for s in c[k] for e in s["examples"]}
            for s in x["senses"]:
                if s.get("source") not in allowed or norm(s.get("en", "")) not in allowed[s.get("source")]:
                    errs.append(f"{w}: en not verbatim from {s.get('source')}: {s.get('en')}")
                if not s.get("pos"):
                    errs.append(f"{w}: no pos")
                if not s.get("ko") or not re.search("[가-힣]", s["ko"]) or s.get("ko_source") != "generated":
                    errs.append(f"{w}: bad ko")
                if not isinstance(s.get("synonyms"), list) or len(s["synonyms"]) > 5 or w in [y.lower() for y in s["synonyms"]]:
                    errs.append(f"{w}: bad synonyms")
                ex = s.get("examples", [])
                if len(ex) != 1 or not ex[0].get("text"):
                    errs.append(f"{w}: need exactly 1 example")
                    continue
                if ex[0].get("source") == "generated":
                    pass
                elif ex[0].get("source") in allowed and norm(ex[0]["text"]) in pool:
                    pass
                else:
                    errs.append(f"{w}: example not verbatim / bad source: {ex[0]}")
                if w[:3] not in ex[0]["text"].lower():
                    warns.append(f"{w}: example may not contain the word: {ex[0]['text']}")
print("\n".join(errs[:80]))
print("WARN\n" + "\n".join(warns[:60]) if warns else "no warnings")
print(f"{total} words checked, {len(errs)} errors, {len(warns)} warnings")
sys.exit(bool(errs))
