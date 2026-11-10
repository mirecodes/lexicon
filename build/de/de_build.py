"""Assemble de/<level>/<letter>.json and de/parts.json from Goethe lemmas + Wiktionary grammar + dcurated/*.json."""
import collections, json, re, sys, urllib.parse
from pathlib import Path
from wordfreq import zipf_frequency

D, DE = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(DE / "tools"))
from validate import chapter

merged = json.loads((D / "de_merged.json").read_text())
ART = {"der": "m", "die": "f", "das": "n"}
FORM_OF = re.compile(r"^(?:inflection of|(?:first|second|third)-person\b|(?:singular|plural) imperative|(?:past|present) participle|"
                     r"(?:strong|weak|mixed|nominative|genitive|dative|accusative|comparative|superlative)\b.*\b(?:of|form)\b|"
                     r"(?:alternative|obsolete|dated) (?:form|spelling) of)", re.I)
assert FORM_OF.match("third-person singular present") and FORM_OF.match("past participle of spannen")
assert not FORM_OF.match("person") and not FORM_OF.match("apple (fruit)")
ORDER = ["verb", "adj", "adv", "prep", "conj", "pron", "det", "num", "intj", "particle", "phrase", "noun", "name"]


def lemma_entries(w):
    path = D / "de_wikt" / (urllib.parse.quote(w, safe="") + ".json")
    ents = json.loads(path.read_text()) if path.exists() else []
    return [e for e in ents if e["pos"] != "name" and e["senses"] and not all(FORM_OF.match(s["gloss"]) for s in e["senses"])]


def pick(w, m):
    ents = lemma_entries(w)
    if m["articles"] or w[0].isupper():
        nouns = [e for e in ents if e["pos"] == "noun"]
        want = {ART[a] for a in m["articles"]}
        # homographs with different genders (der/das Band): take the one Goethe's article names
        same = [e for e in nouns if want & set(re.findall(r"^\S+(?: \S+)* ([mfn])\b", e["head"] or ""))]
        if same or nouns:
            return (same or nouns)[0]
    if w[0].islower():
        ents = [e for e in ents if e["pos"] != "noun"] or ents
    # a "verb" entry with no conjugation is usually a stray form; prefer a real adjective/adverb entry
    real_verb = lambda e: e["pos"] != "verb" or any("past" in f["tags"] for f in e["forms"])
    ents = [e for e in ents if real_verb(e)] or ents
    return min(ents, key=lambda e: ORDER.index(e["pos"]) if e["pos"] in ORDER else 99, default=None)


picks = {w: pick(w[5:] if w.startswith("sich ") else w, m) for w, m in merged.items()}
# Goethe rows that are conjugated forms ("packt ein", "war dabei") rather than dictionary words
SEP = "ab|an|auf|aus|bei|ein|fern|fest|her|hin|los|mit|nach|um|vor|weg|zu|zurück|zusammen|dabei|dafür|erkältet|erlaubt"
JUNK = {w for w in merged if picks[w] is None and re.fullmatch(rf"(?:(?:ist|hat|war|wird) .+|\S+t (?:{SEP}))", w)}
JUNK |= {"warmen Pullover", "german word", "fährt", "empfiehlt", "chattet", "entschuldigt", "erinnert", "erreicht"}
# Austrian/Swiss-only words: the app teaches standard (German) German
# ponytail: hand-checked list; the Goethe TSV lost most (A)/(CH) markers and Wiktionary tags over-flag southern German
REGIONAL = {"Abwart", "Brötli", "Bub", "Coiffeur", "Erdapfel", "Glace", "Jause", "Kaffeehaus", "Müesli", "Pensionist",
            "Pensionistin", "Zündholz", "grillieren", "Eck", "Bancomat", "Bankomat-Karte", "Billett", "Couvert",
            "Faschierte", "Fasnacht", "e-card", "Führerausweis", "Hendl", "Fauteuil", "Fleischhauer"}
JUNK |= REGIONAL
assert "packt ein" in JUNK or "packt ein" not in merged


def lemma_of(w, m):
    """'sich freuen' -> ('freuen', reflexive)."""
    if w.startswith("sich ") and w.count(" ") == 1:
        return w[5:], True
    return w, m["reflexive"]


def strip_sich(forms):
    return {k: re.sub(r"\bsich\b ?", "", v).strip() if isinstance(v, str) else v for k, v in (forms or {}).items()}
cur = {}
for f in sorted((D / "dcurated").glob("*.json")):
    cur.update({x["word"]: x for x in json.loads(f.read_text(encoding="utf-8"))})
def form(p, *tags):
    want = set(tags)
    return next((f["form"] for f in p["forms"] if set(f["tags"]) == want), None)


