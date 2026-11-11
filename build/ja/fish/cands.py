"""Commons search candidates (free licence only) as a contact sheet: W/cands/<slug>.jpg + W/cands/<slug>.json.
Usage: cands.py <W> slug="search terms" ..."""
import io, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

W = Path(sys.argv[1])
UA = {"User-Agent": "lexicon-fish-fetch/1.0 (personal study app)"}
(W / "cands").mkdir(exist_ok=True)


def fetch(url):
    for wait in (5, 15, 40, 90):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(wait)
    raise RuntimeError(url)


for arg in sys.argv[2:]:
    slug, q = arg.split("=", 1)
    r = json.loads(fetch("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=24"
                         "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=300&gsrsearch=" + urllib.parse.quote(q)))
    items = []
    for p in sorted(r.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        lic = re.sub(r"<[^>]+>", "", ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", ""))
        if not re.search(r"\.(jpe?g|png)$", p["title"], re.I) or not re.search(r"CC|Public domain|PD|No restrictions", lic, re.I) or "NC" in lic or "ND" in lic:
            continue
        items.append({"file": p["title"], "license": lic, "thumb": ii.get("thumburl")})
        if len(items) == 12:
            break
    sheet = Image.new("RGB", (4 * 300, 3 * 230), "white"); d = ImageDraw.Draw(sheet)
    for i, it in enumerate(items):
        try:
            im = Image.open(io.BytesIO(fetch(it["thumb"]))).convert("RGB"); im.thumbnail((296, 200))
        except Exception:
            continue
        x, y = (i % 4) * 300, (i // 4) * 230
        sheet.paste(im, (x + 2, y + 2)); d.text((x + 4, y + 206), f"{i} {it['license']}", fill="red")
        time.sleep(1)
    sheet.save(W / "cands" / f"{slug}.jpg", quality=80)
    (W / "cands" / f"{slug}.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    print(slug, len(items), flush=True)
    time.sleep(3)
