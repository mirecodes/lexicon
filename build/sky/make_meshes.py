"""Photos -> low-poly meshes for the German day cards.
Usage: <venv>/python -I make_meshes.py <scratch bodies dir> <repo root>
Reads src/bodies.ts for the objects in use, writes public/sky/meshes.json:
  {img: {"k": kind, "p": [x0,y0,x1,y1...] (0-100), "t": [i,j,k,...], "c": "rrggbbA" per triangle (A = alpha 0-9)}}"""
import json, math, random, re, sys
from pathlib import Path
from PIL import Image, ImageFilter

B, ROOT = Path(sys.argv[1]), Path(sys.argv[2])
bodies = [json.loads(l.strip().rstrip(",")) for l in (ROOT / "src" / "bodies.ts").read_text().splitlines() if l.strip().startswith('{"name"')]
META = json.loads((B / "meta.json").read_text())
SLUG = {m["name"]: s for s, m in META.items()}

# points per kind: enough to show bands/craters/filaments, few enough to stay a light mesh
POINTS = {"small": 70, "comet": 80, "planet": 95, "deep": 150}
SPECIAL = {"Pillars of Creation": 240, "Saturn": 130, "Jupiter": 120, "Crab Nebula": 190, "Sun": 110}
FRAME_FILL = {"Pistol Star", "WR 124", "RS Puppis", "V838 Monocerotis", "WR 140"}  # star fields that fill the frame
SIZE = 96  # analysis grid


def load(name, kind):
    im = Image.open(B / "img" / f"{SLUG[name]}.jpg").convert("RGB")
    w, h = im.size
    if kind == "deep":  # cover: centre square, like the photo version
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    else:  # contain: whole object, padded with black
        s = max(w, h)
        pad = Image.new("RGB", (s, s))
        pad.paste(im, ((s - w) // 2, (s - h) // 2))
        im = pad
    return im.resize((SIZE, SIZE), Image.LANCZOS)


def delaunay(pts):
    """Bowyer-Watson; fine for a few hundred points."""
    big = 1e4
    sp = [(-big, -big), (big * 2, -big), (-big, big * 2)]
    P = list(pts) + sp
    n = len(pts)
    tris = [(n, n + 1, n + 2)]

    def circ(t):
        (ax, ay), (bx, by), (cx, cy) = P[t[0]], P[t[1]], P[t[2]]
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)) or 1e-12
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
        return ux, uy, (ax - ux) ** 2 + (ay - uy) ** 2

    cache = {}
    for i, (x, y) in enumerate(pts):
        bad = []
        for t in tris:
            c = cache.get(t) or cache.setdefault(t, circ(t))
            if (x - c[0]) ** 2 + (y - c[1]) ** 2 < c[2]:
                bad.append(t)
        edges = {}
        for t in bad:
            for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = tuple(sorted(e))
                edges[k] = edges.get(k, 0) + 1
        bs = set(bad)
        tris = [t for t in tris if t not in bs]
        tris += [(a, b, i) for (a, b), cnt in edges.items() if cnt == 1]
    return [t for t in tris if max(t) < n]


