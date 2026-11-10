/* Pieces that show a word: headword, stars, grammar table, parts, senses. */
import { Fragment, createContext, useContext } from "react";
import { GENDER, PART_NAMES, grammarRows, isDe, starCount } from "./lexicon.ts";
import type { Lang, Parts, Sense, Word } from "./types.ts";

export interface WordCtx {
  lang: Lang;
  parts: Parts;
  showWord(word: string): void;
  showPart(key: string): void;
}
export const Ctx = createContext<WordCtx>(null!);
export const useWords = () => useContext(Ctx);

/* square flags, drawn inline so they need no image files */
export function Flag({ lang }: { lang: Lang }) {
  if (lang === "de")
    return (
      <svg className="flag" viewBox="0 0 3 3" aria-hidden="true">
        <rect width="3" height="1" fill="#000" /><rect y="1" width="3" height="1" fill="#DD0000" /><rect y="2" width="3" height="1" fill="#FFCE00" />
      </svg>
    );
  return (
    <svg className="flag" viewBox="0 0 14 14" aria-hidden="true">
      <rect width="14" height="14" fill="#fff" />
      <path d="M0 0h14v2H0zM0 4h14v2H0zM0 8h14v2H0zM0 12h14v2H0z" fill="#B22234" />
      <rect width="7" height="8" fill="#3C3B6E" />
      <g fill="#fff">
        {[[1.75, 2], [3.5, 2], [5.25, 2], [2.6, 4], [4.4, 4], [1.75, 6], [3.5, 6], [5.25, 6]].map(([cx, cy]) => <circle key={`${cx},${cy}`} cx={cx} cy={cy} r=".5" />)}
      </g>
    </svg>
  );
}

export function Stars({ score, className = "" }: { score: number; className?: string }) {
  const n = starCount(score);
  return (
    <span className={`stars ${className}`} role="img" aria-label={`중요도 별 ${n}개`}>
      {[1, 2, 3].map((i) => (i <= n ? <span key={i} className="on">★</span> : i - 0.5 === n ? <span key={i} className="on">☆</span> : <span key={i}>★</span>))}
    </span>
  );
}

export function Headword({ w }: { w: Word }) {
  const g = isDe(w) ? w.grammar : undefined;
  if (g?.type === "noun" && g.gender?.length) {
    if (g.number === "pl") return <span><span className="art g-f">die</span> {w.word}</span>;
    return (
      <span>
        {g.gender.map((x, i) => (
          <span key={x}>{i > 0 && <span className="dot">/</span>}<span className={`art g-${x}`}>{GENDER[x][0]}</span></span>
        ))}{" "}{w.word}
      </span>
    );
  }
  if (g?.type === "verb") {
    return (
      <span>
        {g.reflexive && <span className="refl">sich </span>}
        {g.separable && g.prefix
          ? <><span className="pre">{g.prefix}</span><span className="dot">·</span>{w.word.slice(g.prefix.length)}</>
          : w.word}
      </span>
    );
  }
  return <span>{w.word}</span>;
}

export function GrammarTable({ w }: { w: Word }) {
  const rows = grammarRows(w);
  if (!rows.length) return null;
  return <dl className="gtable">{rows.map(([k, v], i) => <Fragment key={i}><dt>{k}</dt><dd>{v}</dd></Fragment>)}</dl>;
}

export function Chips({ items, className = "syns" }: { items: string[]; className?: string }) {
  const { showWord } = useWords();
  return (
    <div className={className}>
      {items.map((x) => <button key={x} type="button" className="chip" onClick={() => showWord(x)}>{x}</button>)}
    </div>
  );
}

export function SenseBox({ s }: { s: Sense }) {
  return (
    <div className="sense">
      {s.pos && <span className="tag">{s.pos}</span>}
      {s.ko && <p className="ko">{s.ko}</p>}
      {s.en && <p className="en">{s.en}</p>}
      {!!s.synonyms?.length && <Chips items={s.synonyms} />}
      {(s.examples ?? []).slice(0, 2).map((x, i) => (
        <Fragment key={i}>
          <p className="ex">{x.text}</p>
          {x.ko && <p className="ex-ko">{x.ko}</p>}
        </Fragment>
      ))}
    </div>
  );
}

export function WordMeta({ w }: { w: Word }) {
  const { parts, showPart } = useWords();
  const origin = isDe(w) ? undefined : w.origin;
  if (!w.parts?.length && !origin) return null;
  return (
    <div className="meta">
      {(w.parts ?? []).map((key) => {
        const info = parts[key];
        const form = info?.form || key.replace(/\(.*\)$/, "");
        return (
          <button key={key} type="button" className={`part ${info?.type ?? ""}`} onClick={() => showPart(key)}
            aria-label={`${PART_NAMES[info?.type] || "구성 요소"} ${info?.form || key}`}>
            <b>{form}</b>
            {info && <span>{info.ko}</span>}
          </button>
        );
      })}
      {origin && <p className="origin">{origin.ko}</p>}
    </div>
  );
}

export const Senses = ({ w }: { w: Word }) => <>{w.senses.map((s, i) => <SenseBox key={i} s={s} />)}</>;
