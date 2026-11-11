"""Cut each reference photo out (rembg), trace its silhouette, and fit it into a 100x100 frame.
Writes, per fish:
  frame/<slug>.png    the cutout on white, 500x500 = the 100x100 frame (1 unit = 5 px), head on the left
  trace/<slug>.svg    the silhouette outline as one smooth path in that frame
Usage: trace.py <work dir> [slug ...]    flips.json in <work dir> lists slugs whose head faces right in the photo."""
import json, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image
from rembg import new_session, remove

W = Path(sys.argv[1])
meta = json.loads((W / "meta.json").read_text())
flips = set(json.loads((W / "flips.json").read_text())) if (W / "flips.json").exists() else set()
only = set(sys.argv[2:])
crops = json.loads((W / "crops.json").read_text()) if (W / "crops.json").exists() else {}
session = new_session("isnet-general-use")
for d in ("cut", "frame", "trace"):
    (W / d).mkdir(exist_ok=True)
M, PX = 6, 5  # frame margin (units), px per unit


def smooth_path(pts):
    """closed Catmull-Rom spline through pts -> SVG cubic path"""
    n, out = len(pts), [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        out.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return "".join(out) + "Z"


for slug, m in meta.items():
    if not m.get("file") or (only and slug not in only):
        continue
    src = W / "raw" / f"{slug}.{m['ext']}"
    cut_p = W / "cut" / f"{slug}.png"
    if not cut_p.exists() or only:
        im = Image.open(src).convert("RGB")
        crop = crops.get(slug)
        if crop:  # crop to the fish first: [x0, y0, x1, y1] as fractions, optional "grabcut" for camouflaged fish
            w0, h0 = im.size
            im = im.crop((int(crop[0] * w0), int(crop[1] * h0), int(crop[2] * w0), int(crop[3] * h0)))
        if crop and len(crop) > 4 and crop[4] == "grabcut":
            arr = np.array(im)[:, :, ::-1].copy()
            gm = np.zeros(arr.shape[:2], np.uint8)
            mh, mw = arr.shape[0] // 30, arr.shape[1] // 30
            cv2.grabCut(arr, gm, (mw, mh, arr.shape[1] - 2 * mw, arr.shape[0] - 2 * mh), np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_RECT)
            alpha = np.where((gm == 1) | (gm == 3), 255, 0).astype(np.uint8)
            Image.fromarray(np.dstack([np.array(im), alpha])).save(cut_p)
        else:
            alpha = np.array(remove(im, session=session))[:, :, 3]
            if crop and len(crop) > 4 and crop[4] == "merge":  # pale bands read as background: close the gaps, fill holes
                k = max(alpha.shape) // 12
                alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
                cs, _ = cv2.findContours((alpha > 128).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                alpha = np.zeros_like(alpha); cv2.drawContours(alpha, cs, -1, 255, -1)
            Image.fromarray(np.dstack([np.array(im), alpha])).save(cut_p)
    rgba = Image.open(cut_p)
    if slug in flips:
        rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)
    a = np.array(rgba)[:, :, 3]
    _, mask = cv2.threshold(a, 128, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    s = (100 - 2 * M) / max(w, h)
    ox, oy = (100 - w * s) / 2 - x * s, (100 - h * s) / 2 - y * s
    approx = cv2.approxPolyDP(c, 0.003 * cv2.arcLength(c, True), True)[:, 0, :].astype(float)
    pts = approx * s + [ox, oy]
    d = smooth_path(pts)
    (W / "trace" / f"{slug}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="500" height="500">'
        f'<rect width="100" height="100" fill="#fff"/><path d="{d}" fill="none" stroke="#000" stroke-width=".6"/></svg>\n')
    # the cutout placed exactly in the frame, on white
    big = rgba.crop((x, y, x + w, y + h)).resize((max(1, round(w * s * PX)), max(1, round(h * s * PX))), Image.LANCZOS)
    frame = Image.new("RGBA", (100 * PX, 100 * PX), "white")
    frame.alpha_composite(big, (round((x * s + ox) * PX), round((y * s + oy) * PX)))
    frame.convert("RGB").save(W / "frame" / f"{slug}.png")
    print(slug, len(pts), "points", flush=True)
