"""Assemble ja/<level>/<row>.json and ja/parts.json from ja_merged.json + jcurated/*.json + kcurated/*.json.
Usage: ja_build.py <W> <ja dir>"""
import json, sys, unicodedata
from pathlib import Path

D, JA = Path(sys.argv[1]), Path(sys.argv[2])
ROWS = {"a": "あいうえおぁぃぅぇぉゔ", "ka": "かきくけこ", "sa": "さしすせそ", "ta": "たちつてとっ", "na": "なにぬねの",
        "ha": "はひふへほ", "ma": "まみむめも", "ya": "やゆよゃゅょ", "ra": "らりるれろ", "wa": "わをんゎ"}
ROW_OF = {c: r for r, cs in ROWS.items() for c in cs}

hira = lambda s: "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def chapter(reading):
    """Gojūon row file for a reading: コーヒー -> ka, ぎんこう -> ka (same rule as jaChapter in scripts/data.ts)."""
    return ROW_OF.get(unicodedata.normalize("NFD", hira(reading[:1]))[:1], "_")


assert chapter("コーヒー") == "ka" and chapter("ぎんこう") == "ka" and chapter("ぱん") == "ha" and chapter("ゆうびん") == "ya"

merged = json.loads((D / "ja_merged.json").read_text())
cur = {x["id"]: x for f in sorted((D / "jcurated").glob("*.json")) for x in json.loads(f.read_text(encoding="utf-8"))}
kko = {x["kanji"]: x["ko"] for f in sorted((D / "kcurated").glob("*.json")) for x in json.loads(f.read_text(encoding="utf-8"))}
kinfo = {k["kanji"]: k for f in sorted((D / "kbatches").glob("*.jsonl")) for k in map(json.loads, open(f, encoding="utf-8"))}

files, missing, used = {}, [], set()
for r in merged:
    c = cur.get(r["id"])
    if not c:
        missing.append(r["word"])
        continue
    e = {"id": r["id"], "word": r["word"], "reading": r["reading"]}
    if "kanji" in r:
        e["kanji"] = r["kanji"]
    e |= {"level": r["level"], "zipf": r["zipf"], "pos": r["grammar"]["type"], "grammar": r["grammar"]}
    if r["parts"]:
        e["parts"] = [f"{k}|kanji" for k in r["parts"]]
        used.update(r["parts"])
    e["senses"] = [{"en": s["en"], "ko": s["ko"], "examples": [{"text": s["example"]["ja"], "ko": s["example"]["ko"], "source": "generated"}],
                    "source": "generated" if s.get("en_source") == "generated" else "jmdict", "ko_source": "generated"}
                   for s in c["senses"]]
    files.setdefault((r["level"], chapter(r["reading"])), []).append(e)

for old in JA.glob("n[1-5]/*.json"):
    old.unlink()
for (lv, ch), es in files.items():
    (JA / lv).mkdir(parents=True, exist_ok=True)
    es.sort(key=lambda e: (hira(e["reading"]), e["word"]))
    (JA / lv / f"{ch}.json").write_text("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False) for e in es) + "\n]\n", encoding="utf-8")

parts = {f"{k}|kanji": {"type": "kanji", "form": k, "ko": kko[k], "on": kinfo[k]["on"], "kun": kinfo[k]["kun"]}
         for k in sorted(used) if k in kko}
(JA / "parts.json").write_text(json.dumps(parts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(sum(map(len, files.values())), "entries in", len(files), "files;", len(parts), "kanji;",
      "missing curation:", missing[:20], "kanji without ko:", sorted(used - set(kko))[:20])
