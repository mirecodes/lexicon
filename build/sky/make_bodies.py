"""meta.json + images -> public/sky/*.jpg and src/bodies.ts, in the order fetch_bodies.py lists them.
Usage: python3 -I make_bodies.py <scratch bodies dir> <repo root>"""
import json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
B, ROOT = Path(sys.argv[1]), Path(sys.argv[2])
meta = json.loads((B / "meta.json").read_text())
src = (Path(__file__).parent / "fetch_bodies.py").read_text()
LEVELS = eval(src[src.index("LEVELS = ") + 9: src.index("\nOPEN")])  # the ordered lists from the fetcher

KIND = {"a1": "small", "a2": "planet", "b1": "deep"}
NEED = {"a1": 14, "a2": 12, "b1": 34}  # German days per level (50 words a day), so no object repeats and none ships unused
# stars on black space get the transparent treatment; Pistol Star, WR 124, RS Puppis, V838 fill the frame with nebulosity
STARS = {"Sun", "Betelgeuse", "Antares", "Mira"}
COMETS = {"Halley's Comet": -45, "Comet Hale-Bopp": 45, "Comet NEOWISE": -10}  # degrees that turn each tail to the top right

def unscreen(src, dst, floor=12, gamma=0.6, feather=0.12):
    """Black sky -> transparent: alpha from brightness (lifted by gamma so solid surfaces stay solid), colour divided back out,
    so the photo still looks the same over black but blends into any card colour. Alpha also fades to 0 over the outer
    `feather` of the frame, so no straight image edge can show (even when rotated). Needs Pillow (the scratch venv)."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    band = feather * min(w, h)
    px = []
    for i, (r, g, b) in enumerate(im.getdata()):
        x, y = i % w, i // w
        edge = min(1.0, min(x, y, w - 1 - x, h - 1 - y) / band) if band else 1.0
        m = max(0.0, (max(r, g, b) - floor) / (255 - floor))
        a = m ** gamma * (edge * edge * (3 - 2 * edge))  # smoothstep falloff at the frame edge
        px.append((0, 0, 0, 0) if a <= 0 else (min(255, round(r / a)), min(255, round(g / a)), min(255, round(b / a)), round(a * 255)))
    out = Image.new("RGBA", im.size)
    out.putdata(px)
    out.save(dst, "WEBP", quality=82, method=6)


sky = ROOT / "public" / "sky"
sky.mkdir(parents=True, exist_ok=True)
out = {}
for lv, items in LEVELS.items():
    out[lv] = []
    for name, _ in items:
        slug, m = next(((s, m) for s, m in meta.items() if m["name"] == name), (None, None))
        if not m or len(out[lv]) >= NEED[lv]:
            continue
        if lv in ("a1", "a2") or name in STARS:  # bodies photographed against black space
            img = f"{slug}.webp"
            # comet photos are ground-based: a hazy blue night sky, not black, so cut a higher floor
            unscreen(B / "img" / f"{slug}.jpg", sky / img, floor=70 if name in COMETS else 12, feather=0.3 if name in COMETS else 0.12)
        else:  # nebulae fill the frame; a soft radial mask is enough
            img = f"{slug}.jpg"
            shutil.copy(B / "img" / img, sky / img)
        credit = m["artist"] or m["credit"] or "Wikimedia Commons"
        b = {"name": name, "img": img, "kind": "comet" if name in COMETS else KIND[lv], "credit": credit, "license": m["license"], "page": m["page"]}
        if name in COMETS:
            b["rotate"] = COMETS[name]
        out[lv].append(b)

body = "\n".join(f'  {lv}: [\n' + "\n".join("    " + json.dumps(b, ensure_ascii=False, separators=(",", ":")) + "," for b in bs) + "\n  ]," for lv, bs in out.items())
(ROOT / "src" / "bodies.ts").write_text(
    "/* Photos behind the German day cards: A1 small solar-system bodies, A2 planets and moons, B1 stars and nebulae.\n"
    "   Lead images of the English Wikipedia articles, kept only when the Commons licence is public domain or CC;\n"
    "   240px copies in public/sky/. Generated; credits are shown in Settings. */\n"
    "/** kind sets the drawn size: small bodies small, planets medium, stars and nebulae nearly the whole card; rotate turns comet tails to the top right */\n"
    "export interface Body { name: string; img: string; kind: \"small\" | \"comet\" | \"planet\" | \"deep\"; rotate?: number; credit: string; license: string; page: string }\n\n"
    f"export const BODIES: Record<\"a1\" | \"a2\" | \"b1\", Body[]> = {{\n{body}\n}};\n",
    encoding="utf-8",
)
print({lv: len(bs) for lv, bs in out.items()}, sum(f.stat().st_size for f in sky.glob("*.jpg")) // 1024, "KB")
