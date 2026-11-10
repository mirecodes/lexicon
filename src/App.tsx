import { Fragment, memo, useCallback, useDeferredValue, useEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { Cards } from "./Cards.tsx";
import { CONSTELLATIONS, type Constellation } from "./constellations.ts";
import {
  LANGS, PART_NAMES, TODAY_COUNT, dayDeck, getLastDay, getProgress, getTheme, gloss, grammarLine, groups, isEn, isLang,
  keyOf, levelOf, load, loadSynonyms, setTheme, sortText, store, todayDeck, type Loaded, type Theme,
} from "./lexicon.ts";
import { Chips, Ctx, Flag, GrammarTable, Headword, Reading, SenseBox, Senses, Stars, WordMeta, useWords } from "./words.tsx";
import type { Lang, Sense, Word } from "./types.ts";

/* routing: #/<lang>/<view>[/<day id>] */
type Tab = "today" | "days" | "list";
const useHash = () => useSyncExternalStore((cb) => { addEventListener("hashchange", cb); return () => removeEventListener("hashchange", cb); }, () => location.hash);
function parse(hash: string) {
  let [l, view, arg] = hash.replace(/^#\/?/, "").split("/");
  if (!isLang(l)) { [view, arg] = [l, view]; l = store.get<string>("lang") || "en"; }
  return { lang: (isLang(l) ? l : "en") as Lang, view, arg };
}

type Sheet = { kind: "word"; word: string } | { kind: "part"; key: string } | null;

const Icon = ({ children }: { children: ReactNode }) => <svg viewBox="0 0 24 24" aria-hidden="true">{children}</svg>;
const CloseIcon = () => <Icon><path d="M18 6L6 18M6 6l12 12" /></Icon>;

/** <dialog> driven by `open`; closes on Esc, the close button, or a backdrop click */
function Dialog({ open, onClose, title, label, children }: { open: boolean; onClose(): void; title: ReactNode; label: string; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current!;
    if (open && !d.open) d.showModal();
    else if (!open && d.open) d.close();
  }, [open]);
  return (
    // the close event arrives after our own close(); only Esc (dialog still meant open) should report it
    <dialog ref={ref} aria-labelledby={`${label}-title`} onClose={() => { if (open) onClose(); }} onClick={(e) => { if (e.target === ref.current) onClose(); }}>
      <div className="sheet-head">
        <h2 id={`${label}-title`}>{title}</h2>
        <button className="icon" aria-label="닫기" onClick={onClose}><CloseIcon /></button>
      </div>
      {children}
    </dialog>
  );
}

/* popup for a word or a word part */
function WordSheet({ word, data }: { word: string; data: Loaded }) {
  const entry = data.byWord.get(word.toLowerCase());
  const body = useRef<HTMLDivElement>(null);
  const [extra, setExtra] = useState<Sense[] | null | "loading" | "error">("loading");
  useEffect(() => {
    body.current!.scrollTop = 0;
    if (entry) return;
    let live = true;
    setExtra("loading");
    loadSynonyms().then((s) => live && setExtra(s[word.toLowerCase()] ?? null), () => live && setExtra("error"));
    return () => { live = false; };
  }, [word, entry]);
  return (
    <div className="sheet" ref={body}>
      {entry ? (
        <>
          {isEn(entry)
            ? <Stars score={entry.score} className="score" />
            : <><Reading w={entry} /><p className="gline">{entry.level.toUpperCase()} · {grammarLine(entry)}</p><GrammarTable w={entry} /></>}
          <WordMeta w={entry} />
          <Senses w={entry} />
        </>
      ) : extra === "loading" ? <p className="note">불러오는 중…</p>
        : extra === "error" ? <p className="note">뜻을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</p>
        : extra ? extra.map((s, i) => <SenseBox key={i} s={s} />)
        : <p className="note">이 단어의 뜻 정보가 없습니다.</p>}
    </div>
  );
}

function PartSheet({ partKey, data }: { partKey: string; data: Loaded }) {
  const info = data.parts[partKey];
  const others = useMemo(() => data.words.filter((w) => w.parts?.includes(partKey)).sort((a, b) => sortText(a).localeCompare(sortText(b))), [data, partKey]);
  return (
    <div className="sheet">
      {info && <><span className="tag">{PART_NAMES[info.type] || info.type}</span><p className="ko">{info.ko}</p></>}
      {info?.type === "kanji" && <p className="note" lang="ja">{[info.on?.length && `음독 ${info.on.join("、")}`, info.kun?.length && `훈독 ${info.kun.join("、")}`].filter(Boolean).join(" · ")}</p>}
      {info?.type === "sep" && <p className="note">분리 전철: 문장에서 동사와 떨어져 맨 뒤로 갑니다. 예) Ich rufe dich an.</p>}
      {info?.type === "insep" && <p className="note">비분리 전철: 동사에 항상 붙어 있고, 과거분사에 ge-가 붙지 않습니다.</p>}
      <p className="note">이 요소가 포함된 단어 {others.length}개</p>
      <Chips items={others.map(keyOf)} labels={others.map((w) => w.word)} className="related" />
    </div>
  );
}

