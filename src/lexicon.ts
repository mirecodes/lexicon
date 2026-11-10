/* App logic with no UI: languages, storage, decks, German grammar text. */
import type { Bundle, DeWord, EnWord, Gender, JaWord, Lang, Synonyms, VerbClass, Word } from "./types.ts";

export const TODAY_COUNT = 20;
const PER_DAY = 50;
export const LANGS = {
  en: { name: "ENGLISH", title: "Lexicon GRE", daysTab: "Day별", key: "",
        daysTitle: "Day별 단어장", daysSub: "하루 50단어, 중요도가 높은 단어부터 나옵니다.",
        search: "Search words or meanings", sortScore: "Importance" },
  de: { name: "DEUTSCH", title: "Lexicon Deutsch", daysTab: "레벨별", key: "-de",
        daysTitle: "레벨별 단어장", daysSub: "하루 50단어, 레벨 안에서 자주 쓰는 단어부터 나옵니다.",
        search: "Wort oder Bedeutung suchen", sortScore: "Niveau" },
  ja: { name: "日本語", title: "Lexicon 日本語", daysTab: "레벨별", key: "-ja",
        daysTitle: "레벨별 단어장", daysSub: "하루 50단어, 레벨 안에서 자주 쓰는 단어부터 나옵니다.",
        search: "単語・読み・意味で検索", sortScore: "レベル" },
} as const;
export const isLang = (l: unknown): l is Lang => l === "en" || l === "de" || l === "ja";
export const isJa = (w: Word): w is JaWord => "reading" in w;
export const isDe = (w: Word): w is DeWord => "level" in w && !isJa(w);
export const isEn = (w: Word): w is EnWord => "score" in w;
/** Words with a level (German, Japanese) */
export const levelOf = (w: Word): string | null => ("level" in w ? w.level : null);
/** map key for a word: Japanese has homographs (方 かた / ほう, いる 居る / 要る), so its key adds the reading and kanji */
export const keyOf = (w: Word) => (isJa(w) ? [w.word, w.reading, w.kanji].filter(Boolean).join("|") : w.word.toLowerCase());
/** text to sort a word by: Japanese goes by reading (gojūon order) */
export const sortText = (w: Word) => (isJa(w) ? w.reading.replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60)) : w.word);

export const NAMES: Record<string, string> = { VocabCom: "Vocabulary.com" };
export const PART_NAMES: Record<string, string> = { prefix: "접두사", root: "어근", suffix: "접미사", sep: "분리 전철", insep: "비분리 전철", stem: "기본 단어", kanji: "한자" };
export const GENDER: Record<Gender, [string, string]> = { m: ["der", "남성"], f: ["die", "여성"], n: ["das", "중성"] };
const CLASS: Record<VerbClass, string> = { weak: "규칙 변화 (약변화)", strong: "불규칙 변화 (강변화)", mixed: "혼합 변화", irregular: "불규칙 변화", modal: "화법조동사 (불규칙)" };
const AUX: Record<string, string> = { haben: "hat", sein: "ist", "haben/sein": "hat/ist" };
const POS_KO: Record<string, string> = { noun: "명사", verb: "동사", adj: "형용사", adv: "부사", prep: "전치사", conj: "접속사", pron: "대명사", det: "관사·한정사", num: "수사", intj: "감탄사", particle: "불변화사", phrase: "구" };

/* localStorage, failing quietly (private mode, blocked storage) */
export const store = {
  get<T = unknown>(k: string): T | null { try { return JSON.parse(localStorage.getItem(k) ?? "null"); } catch { return null; } },
  set(k: string, v: unknown) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* ignore */ } },
};
const skey = (lang: Lang, k: string) => k + LANGS[lang].key;

