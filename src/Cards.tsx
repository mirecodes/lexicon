/* Flash cards: tap to flip, swipe or arrow keys to move. */
import { useEffect, useLayoutEffect, useRef, useState, type PointerEvent } from "react";
import { flushSync } from "react-dom";
import { grammarLine, isDe, listNames } from "./lexicon.ts";
import type { Deck } from "./lexicon.ts";
import { GrammarTable, Headword, Senses, Stars, WordMeta } from "./words.tsx";
import type { Word } from "./types.ts";

const calm = matchMedia("(prefers-reduced-motion: reduce)");
const Chevron = ({ d }: { d: string }) => <svg viewBox="0 0 24 24" aria-hidden="true"><path d={d} /></svg>;

function Front({ w, first }: { w: Word; first: boolean }) {
  return (
    <>
      <h2><Headword w={w} /></h2>
      {isDe(w)
        ? <><p className="gline">{grammarLine(w)}</p><p className="lists">{w.level.toUpperCase()}</p></>
        : <><Stars score={w.score} className="score" /><p className="lists">{listNames(w)}</p></>}
      {first && <p className="hint">카드를 누르면 뜻이 보이고, 좌우로 밀면 넘어갑니다.</p>}
    </>
  );
}

export function Cards({ deck, setFill }: { deck: Deck; setFill(pct: number): void }) {
  const [idx, setIdx] = useState(deck.start);
  const [flipped, setFlipped] = useState(false);
  const [still, setStill] = useState(false); // flip back without the rotation when the word changes
  const slide = useRef<HTMLDivElement>(null), card = useRef<HTMLDivElement>(null), back = useRef<HTMLDivElement>(null);
  const busy = useRef(false);
  const list = deck.list, done = idx === list.length, w = list[idx];
  const canGo = (delta: number) => (delta > 0 ? !done : idx > 0);

  useEffect(() => {
    deck.save(idx);
    setFill(done ? 100 : ((idx + 1) / list.length) * 100);
  }, [deck, idx, done, list.length, setFill]);

  useLayoutEffect(() => {
    if (!still) return;
    void card.current!.offsetWidth; // commit the unflipped state so the next word's back never shows mid-rotation
    setStill(false);
  }, [still]);

  useEffect(() => { if (flipped) back.current!.scrollTop = 0; }, [flipped]);

  const toggle = () => {
    if (done) location.hash = deck.doneHash;
    else setFlipped((f) => !f);
  };

  const move = (delta: number) => {
    const s = slide.current!;
    if (busy.current) return;
    if (!canGo(delta)) { s.style.transform = ""; return; }
    const step = () => flushSync(() => { setIdx((i) => i + delta); setFlipped(false); setStill(true); });
    if (calm.matches) { step(); s.style.transform = ""; return; }
    busy.current = true;
    s.style.transform = `translateX(${-delta * 110}%)`;
    s.style.opacity = "0";
    setTimeout(() => {
      step();
      s.classList.add("drag");
      s.style.transform = `translateX(${delta * 40}%)`;
      void s.offsetWidth;
      s.classList.remove("drag");
      s.style.transform = "";
      s.style.opacity = "";
      busy.current = false;
    }, 150);
  };

  // keep the latest move/toggle for the window listener
  const keys = useRef({ move, toggle });
  keys.current = { move, toggle };
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (document.querySelector("dialog[open]") || ["SELECT", "INPUT"].includes(t.tagName)) return;
      if (e.key === "ArrowRight") keys.current.move(1);
      else if (e.key === "ArrowLeft") keys.current.move(-1);
      else if (e.key === " " && t.tagName !== "BUTTON") { e.preventDefault(); keys.current.toggle(); }
    };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, []);

  /* swipe */
  const drag = useRef({ x: null as number | null, y: 0, on: false });
  const endDrag = () => { drag.current = { x: null, y: 0, on: false }; slide.current!.classList.remove("drag"); };
  const onDown = (e: PointerEvent) => {
    if ((e.target as HTMLElement).closest("button")) return;
    drag.current = { x: e.clientX, y: e.clientY, on: false };
  };
  const onMove = (e: PointerEvent) => {
    const d = drag.current;
    if (d.x === null || busy.current) return;
    const dx = e.clientX - d.x, dy = e.clientY - d.y;
    if (!d.on && Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) {
      d.on = true;
      slide.current!.classList.add("drag");
      e.currentTarget.setPointerCapture(e.pointerId);
    }
    if (d.on) slide.current!.style.transform = `translateX(${dx}px) rotate(${dx / 50}deg)`;
  };
  const onUp = (e: PointerEvent) => {
    const d = drag.current;
    if (d.x === null) return;
    const dx = e.clientX - d.x, dy = e.clientY - d.y, was = d.on;
    endDrag();
    if (was) {
      if (Math.abs(dx) > 70) move(dx < 0 ? 1 : -1);
      else slide.current!.style.transform = "";
    } else if (Math.abs(dx) < 10 && Math.abs(dy) < 10 && !done) setFlipped((f) => !f);
  };

  return (
    <section className="view">
      <p id="pos" aria-live="polite">{done ? `${deck.title} 완료` : `${deck.title} · ${idx + 1} / ${list.length}`}</p>
      <div className="stage" onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}
        onPointerCancel={() => { endDrag(); slide.current!.style.transform = ""; }}>
        <div id="slide" ref={slide}>
          <div id="card" ref={card} className={[flipped && "flip", still && "still"].filter(Boolean).join(" ")}>
            <div className="face front" inert={flipped}>
              {done
                ? <><h2>{deck.title} 완료</h2><p className="lists">{list.length}단어를 모두 넘겼습니다.</p></>
                : <Front w={w} first={idx === 0} />}
            </div>
            <div className="face back" ref={back} inert={!flipped}>
              {!done && <><h2><Headword w={w} /></h2><GrammarTable w={w} /><WordMeta w={w} /><Senses w={w} /></>}
            </div>
          </div>
        </div>
      </div>
      <div className="controls">
        <button className="icon" aria-label="이전 단어" disabled={!canGo(-1)} onClick={() => move(-1)}><Chevron d="M15 18l-6-6 6-6" /></button>
        <button id="flip" onClick={toggle}>{done ? deck.doneLabel : flipped ? "단어 보기" : "뜻 보기"}</button>
        <button className="icon" aria-label="다음 단어" disabled={!canGo(1)} onClick={() => move(1)}><Chevron d="M9 18l6-6-6-6" /></button>
      </div>
    </section>
  );
}