/* day grid */
function Days({ lang, words }: { lang: Lang; words: Word[] }) {
  const prog = getProgress(lang), last = getLastDay(lang);
  return (
    <section className="view">
      <p className="title">{LANGS[lang].daysTitle}</p>
      <p className="sub">{LANGS[lang].daysSub}</p>
      <div className="scroll">
        {groups(lang, words).map((g) => (
          <Fragment key={g.lv ?? "all"}>
            {g.lv && <p className="level">{g.lv.toUpperCase()} · {g.days.reduce((s, d) => s + d.list.length, 0)}단어</p>}
            <div className="grid">
              {g.days.map((d) => {
                const p = prog[d.id];
                return (
                  <a key={d.id} href={`#/${lang}/day/${d.id}`} className={["day", p?.done && "done", d.id === String(last) && "last"].filter(Boolean).join(" ")}>
                    {lang === "en" && <Sky c={CONSTELLATIONS[(d.n - 1) % CONSTELLATIONS.length]} />}
                    <b>Day {d.n}</b>
                    <span>{p?.done ? "완료" : p?.i ? `${p.i + 1} / ${d.list.length}` : `${d.list.length}단어`}</span>
                  </a>
                );
              })}
            </div>
          </Fragment>
        ))}
      </div>
    </section>
  );
}

/* faint constellation behind a GRE day card; it lights up on hover and once the day is done */
function Sky({ c }: { c: Constellation }) {
  return (
    <>
      <svg className="sky" viewBox="0 0 100 100" aria-hidden="true">
        <title>{`${c.ko} (${c.en})`}</title>
        {c.lines.map(([a, b]) => <line key={`${a}-${b}`} x1={c.stars[a][0]} y1={c.stars[a][1]} x2={c.stars[b][0]} y2={c.stars[b][1]} />)}
        {c.stars.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="1.6" style={{ animationDelay: `${(i * 0.37) % 2}s` }} />)}
      </svg>
      <small className="sky-name">{c.en}</small>
    </>
  );
}

/* word list */
const ListRow = memo(function ListRow({ w, text, hidden }: { w: Word; text: string; hidden: boolean }) {
  const { showWord } = useWords();
  return (
    <button type="button" className="row" hidden={hidden} onClick={() => showWord(keyOf(w))}>
      <span className="w"><Headword w={w} /></span>
      <span className="m">{text}</span>
      {isEn(w) ? <Stars score={w.score} className="s" /> : <span className="s">{levelOf(w)!.toUpperCase()}</span>}
    </button>
  );
});

function WordList({ lang, words }: { lang: Lang; words: Word[] }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"abc" | "score">("abc");
  const query = useDeferredValue(q.trim().toLowerCase());
  const scroll = useRef<HTMLDivElement>(null);
  const rows = useMemo(() => {
    const r = words.map((w) => ({ w, text: gloss(w), key: `${w.word} ${"reading" in w ? w.reading : ""} ${gloss(w)}`.toLowerCase() }));
    return sort === "abc" ? r.sort((a, b) => sortText(a.w).localeCompare(sortText(b.w), lang)) : r; // words come sorted by importance
  }, [words, sort, lang]);
  useEffect(() => { scroll.current!.scrollTop = 0; }, [rows]);
  const n = query ? rows.filter((r) => r.key.includes(query)).length : rows.length;
  return (
    <section className="view">
      <div className="tools">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={LANGS[lang].search} aria-label={LANGS[lang].search}
          autoComplete="off" autoCapitalize="off" spellCheck={false} />
        <select value={sort} onChange={(e) => setSort(e.target.value as "abc" | "score")} aria-label="정렬 기준">
          <option value="abc">A–Z</option>
          <option value="score">{LANGS[lang].sortScore}</option>
        </select>
      </div>
      <p className="sub" aria-live="polite">{n.toLocaleString()}단어</p>
      <div className="scroll" ref={scroll}>
        {rows.map((r) => <ListRow key={keyOf(r.w)} w={r.w} text={r.text} hidden={!!query && !r.key.includes(query)} />)}
      </div>
    </section>
  );
}

/* settings */
function Settings({ lang, tab, onClose }: { lang: Lang; tab: Tab; onClose(): void }) {
  const [theme, setT] = useState<Theme>(getTheme);
  return (
    <div className="sheet">
      <fieldset className="opts">
        <legend>학습 언어</legend>
        {([["en", "English", "GRE · 2,713단어"], ["de", "Deutsch", "A1–B1 · 2,915단어"], ["ja", "日本語", "N5–N3 · 2,948단어"]] as const).map(([l, name, note]) => (
          <label key={l} className="opt">
            {/* keep the same tab; day ids differ between languages, so a day deck falls back to the day list */}
            <input type="radio" name="lang" value={l} checked={lang === l} onChange={() => { onClose(); location.hash = `#/${l}/${tab}`; }} />
            <Flag lang={l} />{name}<small>{note}</small>
          </label>
        ))}
      </fieldset>
      <fieldset className="opts">
        <legend>테마</legend>
        {([["system", "기기 설정 따르기"], ["light", "밝게"], ["dark", "어둡게"]] as const).map(([v, name]) => (
          <label key={v} className="opt">
            <input type="radio" name="theme" value={v} checked={theme === v} onChange={() => { setTheme(v); setT(v); }} />{name}
          </label>
        ))}
      </fieldset>
    </div>
  );
}

