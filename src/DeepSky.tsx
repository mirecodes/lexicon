/* Colourful deep-sky objects (nebulae, clusters, galaxies) behind the German day cards.
   Each is drawn procedurally from its type and a seed, so the figures are evocative, not photographic. */
import { useId, type ReactNode } from "react";

type Kind = "emission" | "reflection" | "planetary" | "remnant" | "open" | "globular" | "galaxy";
export interface DeepSkyObject { name: string; kind: Kind; hue?: number; tilt?: number }

const O = (name: string, kind: Kind, extra: Partial<DeepSkyObject> = {}): DeepSkyObject => ({ name, kind, ...extra });

// real objects; hue tints nebula gas, tilt squashes a galaxy (1 = face-on, .2 = edge-on)
const BY_KIND: DeepSkyObject[][] = [
  [O("Orion Nebula", "emission", { hue: 340 }), O("Lagoon Nebula", "emission", { hue: 350 }), O("Trifid Nebula", "emission", { hue: 320 }),
   O("Eagle Nebula", "emission", { hue: 25 }), O("Omega Nebula", "emission", { hue: 335 }), O("North America Nebula", "emission", { hue: 355 }),
   O("Rosette Nebula", "emission", { hue: 345 }), O("Heart Nebula", "emission", { hue: 330 }), O("Soul Nebula", "emission", { hue: 0 }),
   O("Carina Nebula", "emission", { hue: 20 }), O("Horsehead Nebula", "emission", { hue: 350 }), O("Tarantula Nebula", "emission", { hue: 315 }),
   O("Cocoon Nebula", "emission", { hue: 325 }), O("Crescent Nebula", "emission", { hue: 10 }), O("Pacman Nebula", "emission", { hue: 340 }),
   O("Seagull Nebula", "emission", { hue: 0 })],
  [O("Messier 78", "reflection", { hue: 210 }), O("Witch Head Nebula", "reflection", { hue: 220 }), O("Iris Nebula", "reflection", { hue: 200 })],
  [O("Ring Nebula", "planetary", { hue: 180 }), O("Dumbbell Nebula", "planetary", { hue: 160 }), O("Helix Nebula", "planetary", { hue: 190 }),
   O("Cat's Eye Nebula", "planetary", { hue: 170 }), O("Owl Nebula", "planetary", { hue: 150 }), O("Eskimo Nebula", "planetary", { hue: 200 }),
   O("Saturn Nebula", "planetary", { hue: 185 }), O("Southern Ring Nebula", "planetary", { hue: 175 })],
  [O("Crab Nebula", "remnant", { hue: 25 }), O("Veil Nebula", "remnant", { hue: 190 }), O("Cassiopeia A", "remnant", { hue: 280 }),
   O("Spaghetti Nebula", "remnant", { hue: 0 })],
  [O("Pleiades", "open", { hue: 215 }), O("Beehive Cluster", "open", { hue: 45 }), O("Double Cluster", "open", { hue: 220 }),
   O("Ptolemy Cluster", "open", { hue: 200 }), O("Butterfly Cluster", "open", { hue: 30 }), O("Wild Duck Cluster", "open", { hue: 210 }),
   O("Jewel Box", "open", { hue: 0 }), O("Messier 35", "open", { hue: 200 }), O("Messier 37", "open", { hue: 40 }), O("Hyades", "open", { hue: 30 })],
  [O("Hercules Cluster", "globular"), O("Omega Centauri", "globular"), O("47 Tucanae", "globular"), O("Messier 22", "globular"),
   O("Messier 3", "globular"), O("Messier 5", "globular"), O("Messier 15", "globular"), O("Messier 4", "globular"), O("Messier 92", "globular")],
  [O("Andromeda Galaxy", "galaxy", { tilt: .38 }), O("Triangulum Galaxy", "galaxy", { tilt: .7 }), O("Whirlpool Galaxy", "galaxy", { tilt: .95 }),
   O("Pinwheel Galaxy", "galaxy", { tilt: 1 }), O("Sombrero Galaxy", "galaxy", { tilt: .22 }), O("Bode's Galaxy", "galaxy", { tilt: .55 }),
   O("Southern Pinwheel", "galaxy", { tilt: .9 }), O("NGC 1300", "galaxy", { tilt: .75 }), O("Black Eye Galaxy", "galaxy", { tilt: .5 }),
   O("Cigar Galaxy", "galaxy", { tilt: .2 }), O("Large Magellanic Cloud", "galaxy", { tilt: .65 }), O("Phantom Galaxy", "galaxy", { tilt: 1 }),
   O("Needle Galaxy", "galaxy", { tilt: .15 })],
];

/** round-robin over kinds so neighbouring days look different */
export const DEEP_SKY: DeepSkyObject[] = (() => {
  const queues = BY_KIND.map((k) => [...k]), out: DeepSkyObject[] = [];
  while (queues.some((q) => q.length)) for (const q of queues) if (q.length) out.push(q.shift()!);
  return out;
})();

function rng(seed: string) {
  let h = 1779033703 ^ seed.length;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 3432918353), (h = (h << 13) | (h >>> 19));
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return ((h ^= h >>> 16) >>> 0) / 4294967296;
  };
}

const hsl = (h: number, s: number, l: number, a = 1) => `hsla(${((h % 360) + 360) % 360} ${s}% ${l}% / ${a})`;