def mesh(name, kind):
    im = load(name, kind)
    px = im.load()
    lum = im.convert("L")
    grad = lum.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1)).load()
    lum = lum.load()
    framed = False  # glass follows the object's own glowing region, never the whole square
    # floor: brightness counted as empty sky. Comets: hazy sky, keep the faint tail. Nebulae: keep the gas, drop the dark field
    floor = 38 if kind == "comet" else 14
    if kind == "deep":  # nebulae differ a lot in brightness: keep roughly their brightest half
        v = sorted(max(px[x, y]) for y in range(SIZE) for x in range(SIZE))
        floor = max(34, v[int(len(v) * (0.62 if name in FRAME_FILL else 0.5))])

    def alpha(x, y):
        x, y = min(SIZE - 1, max(0, int(x))), min(SIZE - 1, max(0, int(y)))
        r, g, b = px[x, y]
        m = max(0.0, (max(r, g, b) - floor) / (255 - floor))
        return m ** 0.6

    rnd = random.Random(name)
    n = SPECIAL.get(name, POINTS[kind])
    pts = []
    mind = 100 / math.sqrt(n) * 0.55

    def far(x, y):
        return all((x - a) ** 2 + (y - b) ** 2 >= mind * mind for a, b in pts)

    if framed:
        for x, y in ((0, 0), (SIZE - 1, 0), (0, SIZE - 1), (SIZE - 1, SIZE - 1)):
            pts.append((x, y))
        for i in range(1, 6):  # frame edges, so the stained glass reaches the border
            for p in ((i * SIZE / 6, 0), (i * SIZE / 6, SIZE - 1), (0, i * SIZE / 6), (SIZE - 1, i * SIZE / 6)):
                pts.append(p)
    else:  # silhouette: points where alpha crosses the edge of the body
        edge = [(x, y) for y in range(1, SIZE - 1) for x in range(1, SIZE - 1)
                if alpha(x, y) > 0.3 and min(alpha(x - 1, y), alpha(x + 1, y), alpha(x, y - 1), alpha(x, y + 1)) <= 0.3]
        rnd.shuffle(edge)
        for x, y in edge:
            if len(pts) >= n * 0.3:
                break
            if far(x, y):
                pts.append((x, y))
    tries = 0
    while len(pts) < n and tries < 40000:  # interior, denser where the surface changes (bands, craters, filaments)
        tries += 1
        x, y = rnd.uniform(0, SIZE - 1), rnd.uniform(0, SIZE - 1)
        a = 1.0 if framed else alpha(x, y)
        if a < 0.25:
            continue
        w = 0.25 + min(1.0, grad[int(x), int(y)] / 60)
        if rnd.random() < w and far(x, y):
            pts.append((x, y))

    tris = delaunay(pts)
    out_t, out_c = [], []
    for t in tris:
        (ax, ay), (bx, by), (cx, cy) = (pts[i] for i in t)
        samples = [((ax + bx + cx) / 3, (ay + by + cy) / 3), ((ax + bx) / 2, (ay + by) / 2), ((bx + cx) / 2, (by + cy) / 2), ((cx + ax) / 2, (cy + ay) / 2)]
        al = [alpha(x, y) for x, y in samples]
        if not framed and (sum(al) / 4 < 0.16 or min(al) < 0.03):  # keep the silhouette: drop triangles that bridge empty sky
            continue
        cols = [px[min(SIZE - 1, int(x)), min(SIZE - 1, int(y))] for x, y in samples]
        r, g, b = (sum(c[k] for c in cols) / 4 for k in range(3))
        a = sum(al) / 4 if not framed else max(0.15, sum(max(c) for c in cols) / 4 / 255)
        mx = max(r, g, b, 1)
        r, g, b = (min(255, round(v * 255 / mx * 0.85 + v * 0.15)) for v in (r, g, b))  # normalise brightness, keep hue
        out_t += list(t)
        out_c.append(f"{r:02x}{g:02x}{b:02x}{min(9, round(a * 9))}")
    scale = 100 / (SIZE - 1)
    return {"k": "glass" if kind == "deep" else kind, "p": [round(v * scale, 1) for p in pts for v in p], "t": out_t, "c": "".join(out_c)}


"""3D: globes (planets, moons, stars), rocks (asteroids, comet nuclei), relief (Pillars). Everything else stays flat (z = 0)."""
GLOBE_STARS = {"Sun", "Betelgeuse", "Antares", "Mira"}


def icosphere(level):
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    V = [tuple(c / math.sqrt(sum(k * k for k in v)) for c in v) for v in V]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        mid, F2 = {}, []

        def m(a, b):
            k = (min(a, b), max(a, b))
            if k not in mid:
                p = [(V[a][i] + V[b][i]) / 2 for i in range(3)]
                l = math.sqrt(sum(c * c for c in p))
                V.append(tuple(c / l for c in p))
                mid[k] = len(V) - 1
            return mid[k]
        for a, b, c in F:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = F2
    return V, F


def disk(im, floor):
    """centre and radius of the bright body in a contain-padded photo"""
    px = im.load()
    pts = [(x, y) for y in range(SIZE) for x in range(SIZE) if max(px[x, y]) > floor + 30]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return cx, cy, max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1, pts


MEAN = {}


