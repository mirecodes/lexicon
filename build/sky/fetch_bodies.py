"""Find each body's Wikipedia lead image on Commons, keep it only if openly licensed, save a thumbnail + credit.
Usage: python3 -I fetch_bodies.py <out dir for images> <out json>"""
import json, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

OUT, META = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "LexiconStudyApp/1.0 (static site build; image credits recorded)"}

LEVELS = {
    "a1": [("Ceres", "Ceres (dwarf planet)"), ("Vesta", "4 Vesta"), ("Eros", "433 Eros"), ("Ida", "243 Ida"), ("Itokawa", "25143 Itokawa"),
           ("Ryugu", "162173 Ryugu"), ("Bennu", "101955 Bennu"), ("Arrokoth", "486958 Arrokoth"), ("Lutetia", "21 Lutetia"),
           ("Halley's Comet", "Halley's Comet"), ("Comet Hale-Bopp", "Comet Hale–Bopp"), ("Comet 67P", "67P/Churyumov–Gerasimenko"),
           ("Comet NEOWISE", "C/2020 F3 (NEOWISE)"), ("Tempel 1", "9P/Tempel"), ("Dimorphos", "Dimorphos"), ("Phobos", "Phobos (moon)")],
    "a2": [("Mercury", "Mercury (planet)"), ("Venus", "Venus"), ("Earth", "Earth"), ("Moon", "Moon"), ("Mars", "Mars"), ("Jupiter", "Jupiter"),
           ("Io", "Io (moon)"), ("Europa", "Europa (moon)"), ("Saturn", "Saturn"), ("Titan", "Titan (moon)"), ("Uranus", "Uranus"),
           ("Neptune", "Neptune"), ("Ganymede", "Ganymede (moon)"), ("Enceladus", "Enceladus")],
    # stars: their articles lead with constellation maps, so name the Commons photo directly
    "b1": [("Sun", "File:The Sun by the Atmospheric Imaging Assembly of NASA's Solar Dynamics Observatory - 20100819.jpg"), ("Betelgeuse", "File:Betelgeuse captured by ALMA.jpg"), ("WR 140", "WR 140"),  # Webb's nested dust shells; replaces Eta Carinae, whose lobed photo looked unpleasant
           ("RS Puppis", "RS Puppis"),  # replaces Sirius, whose only real photo is a blurry overexposed point ("Antares", "File:VLTI reconstructed view of the surface of Antares.jpg"),
           ("Pistol Star", "Pistol Star"), ("WR 124", "WR 124"), ("Mira", "File:Mira 1997.jpg"),
           ("Westerlund 2", "Westerlund 2"),  # Polaris and Fomalhaut had only a diagram and an artist's impression ("V838 Monocerotis", "V838 Monocerotis"),
           ("Orion Nebula", "Orion Nebula"), ("Crab Nebula", "Crab Nebula"), ("Pillars of Creation", "File:Pillars of Creation (NIRCam Image).jpg"),  # Webb; Hubble's has the stepped WFPC2 frame
           ("Ring Nebula", "Ring Nebula"), ("Helix Nebula", "Helix Nebula"), ("Cat's Eye Nebula", "Cat's Eye Nebula"),
           ("Horsehead Nebula", "Horsehead Nebula"), ("Lagoon Nebula", "Lagoon Nebula"), ("Trifid Nebula", "Trifid Nebula"),
           ("Carina Nebula", "Carina Nebula"), ("Tarantula Nebula", "Tarantula Nebula"), ("Rosette Nebula", "Rosette Nebula"),
           ("Dumbbell Nebula", "Dumbbell Nebula"), ("Veil Nebula", "Veil Nebula"), ("Bubble Nebula", "Bubble Nebula"),
           ("Butterfly Nebula", "NGC 6302"), ("Southern Ring Nebula", "NGC 3132"), ("Eskimo Nebula", "Eskimo Nebula"),
           ("Omega Nebula", "Omega Nebula"), ("Pleiades", "Pleiades"), ("Boomerang Nebula", "Boomerang Nebula"),
           ("Cone Nebula", "Cone Nebula"), ("Ant Nebula", "Ant Nebula"), ("Red Rectangle", "Red Rectangle Nebula"),
           ("Heart Nebula", "Heart Nebula"), ("Eagle Nebula", "Eagle Nebula"), ("Cassiopeia A", "Cassiopeia A"),
           # spares, in case some of the above have no openly licensed lead image
           ("Owl Nebula", "Owl Nebula"), ("Spirograph Nebula", "IC 418"), ("Hourglass Nebula", "MyCn 18"), ("Flame Nebula", "Flame Nebula"),
           ("Crescent Nebula", "Crescent Nebula"), ("Elephant's Trunk Nebula", "Elephant's Trunk Nebula"), ("Pelican Nebula", "Pelican Nebula"),
           ("Ghost of Jupiter", "NGC 3242"), ("Little Ghost Nebula", "NGC 6369")],
}
OPEN = re.compile(r"^(public domain|pd\b|cc0|cc[ -]by(-sa)?\b|attribution$)", re.I)  # "Attribution": Commons' free credit-only licence


def get(url):
    for i in range(4):  # curl: this Python has no CA bundle
        r = subprocess.run(["curl", "-sSfL", "-m", "40", "-A", UA["User-Agent"], url], capture_output=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(10 + 15 * i)  # 429 / transient
    raise RuntimeError(url)


def api(host, **q):
    return json.loads(get(f"https://{host}/w/api.php?" + urllib.parse.urlencode({"format": "json", "formatversion": 2, **q})))


def strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def fetch(meta, lv, name, title):
    if title.startswith("File:"):
        file = title[5:]
    else:
        page = api("en.wikipedia.org", action="query", prop="pageimages", piprop="name", titles=title, redirects=1)["query"]["pages"][0]
        file = page.get("pageimage")
    if not file:
        return print("NO IMAGE", lv, name)
    info = api("commons.wikimedia.org", action="query", titles=f"File:{file}", prop="imageinfo",
               iiprop="url|extmetadata", iiurlwidth=320)["query"]["pages"][0]
    if "imageinfo" not in info:
        return print("NOT ON COMMONS", lv, name, file)
    ii = info["imageinfo"][0]; em = ii["extmetadata"]
    lic = strip(em.get("LicenseShortName", {}).get("value"))
    if not OPEN.match(lic):
        return print("SKIP LICENSE", lv, name, lic)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    raw, dst = OUT / f"{slug}.src", OUT / f"{slug}.jpg"
    raw.write_bytes(get(ii["thumburl"]))
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72", "-Z", "240", str(raw), "--out", str(dst)], check=True, capture_output=True)
    raw.unlink()
    meta[slug] = {"level": lv, "name": name, "file": file, "license": lic, "artist": strip(em.get("Artist", {}).get("value"))[:160],
                  "credit": strip(em.get("Credit", {}).get("value"))[:160], "page": ii["descriptionurl"]}
    print("OK", lv, name, lic, dst.stat().st_size)


meta = json.loads(META.read_text()) if META.exists() else {}
for lv, items in LEVELS.items():
    for name, title in items:
        if any(m["name"] == name for m in meta.values()):
            continue
        try:
            fetch(meta, lv, name, title)
        except Exception as e:
            print("FAIL", lv, name, e)
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        time.sleep(2)
