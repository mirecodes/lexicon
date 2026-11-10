"""Fetch Wiktionary etymology text for each headword into etym/<word>.json. Safe to re-run."""
import concurrent.futures as cf, json, subprocess, sys, time, urllib.parse
from pathlib import Path

D = Path(sys.argv[1])
OUT = D / "etym"
OUT.mkdir(exist_ok=True)
words = sorted(json.loads((D / "merged.json").read_text()))


def fetch(w):
    target = OUT / (urllib.parse.quote(w, safe="") + ".json")
    if target.exists():
        return w, "skip"
    q = urllib.parse.quote
    time.sleep(0.2)
    r = subprocess.run(["curl", "-sS", "-m", "40", "--retry", "2",
                        f"https://kaikki.org/dictionary/English/meaning/{q(w[0])}/{q(w[:2])}/{q(w)}.jsonl"], capture_output=True)
    try:
        ents = [json.loads(l) for l in r.stdout.decode().splitlines() if l.strip()]
    except ValueError:
        return w, "bad"
    seen, out = set(), []
    for e in ents:
        t = e.get("etymology_text") or ""
        if t.startswith("Etymology tree"):
            # the tree is one short node per line; the prose follows it
            t = "\n".join(l for l in t.split("\n")[1:] if " " in l.strip() and len(l) > 30)
        if e.get("lang_code", "en") == "en" and e.get("word", "").lower() == w and t and t not in seen:
            seen.add(t)
            out.append({"pos": e.get("pos"), "etym": t[:500]})
    target.write_text(json.dumps(out, ensure_ascii=False))
    return w, "ok" if out else "none"


with cf.ThreadPoolExecutor(3) as ex:
    res = list(ex.map(fetch, words))
print("total", len(res), "no etymology", sum(s == "none" for _, s in res), "bad", [w for w, s in res if s == "bad"][:40])
