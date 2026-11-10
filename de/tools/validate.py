#!/usr/bin/env python3
"""Check every chapter file under de/. Usage: python3 de/tools/validate.py [root]"""
import json
import re
import sys
import unicodedata
from pathlib import Path

LEVELS = ("a1", "a2", "b1")
SOURCES = {"wiktionary", "generated"}
GENDERS = {"m", "f", "n"}
PART_TYPES = {"sep", "insep", "stem", "suffix"}


def chapter(word):
    """Letter file for a lemma: first letter with umlauts folded (Äpfel -> a)."""
    s = unicodedata.normalize("NFKD", word.casefold())
    s = re.sub("[^a-z]", "", "".join(c for c in s if not unicodedata.combining(c)))
    return s[:1] or "_"


def check_entry(e, level, letter, parts):
    w, errs = e.get("word", "?"), []
    if e.get("level") != level or chapter(w) != letter:
        errs.append("wrong file")
    g = e.get("grammar") or {}
    if g.get("type") != e.get("pos"):
        errs.append("grammar.type must equal pos")
    if e.get("pos") == "noun" and not (g.get("gender") and GENDERS.issuperset(g["gender"])):
        errs.append("noun without gender")
    if g.get("separable") and not (g.get("prefix") and w.startswith(g["prefix"])):
        errs.append("separable verb needs a matching prefix")
    for p in e.get("parts", []):
        if p not in parts or p.split("|")[1] not in PART_TYPES:
            errs.append(f"unknown part {p}")
    if not e.get("senses"):
        errs.append("no senses")
    for i, s in enumerate(e.get("senses", []), 1):
        if not s.get("en") or not s.get("ko") or s.get("source") not in SOURCES:
            errs.append(f"sense {i}: missing en/ko/source")
        if any(not x.get("text") or not x.get("ko") for x in s.get("examples", [])):
            errs.append(f"sense {i}: bad example")
    return [f"{level}/{letter}/{w}: {m}" for m in errs]


def check_tree(root):
    parts = json.loads((root / "parts.json").read_text(encoding="utf-8"))
    errs, seen, total = [], set(), 0
    for level in LEVELS:
        for path in sorted((root / level).glob("*.json")):
            entries = json.loads(path.read_text(encoding="utf-8"))
            keys = [(e.get("word", "").casefold(), e.get("word", "")) for e in entries]
            if keys != sorted(keys):
                errs.append(f"{level}/{path.stem}: not alphabetical")
            for e in entries:
                if e.get("word") in seen:
                    errs.append(f"{e.get('word')}: duplicate")
                seen.add(e.get("word"))
                errs += check_entry(e, level, path.stem, parts)
                total += 1
    return errs, total


if __name__ == "__main__":
    assert chapter("Äpfel") == "a" and chapter("anrufen") == "a" and chapter("Übung") == "u"
    errors, n = check_tree(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    print("\n".join(errors[:200]))
    print(f"{n} entries, {len(errors)} errors")
    sys.exit(bool(errors))