/* data */
export interface Loaded extends Bundle { byWord: Map<string, Word> }
const cache: Partial<Record<Lang, Promise<Loaded>>> = {};
const getJSON = <T>(url: string): Promise<T> => fetch(url).then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); });
export function load(lang: Lang): Promise<Loaded> {
  return (cache[lang] ??= getJSON<Bundle>(`data/${lang}.json`)
    .then((b) => ({ ...b, byWord: new Map(b.words.map((w) => [keyOf(w), w])) }))
    .catch((e) => { delete cache[lang]; throw e; }));
}
let synonyms: Promise<Synonyms> | null = null;
export const loadSynonyms = () => (synonyms ??= getJSON<Synonyms>("data/en-synonyms.json").catch((e) => { synonyms = null; throw e; }));

/* 중요도 → 별 3개 (0-40: 1, 40-60: 2, 60-80: 2 + 테두리 별, 80-100: 3) */
export const starCount = (score: number) => (score < 40 ? 1 : score < 60 ? 2 : score < 80 ? 2.5 : 3);

/* day groups: GRE is one run of days; German and Japanese restart the day count in each level */
export interface Day { id: string; n: number; lv: string | null; list: Word[] }
const LEVELS: Record<Lang, (string | null)[]> = { en: [null], de: ["a1", "a2", "b1"], ja: ["n5", "n4", "n3", "n2", "n1"] };
export function groups(lang: Lang, words: Word[]) {
  return LEVELS[lang].map((lv) => {
    const list = lv ? words.filter((w) => levelOf(w) === lv) : words;
    const days: Day[] = [];
    for (let i = 0; i < list.length; i += PER_DAY) days.push({ id: `${lv ? lv + "-" : ""}${days.length + 1}`, n: days.length + 1, lv, list: list.slice(i, i + PER_DAY) });
    return { lv, days };
  }).filter((g) => g.days.length);
}
const dayTitle = (d: Day) => (d.lv ? `${d.lv.toUpperCase()} Day ${d.n}` : `Day ${d.n}`);

export interface Progress { i: number; done: boolean }
export const getProgress = (lang: Lang) => store.get<Record<string, Progress>>(skey(lang, "prog")) ?? {};
export const getLastDay = (lang: Lang) => store.get<string>(skey(lang, "lastDay"));

export interface Deck { title: string; list: Word[]; start: number; doneLabel: string; doneHash: string; day?: number; save(i: number): void }

export function dayDeck(lang: Lang, words: Word[], id: string | undefined): Deck {
  const ds = groups(lang, words).flatMap((g) => g.days);
  const i = Math.max(0, ds.findIndex((d) => d.id === id));
  const d = ds[i], next = ds[i + 1];
  const p = getProgress(lang)[d.id];
  return {
    title: dayTitle(d), day: d.n, list: d.list, start: p && !p.done ? Math.min(p.i, d.list.length - 1) : 0,
    doneLabel: next ? `${dayTitle(next)} 시작` : "목록으로", doneHash: next ? `#/${lang}/day/${next.id}` : `#/${lang}/days`,
    save(j) {
      const all = getProgress(lang);
      all[d.id] = { i: j >= d.list.length ? 0 : j, done: all[d.id]?.done || j >= d.list.length };
      store.set(skey(lang, "prog"), all);
      store.set(skey(lang, "lastDay"), d.id);
    },
  };
}

