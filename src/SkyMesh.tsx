/* German day cards: each object drawn from its photo (public/sky/meshes.json, generated).
   - globe / rock: a 3D wireframe in the surface's colours (planets, moons, stars, asteroids, comet nuclei)
   - relief: the Pillars of Creation as a height-field mesh
   - wash: nebulae, comet tails and star fields as soft, overlapping watercolour blooms
   Drawn on a canvas: one still frame at rest; while the card is lit (hover/press, or the day is done)
   the 3D ones turn slowly. The grey/colour switch is CSS (.mesh in styles.css). */
import { useEffect, useRef } from "react";

interface Solid { k: string; m: "globe" | "rock" | "relief"; v: number[]; f: number[]; c: string; tilt?: number }
interface Wash { k: string; m: "wash"; b: (number | string)[] }
type Mesh = Solid | Wash;

let meshes: Promise<Record<string, Mesh>> | null = null;
const loadMeshes = () => (meshes ??= fetch("sky/meshes.json").then((r) => r.json()).catch((e) => { meshes = null; throw e; }));

const calm = matchMedia("(prefers-reduced-motion: reduce)");
const TURN_MS = 24000;
const LIGHT = (() => { const l = [-0.5, -0.6, 0.62], n = Math.hypot(...l); return l.map((x) => x / n); })(); // top left, in front
const rgb = (s: string) => [parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16)];

function drawSolid(ctx: CanvasRenderingContext2D, W: number, mesh: Solid, yaw: number) {
  const S = W / 2.15, C = W / 2, { v, f, c, m } = mesh, n = v.length / 3;
  const a = m === "relief" ? Math.sin(yaw) * 0.35 : yaw; // the relief rocks gently instead of turning
  const tilt = ((mesh.tilt ?? (m === "globe" ? 12 : m === "rock" ? 20 : 8)) * Math.PI) / 180;
  const ca = Math.cos(a), sa = Math.sin(a), ct = Math.cos(tilt), st = Math.sin(tilt);
  const P = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const x = v[i * 3], y = v[i * 3 + 1], z = v[i * 3 + 2];
    const x1 = x * ca + z * sa, z1 = -x * sa + z * ca;
    P[i * 3] = C + x1 * S; P[i * 3 + 1] = C + (y * ct - z1 * st) * S; P[i * 3 + 2] = y * st + z1 * ct;
  }
  const ring = mesh.tilt ? 320 : Infinity; // Saturn: faces after the globe's 320 are its two-sided ring
  const faces: [number, number][] = [];
  for (let j = 0; j < f.length / 3; j++) {
    const i0 = f[j * 3] * 3, i1 = f[j * 3 + 1] * 3, i2 = f[j * 3 + 2] * 3;
    const cross = (P[i1] - P[i0]) * (P[i2 + 1] - P[i0 + 1]) - (P[i1 + 1] - P[i0 + 1]) * (P[i2] - P[i0]);
    if (m !== "relief" && cross > 0 && j < ring) continue; // the far side of a solid
    faces.push([j, P[i0 + 2] + P[i1 + 2] + P[i2 + 2]]);
  }
  faces.sort((p, q) => p[1] - q[1]);
  ctx.lineJoin = "round";
  for (const [j] of faces) {
    const i0 = f[j * 3] * 3, i1 = f[j * 3 + 1] * 3, i2 = f[j * 3 + 2] * 3;
    const [r, g, b] = rgb(c.slice(j * 7, j * 7 + 6)), al = Number(c[j * 7 + 6]) / 9;
    // lambert from the rotated triangle, so the wireframe still reads as a lit solid
    const ux = P[i1] - P[i0], uy = P[i1 + 1] - P[i0 + 1], uz = (P[i1 + 2] - P[i0 + 2]) * S;
    const wx = P[i2] - P[i0], wy = P[i2 + 1] - P[i0 + 1], wz = (P[i2 + 2] - P[i0 + 2]) * S;
    let nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx;
    const l = Math.hypot(nx, ny, nz) || 1;
    if (nz < 0) { nx = -nx; ny = -ny; nz = -nz; }
    const lit = Math.max(0, (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / l);
    ctx.beginPath();
    ctx.moveTo(P[i0], P[i0 + 1]); ctx.lineTo(P[i1], P[i1 + 1]); ctx.lineTo(P[i2], P[i2 + 1]); ctx.closePath();
    if (m === "relief") {
      const k = 0.55 + 0.6 * lit;
      ctx.fillStyle = `rgba(${r * k},${g * k},${b * k},${0.16 * al})`;
      ctx.fill();
    }
    ctx.strokeStyle = `rgba(${r},${g},${b},${(0.25 + 0.55 * lit) * (m === "relief" ? al : 1)})`;
    ctx.lineWidth = W / 420;
    ctx.stroke();
  }
}

