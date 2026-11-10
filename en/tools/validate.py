#!/usr/bin/env python3
"""Check every chapter file under en/. Usage: python3 en/tools/validate.py [root]"""
import json
import re
import sys
from pathlib import Path

LISTS = {"GregMat", "PowerScore", "Magoosh", "VocabCom", "Manhattan"}
SOURCES = {"oewn", "wiktionary", "generated"}


def chapter(word):
    return re.sub("[^a-z]", "", word)[:2]


def score(n_lists, zipf):
    """List agreement (80%) plus closeness to the GRE-core frequency, Zipf 2.5 (20%)."""
    fit = max(0.0, 1 - abs(zipf - 2.5) / 2)
    return round(100 * (0.8 * n_lists / 5 + 0.2 * fit))


def check_entry(e, stem, roots=None):
    w = e.get("word", "?")
    errs = []
    for p in e.get("parts", []):
        if roots is not None and p not in roots:
            errs.append(f"part {p!r} missing from roots.json")
    o = e.get("origin")
    if o is not None and (not o.get("ko") or o.get("source") not in SOURCES):
        errs.append("bad origin")
    if chapter(w) != stem:
        errs.append("wrong chapter")
    if not e.get("lists") or not LISTS.issuperset(e["lists"]) or e["lists"] != sorted(e["lists"]):
        errs.append("bad lists")
    elif e.get("score") != score(len(e["lists"]), e.get("zipf", -9)):
        errs.append("score does not match lists/zipf")
    if not e.get("senses"):
        errs.append("no senses")
    for i, s in enumerate(e.get("senses", []), 1):
        if not s.get("pos") or not s.get("en") or s.get("source") not in SOURCES:
            errs.append(f"sense {i}: missing pos/en/source")
        if e.get("curated") and not s.get("ko"):
            errs.append(f"sense {i}: curated entry without ko")
        if any(x.get("source") not in SOURCES or not x.get("text") for x in s.get("examples", [])):
            errs.append(f"sense {i}: bad example")
    return [f"{stem}/{w}: {m}" for m in errs]


def check_tree(root):
    errs, seen, total, curated = [], set(), 0, 0
    roots_file = root / "roots.json"
    roots = json.loads(roots_file.read_text(encoding="utf-8")) if roots_file.exists() else None
    for path in sorted(root.glob("[a-z]/*.json")):
        stem = path.stem
        if path.parent.name != stem[0]:
            errs.append(f"{path}: chapter in wrong folder")
        entries = json.loads(path.read_text(encoding="utf-8"))
        words = [e.get("word", "") for e in entries]
        if words != sorted(words):
            errs.append(f"{stem}: not alphabetical")
        for e in entries:
            if e.get("word") in seen:
                errs.append(f"{stem}/{e.get('word')}: duplicate")
            seen.add(e.get("word"))
            errs += check_entry(e, stem, roots)
            total += 1
            curated += bool(e.get("curated"))
    return errs, total, curated


if __name__ == "__main__":
    assert chapter("status quo") == "st" and chapter("per se") == "pe"
    assert score(5, 2.5) == 100 and score(1, 5.5) == 16
    errors, n, c = check_tree(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    print("\n".join(errors[:200]))
    print(f"{n} entries, {c} curated, {len(errors)} errors")
    sys.exit(bool(errors))
