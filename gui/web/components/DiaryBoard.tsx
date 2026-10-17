"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import BoardCell from "@/components/BoardCell";
import DiaryInput from "@/components/DiaryInput";
import {
  DAY_MS,
  ROWS_PER_STEP,
  cellEnd,
  cellKey,
  cellStart,
  dayStartMs,
  inCell,
  newBoard,
  sameSpan,
  span,
  type Board,
  type Plan,
} from "@/lib/board";
import { dateTime, isDay, today } from "@/lib/date";
import { T } from "@/lib/text";
import { useBoardCells } from "@/lib/useBoardCells";

// 見えている所の外に、上下・左右へどれだけ(px)描いておくか。これを切ったら足し、REMOVE を越えて離れたら消す。
// REMOVE が ADD 以上なら、足した行がすぐ消える(消した行がすぐ足される)ことはない
const ADD_Y = 400;
const REMOVE_Y = 800;
const ADD_X = 200;
const REMOVE_X = 600;

/** 基準の時刻。画面の左の端・縦の真ん中の点が、どの枡のどこにあるか(枡の中の割合)。
 * 行を足し消ししても、読み終えて高さが変わっても、描き直すたびにこの点を画面の左の真ん中へ戻す */
type Anchor = { row: number; col: number; y: number; x: number };

/** 基準の時刻(枡の始めの 0 時から、枡の日数ぶんを高さの割合で割り振る) */
function anchorTime(origin: string, { row, col, y }: Anchor): number {
  const start = dayStartMs(cellStart(origin, row, col));
  return start + Math.max(0, dayStartMs(cellEnd(origin, row, col)) + DAY_MS - start) * y;
}

/** 基準の点を、画面の左の真ん中へ動かす */
function placeAnchor(el: HTMLElement, { row, col, y, x }: Anchor) {
  const rowEl = el.querySelector(`[data-row="${row}"]`);
  const colEl = rowEl?.querySelector(`[data-col="${col}"]`);
  if (!rowEl || !colEl) return;
  const box = el.getBoundingClientRect();
  const r = rowEl.getBoundingClientRect();
  const c = colEl.getBoundingClientRect();
  el.scrollTop += r.top + r.height * y - (box.top + el.clientHeight / 2);
  el.scrollLeft += c.left + c.width * x - box.left;
}

/** 画面の左の真ん中にある枡と、その中の位置 */
function readAnchor(el: HTMLElement): Anchor | null {
  const box = el.getBoundingClientRect();
  const middle = box.top + el.clientHeight / 2;
  const rowEl = [...el.querySelectorAll<HTMLElement>("[data-row]")].find((r) => r.getBoundingClientRect().bottom > middle);
  const colEl = rowEl && [...rowEl.querySelectorAll<HTMLElement>("[data-col]")].find((c) => c.getBoundingClientRect().right > box.left);
  if (!rowEl || !colEl) return null;
  const r = rowEl.getBoundingClientRect();
  const c = colEl.getBoundingClientRect();
  const ratio = (n: number) => Math.min(1, Math.max(0, n));
  return {
    row: Number(rowEl.dataset.row),
    col: Number(colEl.dataset.col),
    y: ratio((middle - r.top) / r.height),
    x: ratio((box.left - c.left) / c.width),
  };
}

/** 端の行から数えて、見えている所から REMOVE_Y より離れた行の数。`heights` は端の側から、`outside` は見えている所の外の高さ */
function rowsBeyond(heights: number[], outside: number): number {
  let count = 0;
  for (const height of heights) {
    if (outside - height <= REMOVE_Y) break;
    outside -= height;
    count++;
  }
  return count;
}

/** 見えている所の外の余白が ADD を切った向きに足し、REMOVE より離れた行・列を除いた、次に描く範囲 */
function nextWindow(el: HTMLElement, board: Board): Pick<Board, "rows" | "cols"> {
  const rows = { ...board.rows };
  const cols = { ...board.cols };

  const rowEls = [...el.querySelectorAll<HTMLElement>("[data-row]")];
  const heights = rowEls.map((r) => r.getBoundingClientRect().height);
  const above = el.scrollTop;
  const below = el.scrollHeight - el.scrollTop - el.clientHeight;
  if (above < ADD_Y) rows.first -= ROWS_PER_STEP;
  else rows.first += rowsBeyond(heights, above);
  if (below < ADD_Y) rows.last += ROWS_PER_STEP;
  else rows.last -= rowsBeyond(heights.toReversed(), below);

  // 列は幅がそろっているので、一列目と二列目の間隔で数える
  const colEls = rowEls[0] ? [...rowEls[0].querySelectorAll<HTMLElement>("[data-col]")] : [];
  if (colEls.length > 0) {
    const pitch = colEls.length > 1 ? colEls[1].offsetLeft - colEls[0].offsetLeft : colEls[0].offsetWidth;
    const colsBeyond = (outside: number) => Math.max(0, Math.floor((outside - REMOVE_X) / pitch));
    const left = el.scrollLeft;
    const right = el.scrollWidth - el.scrollLeft - el.clientWidth;
    if (left < ADD_X) cols.first = Math.max(board.minCol, cols.first - 1);
    else cols.first += colsBeyond(left);
    if (right < ADD_X) cols.last += 1;
    else cols.last -= colsBeyond(right);
  }
  return { rows, cols };
}