def colour(px, x, y, mean=None):
    """3x3 average around (x, y); too-dark samples (space, shadow) fall back to the body's mean colour,
    so black limb pixels never turn into vivid noise when brightness is lifted"""
    acc, n = [0, 0, 0], 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            p = px[min(SIZE - 1, max(0, int(x) + dx)), min(SIZE - 1, max(0, int(y) + dy))]
            acc = [a + b for a, b in zip(acc, p)]
            n += 1
    r, g, b = (v / n for v in acc)
    if mean and max(r, g, b) < 40:
        r, g, b = mean
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    s, v = min(1.0, s * 1.8 + 0.08), max(v, 0.72)  # thin lines need clear colour: richer hue, never dark
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


def body_mean(px, pts):
    s = [0, 0, 0]
    for x, y in pts:
        s = [a + b for a, b in zip(s, px[x, y])]
    return tuple(v / max(1, len(pts)) for v in s)


def solid(name, kind):
    im = load(name, kind)
    px = im.load()
    cx, cy, R, lit = disk(im, 14)
    mean = body_mean(px, lit)
    rock = kind == "small"
    ringed = name == "Saturn"
    if ringed:  # the photo's width includes the rings: size the globe from its height
        ys = [p[1] for p in lit if abs(p[0] - cx) < 4]
        R = (max(ys) - min(ys)) / 2 if ys else R * 0.45
    V, F = icosphere(2)
    prof = None
    if rock:  # silhouette radius by angle in the image plane, so long rocks (Itokawa) stay long
        prof = []
        for k in range(72):
            a = k / 72 * math.tau
            r = 0
            for s in range(1, int(R * 1.6)):
                x, y = cx + math.cos(a) * s, cy + math.sin(a) * s
                if 0 <= x < SIZE and 0 <= y < SIZE and max(px[int(x), int(y)]) > 44:
                    r = s
            prof.append(max(r, R * 0.25) / R)
    rnd = random.Random(name)
    bumps = [(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(.05, .12)) for _ in range(6)] if rock else []
    out_v = []
    for x, y, z in V:
        s = 1.0
        if rock:
            a = math.atan2(y, x) % math.tau
            rp = prof[int(a / math.tau * 72) % 72]
            xy = math.hypot(x, y)
            s = rp * xy + (sum(prof) / 72) * 0.8 * (1 - xy)  # limb follows the outline, the view axis gets average depth
            s *= 1 + sum(h * math.exp(-((x - bx) ** 2 + (y - by) ** 2 + (z - bz) ** 2) * 6) for bx, by, bz, h in bumps)
        out_v.append((x * s, y * s, z * s))
    cols = []
    for f in F:
        mx_, my_, mz_ = (sum(V[i][k] for i in f) / 3 for k in range(3))
        sx = mx_ if mz_ >= 0 else -mx_  # back half mirrors the front, so the photo wraps without a seam at the limb
        k = 0.9  # stay inside the limb
        sx, sy = cx + sx * R * k, cy + my_ * R * k
        if rock:
            px_s = sum(out_v[i][0] for i in f) / 3
            py_s = sum(out_v[i][1] for i in f) / 3
            sx, sy = cx + (px_s if mz_ >= 0 else -px_s) * R * k, cy + py_s * R * k
        r, g, b = colour(px, sx, sy, mean)
        cols.append(f"{r:02x}{g:02x}{b:02x}7")
    m = {"k": kind, "m": "rock" if rock else "globe", "v": [round(c, 3) for v in out_v for c in v], "f": [i for f in F for i in f], "c": "".join(cols)}
    if ringed:  # rings: an annulus in the equatorial plane; the whole model shrinks so the rings fit the card
        sc = 0.46
        m["v"] = [round(c * sc, 3) for c in m["v"]]
        n0 = len(out_v)
        seg, r1, r2 = 48, 1.25 * sc, 2.15 * sc
        for k in range(seg):
            a = k / seg * math.tau
            m["v"] += [round(math.cos(a) * r1, 3), 0, round(math.sin(a) * r1, 3), round(math.cos(a) * r2, 3), 0, round(math.sin(a) * r2, 3)]
        for k in range(seg):
            i0, o0, i1, o1 = n0 + 2 * k, n0 + 2 * k + 1, n0 + 2 * ((k + 1) % seg), n0 + 2 * ((k + 1) % seg) + 1
            m["f"] += [i0, o0, o1, i0, o1, i1]
            m["c"] += "d8c3965" * 2
        m["tilt"] = 26
    return m


