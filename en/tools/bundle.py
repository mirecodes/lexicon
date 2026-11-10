#!/usr/bin/env python3
"""Bundle en/ chapters into words.json for the app, most important words first. Run after editing chapters."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
words = [e for p in sorted((ROOT / "en").glob("[a-z]/*.json")) for e in json.loads(p.read_text(encoding="utf-8"))]
words.sort(key=lambda e: (-e["score"], e["word"]))
slim = [{k: e[k] for k in ("word", "score", "lists", "senses", "parts", "origin") if k in e} for e in words]
(ROOT / "words.json").write_text(json.dumps(slim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(len(slim), "words,", (ROOT / "words.json").stat().st_size // 1024, "KB")
