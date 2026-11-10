#!/usr/bin/env python3
"""Bundle de/ chapters into words-de.json for the app: by level, then most frequent first. Run after editing chapters."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
words = [e for p in sorted((ROOT / "de").glob("[ab][12]/*.json")) for e in json.loads(p.read_text(encoding="utf-8"))]
words.sort(key=lambda e: (e["level"], -e["zipf"], e["word"].casefold()))
slim = [{k: e[k] for k in ("word", "level", "pos", "grammar", "parts", "senses") if k in e} for e in words]
(ROOT / "words-de.json").write_text(json.dumps(slim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(len(slim), "words,", (ROOT / "words-de.json").stat().st_size // 1024, "KB")
