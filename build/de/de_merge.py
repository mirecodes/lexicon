"""Normalize Goethe A1/A2/B1 headwords -> de_merged.json {lemma: {level, articles, reflexive, raw}}."""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1])


REGIONAL = re.compile(r"\((?:A|CH|A, CH|CH, A)\)|\(A\b")


def parse(raw):
    """-> (lemma, articles, reflexive, number) or None for regional/junk rows."""
    s = re.sub(r"\(\d+\)", "", raw).strip()
    if REGIONAL.search(s.split("→")[0]):
        return None                       # Austrian / Swiss variant: not standard German
    s = s.split("→")[0].strip()
    number = "sg" if re.search(r"\((?:Sg\.?|Sing\.)\)", s) else "pl" if re.search(r"\([Pp]l\.\)", s) else None
    s = re.sub(r"\((?:Sg\.?|Sing\.|[Pp]l\.|D)\)", "", s).strip()
    s = s.split(",")[0].strip()          # drop plural notation like ", -e"
    s = s.split("/")[0].strip() if not re.match(r"^(der|die|das)/", s) else s
    reflexive = bool(re.match(r"^\(sich", s))
    s = re.sub(r"^\(sich[^)]*\)", "", s).strip()
    s = re.sub(r"\(([A-Z])-\)", r"\1-", s)          # (E-)Mail -> E-Mail
    s = re.sub(r"\([^)]*-?\)", "", s).strip(" -")    # (Back-)Ofen -> Ofen, (ab)fahren -> fahren, Grad (Celsius) -> Grad
    m = re.match(r"^((?:der|die|das)(?:/(?:der|die|das))*)\s+(.+)$", s)
    articles = m.group(1).split("/") if m else []
    lemma = (m.group(2) if m else s).strip(" -")
    if not lemma or "(" in lemma or ")" in lemma or re.search(r"\s(der|die|das)\s", lemma):
        return None
    return lemma, articles, reflexive, number


assert parse("die Adresse,-en") == ("Adresse", ["die"], False, None)
assert parse("(sich) anmelden") == ("anmelden", [], True, None)
assert parse("der/die Bekannte") == ("Bekannte", ["der", "die"], False, None)
assert parse("abholen(2)") == ("abholen", [], False, None)
assert parse("das Geld (Sg.)") == ("Geld", ["das"], False, "sg")
assert parse("die Eltern (Pl.)") == ("Eltern", ["die"], False, "pl")
assert parse("die (E-)Mail, -s") == ("E-Mail", ["die"], False, None)
assert parse("der (Back-)Ofen, -ö") == ("Ofen", ["der"], False, None)
assert parse("(sich etwas) kaufen") == ("kaufen", [], True, None)
assert parse("der Bancomat (CH)") is None
assert parse("das (Schlag-)Obers (A)") is None

out = {}
for level in ["a1", "a2", "b1"]:
    for raw in open(D / "de_lists" / f"{level}.txt", encoding="utf-8"):
        if not raw.strip():
            continue
        p = parse(raw)
        if not p:
            continue
        lemma, articles, refl, number = p
        e = out.setdefault(lemma, {"level": level, "articles": [], "reflexive": False, "number": None, "raw": []})
        e["articles"] = sorted(set(e["articles"]) | set(articles))
        e["reflexive"] |= refl
        e["number"] = e["number"] or number
        if raw.strip() not in e["raw"]:
            e["raw"].append(raw.strip())
(D / "de_merged.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
by = {l: sum(e["level"] == l for e in out.values()) for l in ["a1", "a2", "b1"]}
print(len(out), "lemmas", by, "multiword", sum(" " in w for w in out))