def grammar(w, m, p, c):
    if p and p["pos"] == "noun" and w[0].islower():
        p = None  # 'sich vergnügen' only matched the noun 'Vergnügen'
    pos = (p or {}).get("pos") or ("noun" if m["articles"] else "verb" if c.get("forms") else c.get("pos"))
    head = (p or {}).get("head") or ""
    if pos == "noun":
        genders = [ART[a] for a in m["articles"]] or re.findall(r"^\S+(?: \S+)* ([mfn])\b", head)[:1] or ([c["gender"]] if c.get("gender") else [])
        if not genders:
            return {"type": "other"}  # e.g. the bound form "Lieblings-"
        g = {"type": "noun", "gender": genders, "plural": form(p, "plural") if p else c.get("plural")}
        if m.get("number") == "sg" or g["plural"] == "-":
            g["plural"] = None
        if m.get("number") == "pl" or re.search(r"\bpl\b|plural only", head.split("(")[0]):
            g["number"] = "pl"
        if p and form(p, "genitive"):
            g["genitive"] = form(p, "genitive")
        return g
    if pos == "verb":
        fs = strip_sich(c.get("forms")) if not p else {"present3": form(p, "present", "singular", "third-person"), "past": form(p, "past"),
                                           "pp": form(p, "participle", "past"), "aux": form(p, "auxiliary")}
        fs = fs or {}
        aux = re.search(r"auxiliary (haben or sein|sein or haben|haben|sein)", head)
        if aux:
            fs["aux"] = "haben/sein" if " or " in aux.group(1) else aux.group(1)
        kind = ("modal" if "preterite-present" in head else "irregular" if "irregular" in head else
                "strong" if "strong" in head else "weak" if "weak" in head else None)
        if "weak" in head and "strong" in head:
            kind = "mixed"
        g = {"type": "verb", "class": kind, "reflexive": m["reflexive"], **{k: v for k, v in fs.items() if v}}
        p3 = fs.get("present3") or ""
        if " " in p3 and " " not in w:
            prefix = p3.split()[-1]
            if w.startswith(prefix):
                g["separable"], g["prefix"] = True, prefix
        return g
    if pos == "adj" and p:
        g = {"type": "adj"}
        for k, t in (("comparative", "comparative"), ("superlative", "superlative")):
            if form(p, t):
                g[k] = form(p, t)
        return g
    return {"type": pos or "other"}


entries, part_ko = collections.defaultdict(list), collections.defaultdict(collections.Counter)
missing = []
for w, m in merged.items():
    c, p = cur.get(w), picks.get(w)
    if w in JUNK:
        continue
    if not c:
        missing.append(w)
        continue
    w, refl = lemma_of(w, m)
    if w != c["word"] and w in merged:
        continue  # 'sich freuen' duplicates the 'freuen' row, which already says reflexive
    m = {**m, "reflexive": refl}
    g = grammar(w, m, p, c)
    e = {"word": w, "level": m["level"], "zipf": zipf_frequency(w, "de"), "pos": g["type"], "grammar": g,
         "grammar_source": "wiktionary" if p else "generated"}
    if c.get("parts"):
        e["parts"] = [f"{a['form']}|{a['type']}" for a in c["parts"]]
        for a in c["parts"]:
            part_ko[f"{a['form']}|{a['type']}"][a["ko"]] += 1
    e["senses"] = [{"en": s["en"], "ko": s["ko"],
                    "examples": [{"text": s["example"]["de"], "ko": s["example"]["ko"], "source": "generated"}],
                    "source": "generated" if s.get("en_source") == "generated" else "wiktionary", "ko_source": "generated"}
                   for s in c["senses"]]
    entries[(m["level"], chapter(w))].append(e)

for old in DE.glob("[ab][12]/*.json"):
    old.unlink()
for (level, ch), es in entries.items():
    es.sort(key=lambda e: (e["word"].casefold(), e["word"]))
    path = DE / level / f"{ch}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(es, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
parts = {k: {"form": k.split("|")[0], "type": k.split("|")[1], "ko": cnt.most_common(1)[0][0]} for k, cnt in sorted(part_ko.items())}
(DE / "parts.json").write_text(json.dumps(parts, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
n = sum(map(len, entries.values()))
print(n, "entries,", len(parts), "parts; dropped conjugated rows:", sorted(JUNK), "; missing curation:", len(missing), missing[:20])
print("separable verbs", sum(1 for es in entries.values() for e in es if e["grammar"].get("separable")),
      "| verbs without class", [e["word"] for es in entries.values() for e in es if e["pos"] == "verb" and not e["grammar"].get("class")][:15])
