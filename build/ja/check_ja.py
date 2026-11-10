"""Check worker output against its batch. Usage: check_ja.py <W> words|kanji [batch ...]"""
import json, re, sys
from pathlib import Path

D, mode = Path(sys.argv[1]), sys.argv[2]
src, dst = ("jbatches", "jcurated") if mode == "words" else ("kbatches", "kcurated")
names = sys.argv[3:] or sorted(p.stem for p in (D / src).glob("*.jsonl"))
HANGUL = re.compile("[가-힣]")
JA = re.compile("[぀-ヿ一-鿿]")
norm = lambda t: re.sub(r"\s+", " ", t).strip()


def initial_free(syl):
    """Korean syllable with its initial consonant dropped to ㅇ (so 력 ~ 역 ~ 녁 compare equal)."""
    i = ord(syl) - 0xAC00
    return i % 588 if 0 <= i < 11172 else syl


assert initial_free("력") == initial_free("역")
errs, total = [], 0
for n in names:
    rows = [json.loads(l) for l in open(D / src / f"{n}.jsonl", encoding="utf-8")]
    p = D / dst / f"{n}.json"
    if not p.exists():
        errs.append(f"{n}: file missing")
        continue
    got = json.loads(p.read_text(encoding="utf-8"))
    key = "id" if mode == "words" else "kanji"
    if [x.get(key) for x in got] != [r[key] for r in rows]:
        want, have = [r[key] for r in rows], [x.get(key) for x in got]
        errs.append(f"{n}: {key}s differ from batch (order matters): missing {[k for k in want if k not in have][:10]} extra {[k for k in have if k not in want][:10]}")
    by = {r[key]: r for r in rows}
    for x in got:
        r = by.get(x.get(key))
        if not r:
            continue
        total += 1
        if mode == "kanji":
            ko = x.get("ko", "")
            m = re.fullmatch(r"(\S.*) (\S+)", ko)
            if not m or not HANGUL.search(ko):
                errs.append(f"{r['kanji']}: ko must be '훈 음': {ko!r}")
            elif r["eum"] and not (len(m.group(2)) == 1 and initial_free(m.group(2)) in {initial_free(e) for e in r["eum"]}):
                errs.append(f"{r['kanji']}: 음 '{m.group(2)}' not in {r['eum']}")
            continue
        w = r["word"]
        if x.get("word") != w:
            errs.append(f"{r['id']}: word should be {w}")
        glosses = {norm(s["gloss"]) for s in r["senses"]} | {norm(g) for s in r["senses"] for g in s["gloss"].split("; ")}
        if not 1 <= len(x.get("senses", [])) <= 3:
            errs.append(f"{w}: need 1-3 senses")
        for s in x.get("senses", []):
            if not s.get("en"):
                errs.append(f"{w}: empty en")
            elif s.get("en_source") != "generated" and norm(s["en"]) not in glosses:
                errs.append(f"{w}: en not verbatim and not marked generated: {s['en']}")
            if not HANGUL.search(s.get("ko", "")):
                errs.append(f"{w}: bad ko")
            ex = s.get("example") or {}
            if not JA.search(ex.get("ja", "")) or not HANGUL.search(ex.get("ko", "")):
                errs.append(f"{w}: bad example")
print("\n".join(errs[:80]))
print(f"{total} checked, {len(errs)} errors")
sys.exit(bool(errs))