/** 同じ月日を年ごとに横に並べ、上下に日、左右に年をたどる(パソコン向け)。見えている所とその少し外だけを描いて読み、
 * 離れた行・列は消す */
export default function DiaryBoard() {
  const scroller = useRef<HTMLDivElement>(null);
  const clock = useRef<HTMLSpanElement>(null);
  const [board, setBoard] = useState<Board | null>(null);
  const { cells, load, clear, remove } = useBoardCells(board);
  // 画面の大きさが変わったら描き直し、基準の時刻を左の真ん中に戻す
  const [, setResized] = useState(0);
  const anchor = useRef<Anchor>({ row: 0, col: 0, y: 0, x: 0 });
  // 基準の時刻に合わせて自分で動かしたスクロールの位置。この位置で来た scroll は、人が動かしたものではない
  const placed = useRef({ top: -1, left: -1 });

  /** `day` を 0 行目にし、その日の `ratio`(0 時が 0、24 時が 1)を基準の時刻にして出し直す */
  const reset = useCallback(
    (day: string, ratio: number) => {
      clear();
      anchor.current = { row: 0, col: 0, y: ratio, x: 0 };
      setBoard(newBoard(day));
    },
    [clear],
  );
  const resetToNow = useCallback(() => reset(today(), (Date.now() - dayStartMs(today())) / DAY_MS), [reset]);

  // 他の画面から `/?day=YYYY-MM-DD` で開かれたら、その日の正午を基準にする。今はブラウザで開いてから決める(DiaryWeeks と同じ)
  useEffect(() => {
    const day = new URLSearchParams(window.location.search).get("day");
    if (isDay(day)) reset(day, 0.5);
    else resetToNow();
  }, [reset, resetToNow]);

  useEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setResized((n) => n + 1));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const showClock = () => {
    if (clock.current && board) clock.current.textContent = T.diary.reference(dateTime(new Date(anchorTime(board.origin, anchor.current)).toISOString()));
  };

  useLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    placeAnchor(el, anchor.current);
    placed.current = { top: el.scrollTop, left: el.scrollLeft };
    showClock();
  });

  // 足した行や読み終えた日記で余白が変わるので、描き直すたびに確かめる
  const adjust = () => {
    const el = scroller.current;
    if (!el || !board) return;
    const { rows, cols } = nextWindow(el, board);
    if (!sameSpan(rows, board.rows) || !sameSpan(cols, board.cols)) setBoard({ ...board, rows, cols });
  };
  useEffect(adjust);

  const onScroll = () => {
    const el = scroller.current;
    if (!el) return;
    if (el.scrollTop !== placed.current.top || el.scrollLeft !== placed.current.left) {
      anchor.current = readAnchor(el) ?? anchor.current;
      showClock();
    }
    adjust();
  };

  // 今日の枡を描いていれば、そこだけ読み直す。描いていなければ、今を基準にして出し直す
  const onPosted = () => {
    if (!board) return;
    const day = today();
    const plans: Plan[] = span(board.cols).flatMap((col) => {
      const row = span(board.rows).find((r) => inCell(board.origin, r, col, day));
      return row === undefined ? [] : [{ col, rows: { first: row, last: row } }];
    });
    if (plans.length > 0) load(board, plans);
    else resetToNow();
  };

  const now = today();
  return (
    <div className="diary-board-page">
      <div className="toolbar">
        <button
          type="button"
          className="ghost"
          onClick={() => {
            window.history.replaceState(null, "", window.location.pathname);
            resetToNow();
          }}
        >
          {T.diary.now}
        </button>
        <span className="reference" ref={clock} />
        <span className="hint">{T.diary.boardHint}</span>
      </div>
      <div className="diary-board" ref={scroller} onScroll={onScroll}>
        {board === null && <div className="status info">{T.loading}</div>}
        {board &&
          span(board.rows).map((row) => (
            <div key={row} className="diary-board-row" data-row={row}>
              {span(board.cols).map((col) => {
                const start = cellStart(board.origin, row, col);
                const end = cellEnd(board.origin, row, col);
                return (
                  <BoardCell
                    key={col}
                    col={col}
                    cellKey={cellKey(row, col)}
                    start={start}
                    end={end}
                    when={end < now ? "past" : start > now ? "future" : "today"}
                    cell={cells[cellKey(row, col)]}
                    onDeleted={remove}
                  />
                );
              })}
            </div>
          ))}
      </div>
      <DiaryInput onPosted={onPosted} />
    </div>
  );
}
