"""Fetch each merged headword from kaikki.org; keep a slim English-only copy. Safe to re-run."""
import concurrent.futures as cf, json, subprocess, sys, time, urllib.parse
from pathlib import Path

D = Path(sys.argv[1])
OUT = D / "wikt"
OUT.mkdir(exist_ok=True)
words = sorted(json.loads((D / "merged.json").read_text()))


def slim(e):
    senses = []
    for s in e.get("senses", []):
        if not s.get("glosses"):
            continue
        senses.append({
            "gloss": s["glosses"][-1],
            "tags": s.get("tags", []),
            "examples": [x["text"] for x in s.get("examples", []) if x.get("text") and len(x["text"]) < 220][:3],
            "synonyms": [x["word"] for x in s.get("synonyms", []) if x.get("word")][:12],
        })
    return {"pos": e.get("pos"), "senses": senses}


def fetch(w):
    target = OUT / (urllib.parse.quote(w, safe="") + ".json")
    if target.exists():
        return w, "skip"
    url = f"https://kaikki.org/dictionary/English/meaning/{urllib.parse.quote(w[0])}/{urllib.parse.quote(w[:2])}/{urllib.parse.quote(w)}.jsonl"
    time.sleep(0.2)
    r = subprocess.run(["curl", "-sS", "-m", "40", "--retry", "2", url], capture_output=True)
    try:
        ents = [json.loads(l) for l in r.stdout.decode().splitlines() if l.strip()]
    except ValueError:
        return w, "bad"
    ents = [e for e in ents if e.get("lang_code", "en") == "en" and e.get("word", "").lower() == w]
    if not ents:
        return w, "empty"
    target.write_text(json.dumps([slim(e) for e in ents], ensure_ascii=False))
    return w, "ok"


with cf.ThreadPoolExecutor(3) as ex:
    res = list(ex.map(fetch, words))
bad = [w for w, s in res if s in ("bad", "empty")]
print("total", len(res), "failed", len(bad), bad[:80])