/** watercolour: each bloom is a wobbly, soft-edged pool of colour; many overlap and bleed into each other */
function drawWash(ctx: CanvasRenderingContext2D, W: number, mesh: Wash, dark: boolean) {
  const C = W / 2, S = W / 2.9, b = mesh.b; // S: kept inside the card so the bleed never meets its edge
  ctx.globalCompositeOperation = dark ? "screen" : "multiply"; // light on a dark card, pigment on a light one
  ctx.filter = `blur(${(W / 70).toFixed(1)}px)`;
  for (let pass = 0; pass < 2; pass++) { // a wide, very pale underwash, then the pools with their pigment rims
    for (let i = 0; i < b.length; i += 4) {
      const x = C + (b[i] as number) * S, y = C + (b[i + 1] as number) * S, rad = (b[i + 2] as number) * S * (pass ? 1 : 1.5);
      const hex = b[i + 3] as string, strength = Number(hex[6]) / 9;
      // pastel: the photo's hue, thinned toward white as watercolour is
      const [r, g, bl] = rgb(hex).map((v) => Math.round(v * 0.6 + 255 * 0.4));
      const alpha = (pass ? 0.075 : 0.03) * (0.5 + strength);
      const seed = i * 12.9898;
      ctx.beginPath();
      for (let k = 0; k <= 22; k++) {
        const ang = (k / 22) * Math.PI * 2;
        const wob = 1 + 0.2 * Math.sin(ang * 3 + seed) + 0.1 * Math.sin(ang * 7 + seed * 1.7);
        const px = x + Math.cos(ang) * rad * wob, py = y + Math.sin(ang) * rad * wob;
        if (k) ctx.lineTo(px, py); else ctx.moveTo(px, py);
      }
      const gr = ctx.createRadialGradient(x, y, 0, x, y, rad * 1.25);
      gr.addColorStop(0, `rgba(${r},${g},${bl},${alpha * 0.7})`);
      gr.addColorStop(0.75, `rgba(${r},${g},${bl},${alpha})`); // pigment gathers toward the edge of a wet pool
      gr.addColorStop(1, `rgba(${r},${g},${bl},0)`);
      ctx.fillStyle = gr;
      ctx.fill();
      if (pass) {
        ctx.strokeStyle = `rgba(${r},${g},${bl},${alpha * 0.9})`;
        ctx.lineWidth = W / 260;
        ctx.stroke();
      }
    }
  }
  ctx.filter = "none";
  ctx.globalCompositeOperation = "source-over";
}

export function SkyMesh({ img, kind, rotate, done }: { img: string; kind: string; rotate?: number; done: boolean }) {
  const cv = useRef<HTMLCanvasElement>(null);
  const lit = useRef(done), resync = useRef(() => {});
  lit.current = done;
  useEffect(() => resync.current(), [done]);

  useEffect(() => {
    const canvas = cv.current!, card = canvas.parentElement!, ctx = canvas.getContext("2d")!;
    let mesh: Mesh | null = null, raf = 0, hot = false, alive = true, yaw = 0.5, t0 = 0;

    const draw = () => {
      if (!mesh) return;
      const s = Math.round(canvas.clientWidth * devicePixelRatio);
      if (s && canvas.width !== s) canvas.width = canvas.height = s;
      const W = canvas.width;
      ctx.clearRect(0, 0, W, W);
      if (mesh.m === "wash") {
        const bg = getComputedStyle(card).backgroundColor.match(/\d+/g)?.map(Number) ?? [0, 0, 0];
        drawWash(ctx, W, mesh, bg[0] + bg[1] + bg[2] < 384);
      } else drawSolid(ctx, W, mesh, yaw);
    };
    const frame = (now: number) => {
      if (!alive) return;
      if (t0) yaw += ((now - t0) / TURN_MS) * Math.PI * 2;
      t0 = now;
      draw();
      raf = requestAnimationFrame(frame);
    };
    const sync = () => {
      const turn = (lit.current || hot) && mesh && mesh.m !== "wash" && !calm.matches;
      if (turn && !raf) { t0 = 0; raf = requestAnimationFrame(frame); }
      if (!turn && raf) { cancelAnimationFrame(raf); raf = 0; }
    };
    resync.current = sync;

    const on = () => { hot = true; sync(); }, off = () => { hot = false; sync(); };
    card.addEventListener("pointerenter", on);
    card.addEventListener("pointerleave", off);
    card.addEventListener("pointerdown", on);
    card.addEventListener("pointercancel", off);
    const ro = new ResizeObserver(() => { if (!raf) draw(); });
    ro.observe(canvas);
    const theme = new MutationObserver(() => { if (!raf) draw(); }); // the wash blends differently on light and dark cards
    theme.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    loadMeshes().then((all) => { if (!alive) return; mesh = all[img] ?? null; draw(); sync(); }, () => {});
    return () => {
      alive = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
      theme.disconnect();
      card.removeEventListener("pointerenter", on);
      card.removeEventListener("pointerleave", off);
      card.removeEventListener("pointerdown", on);
      card.removeEventListener("pointercancel", off);
    };
  }, [img]);

  return <canvas ref={cv} className={`mesh ${kind}${done ? " lit" : ""}`} aria-hidden="true" style={rotate ? { rotate: `${rotate}deg` } : undefined} />;
}
