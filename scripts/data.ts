/* Check the chapter files in en/ and de/, then bundle them into public/data/ for the app.
   Usage: node scripts/data.ts          check and bundle
          node scripts/data.ts --check  check only
   Exits 1 if any entry is invalid. */
import { mkdirSync, readFileSync, readdirSync, writeFileSync, copyFileSync } from "node:fs";
import { join } from "node:path";
import assert from "node:assert/strict";
import type { Bundle, DeEntry, DeWord, EnEntry, EnWord, Parts } from "../src/types.ts";

const ROOT = join(import.meta.dirname, "..");
const OUT = join(ROOT, "public", "data");
const read = <T>(p: string): T => JSON.parse(readFileSync(p, "utf8"));
const cmp = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0); // code-point order, like Python
const sortedLike = (xs: string[], by: (a: string, b: string) => number) => xs.every((x, i) => !i || by(xs[i - 1], x) <= 0);
const pick = <T extends object, K extends keyof T>(e: T, keys: K[]) =>
  Object.fromEntries(keys.filter((k) => k in e).map((k) => [k, e[k]])) as Pick<T, K>;
/** chapter files under dir/<sub>/ whose folder name matches `sub` */
const chapters = (dir: string, sub: RegExp) =>
  readdirSync(dir).filter((d) => sub.test(d)).sort().flatMap((d) =>
    readdirSync(join(dir, d)).filter((f) => f.endsWith(".json")).sort().map((f) => ({ folder: d, stem: f.slice(0, -5), path: join(dir, d, f) })));

/* ---------- English ---------- */
const LISTS = new Set(["GregMat", "PowerScore", "Magoosh", "VocabCom", "Manhattan"]);
const EN_SOURCES = new Set(["oewn", "wiktionary", "generated"]);

export const enChapter = (word: string) => word.replace(/[^a-z]/g, "").slice(0, 2);

/** List agreement (80%) plus closeness to the GRE-core frequency, Zipf 2.5 (20%). Rounds half to even, like Python. */
export function score(nLists: number, zipf: number) {
  const fit = Math.max(0, 1 - Math.abs(zipf - 2.5) / 2);
  const x = 100 * (0.8 * nLists / 5 + 0.2 * fit), r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 ? r - 1 : r;
}

function checkEn(): { errs: string[]; words: EnEntry[] } {
  const dir = join(ROOT, "en"), roots = read<Parts>(join(dir, "roots.json"));
  const errs: string[] = [], seen = new Set<string>(), all: EnEntry[] = [];
  for (const { folder, stem, path } of chapters(dir, /^[a-z]$/)) {
    if (folder !== stem[0]) errs.push(`${path}: chapter in wrong folder`);
    const entries = read<EnEntry[]>(path);
    if (!sortedLike(entries.map((e) => e.word ?? ""), cmp)) errs.push(`${stem}: not alphabetical`);
    for (const e of entries) {
      const bad = (m: string) => errs.push(`${stem}/${e.word ?? "?"}: ${m}`);
      if (seen.has(e.word)) bad("duplicate");
      seen.add(e.word);
      for (const p of e.parts ?? []) if (!(p in roots)) bad(`part '${p}' missing from roots.json`);
      if (e.origin != null && (!e.origin.ko || !EN_SOURCES.has(e.origin.source))) bad("bad origin");
      if (enChapter(e.word ?? "") !== stem) bad("wrong chapter");
      if (!e.lists?.length || !e.lists.every((l) => LISTS.has(l)) || !sortedLike(e.lists, cmp)) bad("bad lists");
      else if (e.score !== score(e.lists.length, e.zipf ?? -9)) bad("score does not match lists/zipf");
      if (!e.senses?.length) bad("no senses");
      (e.senses ?? []).forEach((s, i) => {
        if (!s.pos || !s.en || !EN_SOURCES.has(s.source!)) bad(`sense ${i + 1}: missing pos/en/source`);
        if (e.curated && !s.ko) bad(`sense ${i + 1}: curated entry without ko`);
        if ((s.examples ?? []).some((x) => !EN_SOURCES.has(x.source!) || !x.text)) bad(`sense ${i + 1}: bad example`);
      });
      all.push(e);
    }
  }
  return { errs, words: all };
}

/** most important words first */
function bundleEn(entries: EnEntry[]): Bundle<EnWord> {
  const words = [...entries].sort((a, b) => b.score - a.score || cmp(a.word, b.word))
    .map((e) => pick(e, ["word", "score", "lists", "senses", "parts", "origin"]));
  return { words, parts: read<Parts>(join(ROOT, "en", "roots.json")) };
}