export function DeepSky({ o }: { o: DeepSkyObject }) {
  const id = useId().replace(/:/g, "");
  const r = rng(o.name), hue = o.hue ?? 45;
  const blur = `url(#${id}b)`, soft = `url(#${id}s)`;
  const stars = (n: number, spread: number, size: number, color: (i: number) => string, cx = 50, cy = 50) =>
    Array.from({ length: n }, (_, i) => {
      const a = r() * Math.PI * 2, d = spread * Math.sqrt(r()) * (0.4 + 0.6 * r());
      return <circle key={i} className="tw" cx={cx + Math.cos(a) * d} cy={cy + Math.sin(a) * d} r={size * (0.4 + r())} fill={color(i)} style={{ animationDelay: `${(i * 0.31) % 2}s` }} />;
    });
  const field = stars(10, 46, 0.7, () => "#fff"); // background stars, every kind

  let body;
  switch (o.kind) {
    case "emission":
    case "reflection": {
      const sat = o.kind === "emission" ? 85 : 75;
      body = (
        <g filter={blur}>
          {Array.from({ length: 7 }, (_, i) => (
            <ellipse key={i} cx={50 + (r() - .5) * 40} cy={50 + (r() - .5) * 36} rx={10 + r() * 16} ry={7 + r() * 12}
              transform={`rotate(${r() * 180} 50 50)`} fill={hsl(hue + (r() - .5) * 60, sat, 45 + r() * 20, .55)} />
          ))}
          <ellipse cx={50 + (r() - .5) * 10} cy={50 + (r() - .5) * 10} rx="9" ry="7" fill={hsl(hue + 30, 90, 75, .7)} />
          {o.kind === "emission" && <ellipse cx={45 + r() * 10} cy={40 + r() * 20} rx="5" ry="16" transform={`rotate(${r() * 180} 50 50)`} fill="#000" opacity=".45" />}
        </g>
      );
      break;
    }
    case "planetary": {
      const rx = 17 + r() * 6, ry = rx * (0.65 + r() * 0.35), rot = r() * 180;
      body = (
        <g transform={`rotate(${rot} 50 50)`}>
          <ellipse cx="50" cy="50" rx={rx + 7} ry={ry + 7} fill={hsl(hue + 160, 85, 55, .55)} filter={blur} />
          <ellipse cx="50" cy="50" rx={rx} ry={ry} fill="none" stroke={hsl(hue + 150, 95, 62)} strokeWidth="7" filter={soft} />
          <ellipse cx="50" cy="50" rx={rx - 4} ry={ry - 4} fill={hsl(hue, 85, 65, .7)} filter={soft} />
          <circle cx="50" cy="50" r="1.4" fill="#fff" />
        </g>
      );
      break;
    }
    case "remnant": {
      body = (
        <g filter={soft} fill="none" strokeLinecap="round">
          {Array.from({ length: 9 }, (_, i) => {
            const a0 = r() * Math.PI * 2, a1 = a0 + 0.6 + r(), rad = 18 + r() * 16;
            const p = (a: number, k = 1) => `${50 + Math.cos(a) * rad * k} ${50 + Math.sin(a) * rad * k}`;
            return <path key={i} d={`M${p(a0)} Q${p((a0 + a1) / 2, 1.25)} ${p(a1)}`} stroke={hsl(hue + (i % 2 ? 0 : 160), 90, 60, .8)} strokeWidth={1.2 + r() * 1.6} />;
          })}
          <circle cx="50" cy="50" r="10" fill={hsl(hue + 200, 70, 60, .25)} filter={blur} />
        </g>
      );
      break;
    }
    case "open":
      body = (
        <>
          <circle cx="50" cy="50" r="28" fill={hsl(hue, 85, 60, .38)} filter={blur} />
          {stars(26, 32, 1.8, (i) => (i % 5 ? hsl(hue, 90, 80) : "#fff"))}
        </>
      );
      break;
    case "globular":
      body = (
        <>
          <circle cx="50" cy="50" r="22" fill={`url(#${id}g)`} />
          {stars(60, 24, 0.75, (i) => (i % 4 ? "hsl(45 90% 80%)" : "#fff"))}
        </>
      );
      break;
    case "galaxy": {
      const tilt = o.tilt ?? 0.7, rot = r() * 180, arms: ReactNode[] = [];
      for (let arm = 0; arm < 2; arm++)
        for (let i = 0; i < 26; i++) {
          const t = i / 26, a = arm * Math.PI + t * 3.4, d = 4 + t * 34;
          arms.push(<circle key={`${arm}-${i}`} cx={50 + Math.cos(a) * d + (r() - .5) * 4} cy={50 + Math.sin(a) * d + (r() - .5) * 4}
            r={2.6 - t * 1.6} fill={i % 6 === 3 ? "hsl(330 85% 70%)" : "hsl(215 85% 78%)"} opacity={0.75 - t * 0.35} />);
        }
      body = (
        <g transform={`rotate(${rot} 50 50) translate(50 50) scale(1 ${tilt}) translate(-50 -50)`}>
          <ellipse cx="50" cy="50" rx="36" ry="36" fill="hsl(220 80% 65% / .35)" filter={blur} />
          <g filter={soft}>{arms}</g>
          <ellipse cx="50" cy="50" rx="11" ry="11" fill={`url(#${id}g)`} />
          {tilt < 0.3 && <rect x="12" y="48.5" width="76" height="3" fill="#000" opacity=".5" filter={soft} />}
        </g>
      );
      break;
    }
  }

  return (
    <svg className="deep" viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <filter id={`${id}b`} x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" /></filter>
        <filter id={`${id}s`} x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.2" /></filter>
        <radialGradient id={`${id}g`}>
          <stop offset="0" stopColor="#fff8e1" /><stop offset=".35" stopColor="hsl(42 95% 72%)" stopOpacity=".8" />
          <stop offset="1" stopColor="hsl(30 90% 55%)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <title>{o.name}</title>
      {field}
      {body}
    </svg>
  );
}