def relief(name):
    """Pillars of Creation: a height field from brightness, so the columns stand out of the cloud"""
    im = load(name, "deep")
    px = im.load()
    lumi = im.convert("L").filter(ImageFilter.GaussianBlur(2))
    cut = sorted(lumi.getdata())[int(SIZE * SIZE * 0.5)]  # the pillars are the brighter half of the frame
    lum = lumi.load()
    n = 26
    V, F, C = [], [], []
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = i / n * (SIZE - 1), j / n * (SIZE - 1)
            V += [round(i / n * 2 - 1, 3), round(j / n * 2 - 1, 3), round(lum[int(x), int(y)] / 255 * 0.55, 3)]
    for j in range(n):
        for i in range(n):
            a, b, c, d = j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i, (j + 1) * (n + 1) + i + 1
            for tri in ((a, b, d), (a, d, c)):
                xs = sum((k % (n + 1)) for k in tri) / 3 / n * (SIZE - 1)
                ys = sum((k // (n + 1)) for k in tri) / 3 / n * (SIZE - 1)
                r, g, bb = colour(px, xs, ys)
                l = lum[int(xs), int(ys)]
                if l < cut:  # dark sky between the pillars: leave it out, so the model keeps their outline
                    continue
                al = min(9, round(3 + (l - cut) / max(1, 255 - cut) * 8))
                F += list(tri)
                C.append(f"{r:02x}{g:02x}{bb:02x}{al}")
    return {"k": "deep", "m": "relief", "v": V, "f": F, "c": "".join(C)}


def wash(name, kind):
    """Watercolour: soft, heavily overlapping blobs of the photo's colours over its bright region.
    Each blob: x, y (-1..1), radius, colour. Bigger blobs where the nebula is broad, smaller where it has detail."""
    im = load(name, kind)
    px = im.load()
    lumi = im.convert("L").filter(ImageFilter.GaussianBlur(3))
    lum = lumi.load()
    grad = im.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(2)).load()
    v = sorted(lumi.getdata())
    floor = 40 if kind == "comet" else max(30, v[int(len(v) * (0.62 if name in FRAME_FILL else 0.5))])
    rnd = random.Random(name)
    blobs, tries = [], 0
    n = 34 if kind == "comet" else 70
    while len(blobs) < n * 4 and tries < 30000:  # 4 values per blob
        tries += 1
        x, y = rnd.uniform(0, SIZE - 1), rnd.uniform(0, SIZE - 1)
        l = lum[int(x), int(y)]
        if l <= floor or rnd.random() > (l - floor) / (255 - floor) + 0.15:
            continue
        detail = min(1.0, grad[int(x), int(y)] / 50)
        r = (0.16 + 0.22 * (1 - detail)) * rnd.uniform(0.7, 1.25)  # in -1..1 units
        cr, cg, cb = colour(px, x, y)
        strength = min(9, round(2 + (l - floor) / (255 - floor) * 8))
        blobs += [round(x / (SIZE - 1) * 2 - 1, 3), round(y / (SIZE - 1) * 2 - 1, 3), round(r, 3), f"{cr:02x}{cg:02x}{cb:02x}{strength}"]
    return {"k": "deep" if kind == "deep" else kind, "m": "wash", "b": blobs}


def flat(name, kind):
    """2D mesh as 3D data with z = 0, in the same -1..1 box"""
    m = mesh(name, kind)
    v = []
    for i in range(0, len(m["p"]), 2):
        v += [round(m["p"][i] / 50 - 1, 3), round(m["p"][i + 1] / 50 - 1, 3), 0]
    return {"k": m["k"], "m": "flat", "v": v, "f": m["t"], "c": m["c"]}


out = {}
for b in bodies:
    nm, kd = b["name"], b["kind"]
    if nm == "Pillars of Creation":
        out[b["img"]] = relief(nm)
    elif kd in ("small", "planet") or nm in GLOBE_STARS:
        out[b["img"]] = solid(nm, kd if nm not in GLOBE_STARS else "planet")
    else:  # nebulae, comet tails, star fields
        out[b["img"]] = wash(nm, kd)
    o = out[b["img"]]
    print(nm, o["m"], len(o["c"]) // 7 if "c" in o else len(o["b"]) // 4, "faces/blobs")
(ROOT / "public" / "sky" / "meshes.json").write_text(json.dumps(out, separators=(",", ":")))
print((ROOT / "public" / "sky" / "meshes.json").stat().st_size // 1024, "KB")
