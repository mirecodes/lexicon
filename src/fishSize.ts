/* Typical adult length (cm) of each fish on the Japanese day cards, so small fish are drawn small.
   Kept apart from the generated src/fish.ts; keyed by its img. Manta: disc width. */
export const FISH_CM: Record<string, number> = {
  // N5 tropical and aquarium fish
  "ocellaris-clownfish.webp": 8, "blue-tang.webp": 25, "moorish-idol.webp": 18, "mandarinfish.webp": 6, "royal-gramma.webp": 7,
  "siamese-fighting-fish.webp": 6, "neon-tetra.webp": 3.5, "guppy.webp": 4, "discus-fish.webp": 15, "pterophyllum-scalare.webp": 15,
  "yellow-tang.webp": 18, "emperor-angelfish.webp": 35, "red-lionfish.webp": 35, "copperband-butterflyfish.webp": 18,
  // N4 fish of Korea
  "chub-mackerel.webp": 40, "largehead-hairtail.webp": 120, "small-yellow-croaker.webp": 25, "alaska-pollock.webp": 50,
  "olive-flounder.webp": 60, "korean-rockfish.webp": 35, "red-seabream.webp": 50, "flathead-grey-mullet.webp": 50,
  "ayu-sweetfish.webp": 20, "siniperca-scherzeri.webp": 30, "coreoleuciscus-splendidus.webp": 12, "common-carp.webp": 60,
  "amur-catfish.webp": 50,
  // N3 large species
  "atlantic-bluefin-tuna.webp": 250, "yellowfin-tuna.webp": 150, "swordfish.webp": 300, "atlantic-blue-marlin.webp": 350,
  "sailfish.webp": 300, "whale-shark.webp": 1000, "great-white-shark.webp": 450, "giant-oceanic-manta-ray.webp": 500,
  "ocean-sunfish.webp": 180, "giant-grouper.webp": 200, "humphead-wrasse.webp": 150, "mahi-mahi.webp": 100,
  "giant-trevally.webp": 120, "arapaima.webp": 250, "beluga-sturgeon.webp": 400, "great-hammerhead.webp": 400, "giant-oarfish.webp": 800,
};

/** share of the card a fish takes: log scale, 3.5 cm neon tetra about 42%, 10 m whale shark 100% */
export function fishScale(img: string) {
  const cm = FISH_CM[img];
  if (!cm) return 1;
  const t = (Math.log(cm) - Math.log(3.5)) / (Math.log(1000) - Math.log(3.5));
  return +(0.42 + 0.58 * Math.min(1, Math.max(0, t))).toFixed(3);
}
