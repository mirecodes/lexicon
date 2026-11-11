"""Pencil-sketch fish from a cut-out photo, tone carried by fine hatch strokes (no dots, no filled areas):
  - short thin strokes along the body's flow (head to tail), denser where the photo is darker
  - a second, crossing stroke layer only in the darkest parts
  - fin rays: strokes from each fin's outer edge back to its base on the body
  - a smoothed outline and a few clean detail lines (eye, gill cover, lateral line) from the photo
Renders at 2x and downsamples. Writes W/sk/<slug>.png (ink on transparent, head left) and W/sk/<slug>_prev.png.
Usage: sketch.py <W> [slug ...]   per-fish tweaks in W/sk.json"""
import json, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image

W = Path(sys.argv[1])
meta = json.loads((W / "meta.json").read_text())
flips = set(json.loads((W / "flips.json").read_text()))
cfg = json.loads((W / "sk.json").read_text()) if (W / "sk.json").exists() else {}
(W / "sk").mkdir(exist_ok=True)
OUT = 480
L = OUT * 2
SH = 4  # cv2 sub-pixel shift


def seg(img, p, q, thick=1):
    cv2.line(img, (int(p[0] * 16), int(p[1] * 16)), (int(q[0] * 16), int(q[1] * 16)), 255, thick, lineType=cv2.LINE_AA, shift=SH)


