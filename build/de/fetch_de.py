"""Fetch each German lemma from kaikki.org (English Wiktionary, German section); keep a slim copy in de_wikt/. Safe to re-run."""
import concurrent.futures as cf, json, subprocess, sys, time, urllib.parse
from pathlib import Path

D = Path(sys.argv[1])
OUT = D / "de_wikt"
OUT.mkdir(exist_ok=True)
words = sorted(json.loads((D / "de_merged.json").read_text()))
KEEP_FORM_TAGS = [{"present", "singular", "third-person"}, {"past"}, {"participle", "past"}, {"auxiliary"},
                  {"plural"}, {"genitive"}, {"comparative"}, {"superlative"}]
SKIP = {"obsolete", "archaic", "rare", "dialectal", "historical"}


def etym(t):
    if t.startswith("Etymology tree"):
        t = "\n".join(l for l in t.split("\n")[1:] if " " in l.strip() and len(l) > 30)
    return t[:400]


def slim(e):
    forms = []
    for f in e.get("forms", []):
        tags = set(f.get("tags", []))
        if any(k == tags for k in KEEP_FORM_TAGS) and f["form"] not in ("-",):
            forms.append({"form": f["form"], "tags": sorted(tags)})
    senses = []
    for s in e.get("senses", []):
        if s.get("glosses") and not SKIP & set(s.get("tags", [])):
            senses.append({"gloss": s["glosses"][-1], "tags": [t for t in s.get("tags", []) if t in ("reflexive", "transitive", "intransitive", "separable", "colloquial")]})
    return {"pos": e.get("pos"), "head": next((h.get("expansion") for h in e.get("head_templates", [])), None),
            "forms": forms[:12], "senses": senses[:8], "etym": etym(e.get("etymology_text") or "")}


def fetch(w):
    target = OUT / (urllib.parse.quote(w, safe="") + ".json")
    if target.exists():
        return w, "skip"
    q = urllib.parse.quote
    time.sleep(0.2)
    r = subprocess.run(["curl", "-sS", "-m", "40", "--retry", "2",
                        f"https://kaikki.org/dictionary/German/meaning/{q(w[0])}/{q(w[:2])}/{q(w)}.jsonl"], capture_output=True)
    try:
        ents = [json.loads(l) for l in r.stdout.decode().splitlines() if l.strip()]
    except ValueError:
        ents = []
    ents = [slim(e) for e in ents if e.get("word") == w]
    target.write_text(json.dumps(ents, ensure_ascii=False))
    return w, "ok" if ents else "empty"


with cf.ThreadPoolExecutor(3) as ex:
    res = list(ex.map(fetch, words))
empty = [w for w, s in res if s == "empty"]
print("total", len(res), "empty", len(empty), empty[:120])
