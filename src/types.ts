/* Shapes of the chapter files in en/ and de/ and of the bundles the app loads. */

export type Source = "oewn" | "wiktionary" | "generated";

export interface Example {
  text: string;
  ko?: string;
  source?: Source;
}

export interface Sense {
  pos?: string;
  en: string;
  ko?: string;
  synonyms?: string[];
  examples?: Example[];
  source?: Source;
  ko_source?: "generated";
}

/* English (GRE) */
export type ListName = "GregMat" | "PowerScore" | "Magoosh" | "VocabCom" | "Manhattan";

export interface EnEntry {
  word: string;
  score: number;
  zipf: number;
  lists: ListName[];
  curated?: boolean;
  parts?: string[];
  origin?: { ko: string; source: Source; ko_source?: "generated" };
  senses: Sense[];
}
export type EnWord = Pick<EnEntry, "word" | "score" | "lists" | "senses" | "parts" | "origin">;

/* German (A1–B1) */
export type Level = "a1" | "a2" | "b1";
export type Gender = "m" | "f" | "n";
export type VerbClass = "weak" | "strong" | "mixed" | "irregular" | "modal";

export interface Grammar {
  type: string;
  gender?: Gender[];
  plural?: string | null;
  genitive?: string | null;
  number?: "pl";
  class?: VerbClass | null;
  reflexive?: boolean;
  present3?: string;
  past?: string;
  pp?: string;
  aux?: "haben" | "sein" | "haben/sein";
  separable?: boolean;
  prefix?: string;
  comparative?: string;
  superlative?: string;
}

export interface DeEntry {
  word: string;
  level: Level;
  zipf: number;
  pos: string;
  grammar?: Grammar;
  grammar_source?: Source;
  parts?: string[];
  senses: Sense[];
}
export type DeWord = Pick<DeEntry, "word" | "level" | "pos" | "grammar" | "parts" | "senses">;

/* word parts: en/roots.json and de/parts.json */
export type PartType = "prefix" | "root" | "suffix" | "sep" | "insep" | "stem";
export interface PartInfo {
  type: PartType;
  ko: string;
  form?: string;
}
export type Parts = Record<string, PartInfo>;

/* bundles in public/data/, written by scripts/data.ts */
export type Lang = "en" | "de";
export type Word = EnWord | DeWord;
export interface Bundle<W extends Word = Word> {
  words: W[];
  parts: Parts;
}
export type Synonyms = Record<string, Sense[]>;
