"""Lead image + Commons licence for each fish's English Wikipedia article -> raw/<slug>.<ext>, meta.json.
Usage: fetch.py <out dir> [title=File:Override.jpg ...]"""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path(sys.argv[1])
OVERRIDE = dict(a.split("=", 1) for a in sys.argv[2:])
UA = {"User-Agent": "lexicon-fish-fetch/1.0 (personal study app)"}
FISH = {
    "n5": [  # tropical fish
        ("Ocellaris clownfish", "흰동가리"), ("Blue tang", "블루탱"), ("Moorish idol", "깃대돔"), ("Mandarinfish", "만다린피시"),
        ("Royal gramma", "로열그라마"), ("Siamese fighting fish", "베타"), ("Neon tetra", "네온테트라"), ("Guppy", "구피"),
        ("Discus (fish)", "디스커스"), ("Pterophyllum scalare", "엔젤피시"), ("Yellow tang", "옐로탱"), ("Emperor angelfish", "황제엔젤피시"),
        ("Red lionfish", "쏠배감펭"), ("Copperband butterflyfish", "두동가리돔"),
    ],
    "n4": [  # fish found in Korea
        ("Chub mackerel", "고등어"), ("Largehead hairtail", "갈치"), ("Small yellow croaker", "참조기"), ("Alaska pollock", "명태"),
        ("Olive flounder", "넙치 (광어)"), ("Korean rockfish", "조피볼락 (우럭)"), ("Red seabream", "참돔"), ("Flathead grey mullet", "숭어"),
        ("Ayu sweetfish", "은어"), ("Siniperca scherzeri", "쏘가리"), ("Coreoleuciscus splendidus", "쉬리"), ("Common carp", "잉어"),
        ("Amur catfish", "메기"),
    ],
    "n3": [  # large species
        ("Atlantic bluefin tuna", "참다랑어"), ("Yellowfin tuna", "황다랑어"), ("Swordfish", "황새치"), ("Atlantic blue marlin", "청새치"),
        ("Sailfish", "돛새치"), ("Whale shark", "고래상어"), ("Great white shark", "백상아리"), ("Giant oceanic manta ray", "쥐가오리"),
        ("Ocean sunfish", "개복치"), ("Giant grouper", "대왕바리"), ("Humphead wrasse", "나폴레옹피시"), ("Mahi-mahi", "만새기"),
        ("Giant trevally", "무명갈전갱이"), ("Arapaima", "피라루쿠"), ("Beluga (sturgeon)", "벨루가 철갑상어"), ("Great hammerhead", "큰귀상어"),
        ("Giant oarfish", "산갈치"),
    ],
}
slug = lambda t: re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
def fetch(url):
    for wait in (5, 15, 40, 90):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(wait)
    raise RuntimeError("rate limited: " + url)


get = lambda url: json.loads(fetch(url))
strip = lambda h: re.sub(r"<[^>]+>", "", h or "").strip()

(OUT / "raw").mkdir(parents=True, exist_ok=True)
meta = json.loads((OUT / "meta.json").read_text()) if (OUT / "meta.json").exists() else {}
for lv, items in FISH.items():
    for title, ko in items:
        s = slug(title)
        file = OVERRIDE.get(title)
        if not file and s in meta and meta[s]["file"]:
            continue
        if not file:
            p = get("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&piprop=name&redirects=1&titles=" + urllib.parse.quote(title))
            page = next(iter(p["query"]["pages"].values()))
            file = "File:" + page.get("pageimage", "") if page.get("pageimage") else None
        if not file:  # no free lead image: first photo from a Commons search
            r = get("https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srnamespace=6&srlimit=5&srsearch="
                    + urllib.parse.quote(title.split(" (")[0] + " fish"))
            file = next((x["title"] for x in r["query"]["search"] if re.search(r"\.(jpe?g|png)$", x["title"], re.I)), None)
        if not file:
            print("NO IMAGE", title); meta[s] = {"title": title, "ko": ko, "level": lv, "file": None}; continue
        q = get("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=900&titles=" + urllib.parse.quote(file))
        info = next(iter(q["query"]["pages"].values()))["imageinfo"][0]
        md = info["extmetadata"]
        lic = strip(md.get("LicenseShortName", {}).get("value"))
        url = info["thumburl"]
        ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
        (OUT / "raw" / f"{s}.{ext}").write_bytes(fetch(url))
        meta[s] = {"title": title, "ko": ko, "level": lv, "file": file, "ext": ext, "license": lic,
                   "credit": strip(md.get("Artist", {}).get("value"))[:160], "page": info["descriptionurl"]}
        print(lv, s, lic, file, flush=True)
        (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        time.sleep(4)
(OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