export function App() {
  const { lang, view, arg } = parse(useHash());
  const [data, setData] = useState<{ lang: Lang; d: Loaded } | "error" | null>(null);
  const [sheet, setSheet] = useState<Sheet>(null);
  const [settings, setSettings] = useState(false);
  const [fill, setFill] = useState(0);
  const tab: Tab = view === "days" || view === "day" ? "days" : view === "list" ? "list" : "today";

  useEffect(() => {
    let live = true;
    store.set("lang", lang);
    document.title = LANGS[lang].title;
    load(lang).then((d) => live && setData({ lang, d }), () => live && setData("error"));
    return () => { live = false; };
  }, [lang]);

  // a new route closes the popup and empties the progress bar until a deck fills it
  const hash = useHash();
  useEffect(() => { setSheet(null); setFill(0); }, [hash]);

  const showWord = useCallback((word: string) => setSheet({ kind: "word", word }), []);
  const showPart = useCallback((key: string) => setSheet({ kind: "part", key }), []);
  const loaded = data && data !== "error" && data.lang === lang ? data.d : null;
  const ctx = useMemo(() => ({ lang, parts: loaded?.parts ?? {}, showWord, showPart }), [lang, loaded, showWord, showPart]);

  const deck = useMemo(() => {
    if (!loaded || (tab !== "today" && view !== "day")) return null;
    return view === "day" ? dayDeck(lang, loaded.words, arg || undefined) : todayDeck(lang, loaded.words);
  }, [loaded, lang, view, arg, tab]);

  let main: ReactNode;
  if (data === "error") main = <section className="view"><p id="pos">단어 데이터를 불러오지 못했습니다. 새로고침해 주세요.</p></section>;
  else if (!loaded) main = <section className="view"><p id="pos">불러오는 중…</p></section>;
  else if (view === "days") main = <Days lang={lang} words={loaded.words} />;
  else if (view === "list") main = <WordList key={lang} lang={lang} words={loaded.words} />;
  else main = <Cards key={hash + lang} deck={deck!} setFill={setFill} />;

  const sheetTitle = sheet?.kind === "word"
    ? (loaded?.byWord.get(sheet.word.toLowerCase()) ? <Headword w={loaded.byWord.get(sheet.word.toLowerCase())!} /> : sheet.word)
    : sheet ? (loaded?.parts[sheet.key]?.form || sheet.key) : "";

  return (
    <Ctx.Provider value={ctx}>
      <header>
        <button className="now" aria-label="학습 언어 바꾸기" onClick={() => setSettings(true)}>
          <Flag lang={lang} /><span>{LANGS[lang].name}</span>
        </button>
        <button className="icon" aria-label="설정" onClick={() => setSettings(true)}>
          <Icon><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" /><circle cx="12" cy="12" r="3" /></Icon>
        </button>
      </header>
      <div className="track"><div id="fill" style={{ width: `${fill}%` }} /></div>
      <main>{main}</main>
      <nav className="tabs" aria-label="주요 메뉴">
        <a href={`#/${lang}/today`} aria-current={tab === "today" ? "page" : undefined}>
          <Icon><path d="M12 2v4M4.9 8.9l1.4 1.4M2 18h2M20 18h2M17.7 10.3l1.4-1.4M22 22H2M16 18a4 4 0 0 0-8 0" /></Icon>오늘의 {TODAY_COUNT}단어
        </a>
        <a href={`#/${lang}/days`} aria-current={tab === "days" ? "page" : undefined}>
          <Icon><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></Icon>{LANGS[lang].daysTab}
        </a>
        <a href={`#/${lang}/list`} aria-current={tab === "list" ? "page" : undefined}>
          <Icon><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></Icon>전체 단어
        </a>
      </nav>
      <Dialog open={!!sheet} onClose={() => setSheet(null)} title={sheetTitle} label="sheet">
        {loaded && sheet?.kind === "word" && <WordSheet key={sheet.word} word={sheet.word} data={loaded} />}
        {loaded && sheet?.kind === "part" && <PartSheet partKey={sheet.key} data={loaded} />}
      </Dialog>
      <Dialog open={settings} onClose={() => setSettings(false)} title="설정" label="settings">
        <Settings lang={lang} tab={tab} onClose={() => setSettings(false)} />
      </Dialog>
    </Ctx.Provider>
  );
}