def render(slug):
    c = cfg.get(slug, {})
    rng = np.random.default_rng(5)
    rgba = Image.open(W / "cut" / f"{slug}.png")
    if slug in flips:
        rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)
    a = np.array(rgba)
    m = (a[:, :, 3] > 128).astype(np.uint8)
    _, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    m = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8) * 255
    x, y, w, h = cv2.boundingRect(m)
    pad = 16
    s = (L - 2 * pad) / max(w, h)
    rgb = cv2.resize(a[y:y + h, x:x + w, :3], None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    m = cv2.resize(m[y:y + h, x:x + w], (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
    rgb = cv2.copyMakeBorder(rgb, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    m = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    m = (cv2.GaussianBlur(m, (9, 9), 0) > 128).astype(np.uint8)
    sh = m.shape
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255

    # tone 0..1 (1 = darkest)
    tone = 1 - cv2.GaussianBlur(gray, (0, 0), 3)
    v = tone[m > 0]
    lo, hi = np.percentile(v, c.get("lo", 10)), np.percentile(v, 98)
    tone = np.clip((tone - lo) / max(hi - lo, 1e-3), 0, 1) ** c.get("gamma", 1.4)

    # body vs fins: the body is what survives a large opening; fins are the rest
    k = max(9, int(min(sh) * c.get("bodyk", 0.11)) | 1)
    body = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    _, bl, bs, _ = cv2.connectedComponentsWithStats(body)
    body = (bl == 1 + np.argmax(bs[1:, cv2.CC_STAT_AREA])).astype(np.uint8) if bs.shape[0] > 1 else m.copy()
    fins = (m & (1 - body)).astype(np.uint8)

    # flow direction: along the body, bending with back and belly (iso-lines of the top-bottom position)
    cols = np.where(m.any(0))[0]
    top = np.full(sh[1], np.nan); bot = np.full(sh[1], np.nan)
    for xx_ in cols:
        ys = np.where(body[:, xx_])[0] if body[:, xx_].any() else np.where(m[:, xx_])[0]
        top[xx_], bot[xx_] = ys[0], ys[-1]
    idx = np.arange(sh[1])
    top = np.interp(idx, cols, top[cols]); bot = np.interp(idx, cols, bot[cols])
    top = cv2.GaussianBlur(top.reshape(1, -1), (0, 0), 30).ravel(); bot = cv2.GaussianBlur(bot.reshape(1, -1), (0, 0), 30).ravel()
    yy, xx = np.mgrid[0:sh[0], 0:sh[1]].astype(np.float32)
    vv = ((yy - top[None, :]) / np.maximum(bot - top, 8)[None, :]).astype(np.float32)
    gx = cv2.Sobel(vv, cv2.CV_32F, 1, 0, ksize=5); gy = cv2.Sobel(vv, cv2.CV_32F, 0, 1, ksize=5)
    ang = np.arctan2(gy, gx) + np.pi / 2  # tangent of the iso-line

    ink = np.zeros(sh, np.uint8)
    # hatch strokes: one candidate per jittered cell, kept with probability = tone
    for layer, (cell, th, turn, ln) in enumerate([(c.get("cell", 9.0), 0.05, 0.0, (22, 44)), (12.0, 0.7, np.deg2rad(35), (14, 26))]):
        gyy, gxx = np.mgrid[0:sh[0]:cell, 0:sh[1]:cell]
        px = (gxx + rng.uniform(0, cell, gxx.shape)).ravel(); py = (gyy + rng.uniform(0, cell, gyy.shape)).ravel()
        ok = (px < sh[1] - 1) & (py < sh[0] - 1); px, py = px[ok], py[ok]
        ix, iy = px.astype(int), py.astype(int)
        p = np.clip((tone[iy, ix] - th) / (1 - th), 0, 1)
        keep = (body[iy, ix] > 0) & (rng.uniform(0, 1, len(px)) < p * c.get("density", 0.78))
        for X, Y in zip(px[keep], py[keep]):
            t = ang[int(Y), int(X)] + turn + rng.normal(0, 0.04)
            half = rng.uniform(*ln) / 2
            d = np.array([np.cos(t), np.sin(t)]) * half
            seg(ink, (X - d[0], Y - d[1]), (X + d[0], Y + d[1]), 1)
    ink = cv2.bitwise_and(ink, ink, mask=body * 255)

    # fin rays: from points along each fin's outer edge to the nearest body edge point
    fin_ink = np.zeros(sh, np.uint8)
    bcs, _ = cv2.findContours(body, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    bpts = np.vstack([b[:, 0] for b in bcs]).astype(np.float32)
    n, fl, fs, _ = cv2.connectedComponentsWithStats(fins)
    for i in range(1, n):
        if fs[i, cv2.CC_STAT_AREA] < 300:
            continue
        fm = (fl == i).astype(np.uint8)
        fc, _ = cv2.findContours(fm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        edge = fc[0][:, 0].astype(np.float32)
        dist_body = np.min(np.linalg.norm(edge[:, None, :] - bpts[None, ::4, :], axis=2), axis=1)
        outer = edge[dist_body > 6]
        step = max(1, int(c.get("rays", 15)))
        for q in outer[::step]:
            j = np.argmin(np.linalg.norm(bpts - q, axis=1))
            seg(fin_ink, q, bpts[j], 1)
        # a little tone inside the fin too
    fin_ink = cv2.bitwise_and(fin_ink, fin_ink, mask=cv2.dilate(fins, np.ones((3, 3), np.uint8)) * 255)
    ink = np.maximum(ink, (fin_ink.astype(np.float32) * 0.85).astype(np.uint8))

    # detail lines from the photo: only longer clean strokes
    g1 = cv2.GaussianBlur(gray, (0, 0), 1.6)
    g2 = cv2.GaussianBlur(gray, (0, 0), 1.6 * 1.6)
    edge = ((g1 - 0.985 * g2) < c.get("eps", -0.012)).astype(np.uint8)
    edge &= cv2.erode(body, np.ones((9, 9), np.uint8))
    n, lab2, st, _ = cv2.connectedComponentsWithStats(edge, connectivity=8)
    big = np.zeros(n, bool)
    big[1:] = np.maximum(st[1:, cv2.CC_STAT_WIDTH], st[1:, cv2.CC_STAT_HEIGHT]) >= c.get("minlen", 22)
    det = (big[lab2].astype(np.uint8) * 255)
    ink = np.maximum(ink, cv2.GaussianBlur(det, (3, 3), 0))

    # smoothed outline
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    o = max(cs, key=cv2.contourArea)[:, 0].astype(np.float32)
    k1 = 7
    pad_o = np.vstack([o[-k1:], o, o[:k1]])
    ker = np.ones(2 * k1 + 1) / (2 * k1 + 1)
    so = np.stack([np.convolve(pad_o[:, 0], ker, "valid"), np.convolve(pad_o[:, 1], ker, "valid")], 1)
    cv2.polylines(ink, [(so * 16).astype(np.int32)], True, 255, 4, lineType=cv2.LINE_AA, shift=SH)

    small = cv2.resize(ink, (sh[1] // 2, sh[0] // 2), interpolation=cv2.INTER_AREA)
    out = np.zeros((*small.shape, 4), np.uint8); out[:, :, 3] = small
    Image.fromarray(out).save(W / "sk" / f"{slug}.png")
    Image.fromarray(255 - small).save(W / "sk" / f"{slug}_prev.png")
    print(slug, small.shape, flush=True)


for slug in sys.argv[2:] or list(meta):
    render(slug)
