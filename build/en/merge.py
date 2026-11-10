"""Merge the 5 chosen GRE lists, normalise, attach Zipf frequency, report stats."""
import collections, csv, gzip, json, statistics as st, sys, unicodedata, xml.etree.ElementTree as ET
from pathlib import Path
from wordfreq import zipf_frequency

D = Path(sys.argv[1])
LISTS = ["GregMat", "PowerScore", "Magoosh", "VocabCom", "Manhattan"]
FIX = {  # typos in the source lists, and inflected forms -> lemma
    "abstemioius": "abstemious", "conflagaration": "conflagration", "decourous": "decorous",
    "idolatrious": "idolatrous", "inerlocutor": "interlocutor", "jucture": "juncture",
    "plebian": "plebeian", "solicitious": "solicitous", "ubiquitious": "ubiquitous",
    "antedated": "antedate", "aspersions": "aspersion", "baying": "bay", "behooves": "behoove",
    "cosseted": "cosset", "discomfiting": "discomfit", "effacing": "efface", "flummoxed": "flummox",
    "importuned": "importune", "venerated": "venerate", "vaunted": "vaunt", "ranks": "rank",
    "contraries": "contrary", "hamstrung": "hamstring", "intertwined": "intertwine",
    "polarized": "polarize", "steeped": "steep", "warranted": "warrant", "attuned": "attune",
    "autonomously": "autonomous", "machinations": "machination",
}


def fold(w):
    w = unicodedata.normalize("NFKD", w.strip().lower())
    return "".join(c for c in w if not unicodedata.combining(c))


oewn = {}
root = ET.parse(gzip.open(D / "oewn/oewn2025.xml.gz")).getroot()
for e in root[0].findall("LexicalEntry"):
    oewn.setdefault(fold(e.find("Lemma").get("writtenForm")), []).append(e.find("Lemma").get("partOfSpeech"))

sources = collections.defaultdict(set)
for n in LISTS:
    with open(D / f"lists/{n}.csv", encoding="utf-8-sig", errors="replace", newline="") as f:
        for r in csv.reader(f):
            if r and r[0].strip() and fold(r[0]) != "e.g.":
                sources[FIX.get(fold(r[0]), fold(r[0]))].add(n)


def score(n_lists, z):
    # ponytail: weights are hand-set; GRE-core Zipf median is ~2.5, so frequency scores as closeness to it
    fit = max(0.0, 1 - abs(z - 2.5) / 2)
    return round(100 * (0.8 * n_lists / 5 + 0.2 * fit))


assert score(5, 2.5) == 100 and score(1, 5.5) == 16 and score(3, 2.5) > score(3, 5.0)

rows = {}
for w, s in sources.items():
    z = zipf_frequency(w, "en")
    rows[w] = {"lists": sorted(s), "zipf": z, "score": score(len(s), z), "in_oewn": w in oewn}
assert "abstemious" in rows and "abstemioius" not in rows and "flummox" in rows
(D / "merged.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0, sort_keys=True))

print("union", len(rows))
for n in LISTS:
    print(n, sum(n in r["lists"] for r in rows.values()))
for k in range(1, 6):
    z = [r["zipf"] for r in rows.values() if len(r["lists"]) == k]
    print(f"exactly {k} lists: n={len(z)} zipf median={st.median(z):.2f} p10={st.quantiles(z, n=10)[0]:.2f} p90={st.quantiles(z, n=10)[-1]:.2f}")
only_vc = [w for w, r in rows.items() if r["lists"] == ["VocabCom"]]
print("only VocabCom", len(only_vc), "with zipf>=4.5:", sum(rows[w]["zipf"] >= 4.5 for w in only_vc), sorted(only_vc, key=lambda w: -rows[w]["zipf"])[:25])
miss = sorted(w for w, r in rows.items() if not r["in_oewn"])
print("not in OEWN", len(miss), miss)