function fnv(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

export function todayDeck(lang: Lang, words: Word[]): Deck {
  const d = new Date();
  const date = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  // German, Japanese: any level. English: the more important half (words is sorted by importance)
  const pool = lang === "en" ? words.slice(0, Math.ceil(words.length / 2)) : words;
  const list = pool.map((w) => [fnv(date + w.word), w] as const).sort((a, b) => a[0] - b[0]).slice(0, TODAY_COUNT).map((x) => x[1]);
  const s = store.get<{ date: string; i: number }>(skey(lang, "today"));
  return {
    title: "오늘의 단어", list, start: s?.date === date ? Math.min(s.i, list.length) : 0,
    doneLabel: `${LANGS[lang].daysTab} 학습으로`, doneHash: `#/${lang}/days`,
    save(i) { store.set(skey(lang, "today"), { date, i }); },
  };
}

/* Japanese grammar text */
const JA_POS: Record<string, string> = { noun: "명사", verb: "동사", adv: "부사", conj: "접속사", pron: "대명사", num: "수사", interj: "감탄사",
  expr: "표현", counter: "조수사", suffix: "접미사", prefix: "접두사", adnominal: "연체사", aux: "조동사", particle: "조사" };
const JA_CLASS: Record<string, string> = { godan: "1그룹 동사 (5단)", ichidan: "2그룹 동사 (1단)", suru: "3그룹 동사 (する)", kuru: "3그룹 동사 (来る)",
  i: "い형용사", na: "な형용사" };
function jaLine(w: JaWord) {
  const g = w.grammar;
  return [(g.class && JA_CLASS[g.class]) || JA_POS[g.type] || (g.type === "adj" ? "형용사" : ""),
    g.transitive === true ? "타동사" : g.transitive === false ? "자동사" : null, g.suru ? "する를 붙여 동사로" : null].filter(Boolean).join(" · ");
}

/* German grammar text */
export function grammarLine(w: DeWord | JaWord) {
  if (isJa(w)) return jaLine(w);
  const g = w.grammar ?? { type: "" };
  if (g.type === "noun") {
    if (g.number === "pl") return "복수형으로만 씀";
    const gender = (g.gender ?? []).map((x) => GENDER[x][1]).join("·");
    return [gender, g.plural ? `복수 die ${g.plural}` : "복수 없음"].filter(Boolean).join(" · ");
  }
  if (g.type === "verb") return [g.separable ? "분리동사" : null, g.class && CLASS[g.class]].filter(Boolean).join(" · ") || "동사";
  return POS_KO[g.type] || "";
}

export function grammarRows(w: Word): [string, string][] {
  if (!isDe(w)) return [];
  const g = w.grammar ?? { type: "" };
  const rows: [string, string][] = [];
  if (g.type === "noun" && g.number !== "pl") {
    rows.push(["성", (g.gender ?? []).map((x) => `${GENDER[x][1]} (${GENDER[x][0]})`).join(", ")]);
    rows.push(["복수", g.plural ? `die ${g.plural}` : "없음"]);
    if (g.genitive) rows.push(["2격", `des ${g.genitive}`]);
  } else if (g.type === "verb") {
    if (g.class) rows.push(["변화", CLASS[g.class]]);
    if (g.separable && g.prefix) rows.push(["분리", `${g.prefix} + ${w.word.slice(g.prefix.length)} · 전철은 문장 끝으로 이동`]);
    // reflexive "sich" goes right after the finite verb: er freut sich, er zieht sich um, er hat sich gefreut
    const withSich = (finite: string) => (g.reflexive ? finite.replace(/^(\S+)/, "$1 sich") : finite);
    if (g.present3) rows.push(["현재", `er ${withSich(g.present3)}`]);
    if (g.past) rows.push(["과거", `er ${withSich(g.past)}`]);
    if (g.pp) rows.push(["현재완료", `er ${withSich(AUX[g.aux ?? ""] || "hat")} ${g.pp}`]);
    if (g.aux === "haben/sein") rows.push(["", "이동·상태 변화 뜻이면 ist, 그 밖에는 hat"]);
  } else if (g.type === "adj") {
    if (g.comparative) rows.push(["비교급", g.comparative]);
    if (g.superlative) rows.push(["최상급", `am ${g.superlative}`]);
  }
  return rows;
}

export const listNames = (w: EnWord) => w.lists.map((l) => NAMES[l] || l).join(" · ");
export const gloss = (w: Word) => w.senses.map((s) => s.ko || s.en).join(" / ");

/* theme */
export type Theme = "system" | "light" | "dark";
export function syncBar() {
  const bar = getComputedStyle(document.documentElement).getPropertyValue("--bar").trim();
  document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')!.content = bar;
}
export function setTheme(mode: Theme) {
  if (mode === "light" || mode === "dark") document.documentElement.dataset.theme = mode;
  else delete document.documentElement.dataset.theme;
  store.set("theme", mode === "system" ? null : mode);
  syncBar();
}
export const getTheme = (): Theme => store.get<Theme>("theme") || "system";
