"""Join the Waller JLPT lists with JMdict -> ja_merged.json, jbatches/NN.jsonl (words) and kbatches/NN.jsonl (kanji).
Usage: ja_merge.py <W> [levels]   levels default: 5,4,3"""
import csv, json, sys
from pathlib import Path
from wordfreq import zipf_frequency

D = Path(sys.argv[1])
LEVELS = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "5,4,3").split(",")]
SIZE = 200

jm = json.loads(next((D / "dict").glob("jmdict-eng-*.json")).read_text())
J = {w["id"]: w for w in jm["words"]}
kd = json.loads(next((D / "dict").glob("kanjidic2-en-*.json")).read_text())
K = {c["literal"]: c for c in kd["characters"]}

GODAN = {"v5u", "v5k", "v5k-s", "v5g", "v5s", "v5t", "v5n", "v5b", "v5m", "v5r", "v5r-i", "v5aru", "v5u-s"}
SIMPLE = {"n": "noun", "n-adv": "noun", "n-t": "noun", "n-pr": "noun", "num": "num", "pn": "pron", "adv": "adv", "adv-to": "adv",
          "conj": "conj", "int": "interj", "prt": "particle", "exp": "expr", "ctr": "counter", "suf": "suffix", "n-suf": "suffix",
          "pref": "prefix", "n-pref": "prefix", "adj-pn": "adnominal", "aux": "aux", "aux-v": "aux", "aux-adj": "aux", "cop": "aux",
          "adj-no": "noun", "adj-f": "adnominal"}


def grammar(tags):
    """JMdict part-of-speech tags of the first sense -> our grammar object."""
    t = set(tags)
    if t & (GODAN | {"v1", "v1-s", "vs-i", "vs-s", "vk", "v2a-s"}):
        cls = ("godan" if t & GODAN else "ichidan" if t & {"v1", "v1-s"} else "kuru" if "vk" in t else
               "suru" if t & {"vs-i", "vs-s"} else "other")
        g = {"type": "verb", "class": cls}
        if ("vt" in t) != ("vi" in t):
            g["transitive"] = "vt" in t
        return g
    if t & {"adj-i", "adj-ix"}:
        return {"type": "adj", "class": "i"}
    if "adj-na" in t:
        return {"type": "adj", "class": "na"}
    g = {"type": next((SIMPLE[x] for x in tags if x in SIMPLE), "other")}
    if "vs" in t:
        g["suru"] = True  # 勉強 -> 勉強する
    return g


assert grammar(["v1", "vt"]) == {"type": "verb", "class": "ichidan", "transitive": True}
assert grammar(["n", "vs", "vt"]) == {"type": "noun", "suru": True}
assert grammar(["adj-na", "n"]) == {"type": "adj", "class": "na"}

is_kanji = lambda ch: "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿"
rows, seen = [], set()
for n in LEVELS:
    for r in csv.DictReader(open(D / "lists" / "yomi" / f"n{n}.csv", encoding="utf-8")):
        i = r["jmdict_seq"]
        if i in seen:
            continue  # lowest level wins
        seen.add(i)
        e = J[i]
        uk = "uk" in e["sense"][0]["misc"]
        word = r["kana"] if uk or not r["kanji"] else r["kanji"]
        senses = [s for s in e["sense"] if (r["kanji"] and "*" in s["appliesToKanji"] or r["kanji"] in s["appliesToKanji"])
                  or not r["kanji"] and ("*" in s["appliesToKana"] or r["kana"] in s["appliesToKana"])] or e["sense"]
        row = {"id": int(i), "word": word, "reading": r["kana"], "level": f"n{n}", "zipf": zipf_frequency(word, "ja"),
               "grammar": grammar(e["sense"][0]["partOfSpeech"]),
               "senses": [{"gloss": "; ".join(g["text"] for g in s["gloss"]), "pos": s["partOfSpeech"], "misc": s["misc"]}
                          for s in senses][:8]}
        if word != r["kanji"] and r["kanji"]:
            row["kanji"] = r["kanji"]  # usually written in kana: いる (居る)
        row["parts"] = [c for c in dict.fromkeys(word) if is_kanji(c)]
        rows.append(row)

(D / "ja_merged.json").write_text(json.dumps(rows, ensure_ascii=False))
for name, items in (("jbatches", [{k: r[k] for k in ("id", "word", "reading", "level", "grammar", "senses")} | ({"kanji": r["kanji"]} if "kanji" in r else {}) for r in rows]),):
    out = D / name
    out.mkdir(exist_ok=True)
    for i in range(0, len(items), SIZE):
        with open(out / f"{i // SIZE + 1:02d}.jsonl", "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in items[i:i + SIZE])

# kanji: meanings and Korean sound (eum) from KANJIDIC2, for the worker that writes 훈음
words_of = {}
for r in rows:
    for c in r["parts"]:
        words_of.setdefault(c, []).append(r["word"])
kanji = []
for c, ws in words_of.items():
    rm = (K.get(c) or {}).get("readingMeaning") or {"groups": []}
    rd = [x for g in rm["groups"] for x in g["readings"]]
    kanji.append({"kanji": c, "en": [m["value"] for g in rm["groups"] for m in g["meanings"] if m["lang"] == "en"][:5],
                  "eum": [x["value"] for x in rd if x["type"] == "korean_h"],
                  "on": [x["value"] for x in rd if x["type"] == "ja_on"], "kun": [x["value"] for x in rd if x["type"] == "ja_kun"],
                  "words": ws[:4]})
out = D / "kbatches"
out.mkdir(exist_ok=True)
KSIZE = 500
for i in range(0, len(kanji), KSIZE):
    with open(out / f"{i // KSIZE + 1:02d}.jsonl", "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in kanji[i:i + KSIZE])
print(len(rows), "words", (len(rows) + SIZE - 1) // SIZE, "batches;", len(kanji), "kanji,", sum(not k["eum"] for k in kanji), "without Korean reading")