/* ---------- German ---------- */
const DE_SOURCES = new Set(["wiktionary", "generated"]);
const GENDERS = new Set(["m", "f", "n"]);
const PART_TYPES = new Set(["sep", "insep", "stem", "suffix"]);

// ponytail: covers German (ß → ss); Python's full casefold also folds other scripts, which the data never uses
const casefold = (s: string) => s.toLowerCase().replace(/ß/g, "ss");
const deKey = (a: string, b: string) => cmp(casefold(a), casefold(b)) || cmp(a, b);

/** letter file for a lemma: first letter with umlauts folded (Äpfel -> a) */
export const deChapter = (word: string) =>
  casefold(word).normalize("NFKD").replace(/\p{M}/gu, "").replace(/[^a-z]/g, "").slice(0, 1) || "_";

function checkDe(): { errs: string[]; words: DeEntry[] } {
  const dir = join(ROOT, "de"), parts = read<Parts>(join(dir, "parts.json"));
  const errs: string[] = [], seen = new Set<string>(), all: DeEntry[] = [];
  for (const { folder: level, stem: letter, path } of chapters(dir, /^(a1|a2|b1)$/)) {
    const entries = read<DeEntry[]>(path);
    if (!sortedLike(entries.map((e) => e.word ?? ""), deKey)) errs.push(`${level}/${letter}: not alphabetical`);
    for (const e of entries) {
      const w = e.word ?? "?", bad = (m: string) => errs.push(`${level}/${letter}/${w}: ${m}`);
      if (seen.has(e.word)) errs.push(`${e.word}: duplicate`);
      seen.add(e.word);
      if (e.level !== level || deChapter(w) !== letter) bad("wrong file");
      const g = e.grammar ?? ({} as NonNullable<DeEntry["grammar"]>);
      if (g.type !== e.pos) bad("grammar.type must equal pos");
      if (e.pos === "noun" && !(g.gender?.length && g.gender.every((x) => GENDERS.has(x)))) bad("noun without gender");
      if (g.separable && !(g.prefix && w.startsWith(g.prefix))) bad("separable verb needs a matching prefix");
      for (const p of e.parts ?? []) if (!(p in parts) || !PART_TYPES.has(p.split("|")[1])) bad(`unknown part ${p}`);
      if (!e.senses?.length) bad("no senses");
      (e.senses ?? []).forEach((s, i) => {
        if (!s.en || !s.ko || !DE_SOURCES.has(s.source!)) bad(`sense ${i + 1}: missing en/ko/source`);
        if ((s.examples ?? []).some((x) => !x.text || !x.ko)) bad(`sense ${i + 1}: bad example`);
      });
      all.push(e);
    }
  }
  return { errs, words: all };
}

/** by level, then most frequent first */
function bundleDe(entries: DeEntry[]): Bundle<DeWord> {
  const words = [...entries].sort((a, b) => cmp(a.level, b.level) || b.zipf - a.zipf || cmp(casefold(a.word), casefold(b.word)))
    .map((e) => pick(e, ["word", "level", "pos", "grammar", "parts", "senses"]));
  return { words, parts: read<Parts>(join(ROOT, "de", "parts.json")) };
}

/* ---------- main ---------- */
assert.equal(enChapter("status quo"), "st");
assert.equal(enChapter("per se"), "pe");
assert.equal(score(5, 2.5), 100);
assert.equal(score(1, 5.5), 16);
assert.equal(deChapter("Äpfel"), "a");
assert.equal(deChapter("anrufen"), "a");
assert.equal(deChapter("Übung"), "u");

const en = checkEn(), de = checkDe();
let failed = false;
for (const [name, r] of [["en", en], ["de", de]] as const) {
  console.log(r.errs.slice(0, 200).join("\n") || "", `${name}: ${r.words.length} entries, ${r.errs.length} errors`);
  failed ||= r.errs.length > 0;
}
if (failed) process.exit(1);

if (!process.argv.includes("--check")) {
  mkdirSync(OUT, { recursive: true });
  const write = (f: string, data: unknown) => {
    writeFileSync(join(OUT, f), JSON.stringify(data));
    console.log(`public/data/${f}`);
  };
  write("en.json", bundleEn(en.words));
  write("de.json", bundleDe(de.words));
  copyFileSync(join(ROOT, "en", "synonyms.json"), join(OUT, "en-synonyms.json"));
}
