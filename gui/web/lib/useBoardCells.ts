import { useCallback, useEffect, useRef, useState } from "react";
import { listDiariesInSpans, type DiaryRecord } from "@/lib/api";
import { cellEnd, cellKey, cellStart, inCell, inSpan, missingPlans, parseKey, span, type Board, type Plan } from "@/lib/board";
import { dayOf, today } from "@/lib/date";

// 読み込みの予定(描いている枡のうち、まだ読んでいない所)を立てるのは、この間隔(ms)に一度まで。
// 予定は一度のリクエストにまとめるので、スクロールし続けても Lambda を呼ぶのは 1 秒に一度で済む
const PLAN_INTERVAL = 1000;
// 描き始めや足し消しの直後は描く範囲が続けて変わるので、落ち着くのを少し待ってから予定を立てる
const PLAN_SETTLE = 100;
// 一度に頼める範囲の数(API の ListDiariesInSpans の上限)。越えた分は次の予定に回る
const MAX_SPANS = 100;

export type Cell = { diaries: DiaryRecord[] } | { error: string };

/** 盤の描いている枡の日記。描く範囲が変わったら、まだ読んでいない枡を予定にまとめて一度に読み、範囲から外れた枡は捨てる
 * (戻ってきたら読み直す) */
export function useBoardCells(board: Board | null) {
  const [cells, setCells] = useState<Record<string, Cell>>({});
  // 読みに出した枡と、その読み込みの番号。番号が替わった(消して出し直した)枡には、前の読み込みの結果を書かない
  const requested = useRef(new Map<string, number>());
  const nextRequest = useRef(0);
  const latest = useRef<Board | null>(null);
  const planTimer = useRef<number | null>(null);
  const lastPlan = useRef(0);

  /** 予定の枡を、一度のリクエストで読む */
  const load = useCallback((b: Board, plans: Plan[]) => {
    const id = nextRequest.current++;
    for (const plan of plans) for (const row of span(plan.rows)) requested.current.set(cellKey(row, plan.col), id);
    /** `targets` の枡のうち、この読み込みのあとで捨てたり読み直しに出したりしていないものに書く */
    const settle = (targets: Plan[], cellOf: (row: number, plan: Plan, index: number) => Cell) => {
      if (targets.length === 0) return;
      setCells((prev) => {
        const next = { ...prev };
        targets.forEach((plan, index) => {
          for (const row of span(plan.rows)) {
            const key = cellKey(row, plan.col);
            if (requested.current.get(key) === id) next[key] = cellOf(row, plan, index);
          }
        });
        return next;
      });
    };
    // まだ来ていない日は、読まずに空にする
    const day = today();
    const past = plans.filter((plan) => cellStart(b.origin, plan.rows.first, plan.col) <= day);
    settle(plans.filter((plan) => !past.includes(plan)), () => ({ diaries: [] }));
    if (past.length === 0) return;
    listDiariesInSpans(past.map((plan) => ({
      start_date: cellStart(b.origin, plan.rows.first, plan.col),
      end_date: cellEnd(b.origin, plan.rows.last, plan.col),
    })))
      .then((found) => {
        const dated = found.map(({ diaries }) => diaries.map((diary) => ({ day: dayOf(diary.time), diary })));
        settle(past, (row, plan, index) => ({
          diaries: dated[index].filter(({ day }) => inCell(b.origin, row, plan.col, day)).map(({ diary }) => diary),
        }));
      })
      .catch((e: Error) => settle(past, () => ({ error: e.message })));
  }, []);

  const planFetch = useCallback(() => {
    planTimer.current = null;
    lastPlan.current = Date.now();
    const b = latest.current;
    if (!b) return;
    const plans = missingPlans(b, (key) => requested.current.has(key));
    if (plans.length > 0) load(b, plans.slice(0, MAX_SPANS));
  }, [load]);

  useEffect(() => {
    latest.current = board;
    if (!board) return;
    const outside = (key: string) => {
      const [row, col] = parseKey(key);
      return !inSpan(row, board.rows) || !inSpan(col, board.cols);
    };
    for (const key of [...requested.current.keys()]) if (outside(key)) requested.current.delete(key);
    setCells((prev) => (Object.keys(prev).some(outside) ? Object.fromEntries(Object.entries(prev).filter(([key]) => !outside(key))) : prev));
    if (planTimer.current === null) {
      planTimer.current = window.setTimeout(planFetch, Math.max(PLAN_SETTLE, lastPlan.current + PLAN_INTERVAL - Date.now()));
    }
  }, [board, planFetch]);

  useEffect(() => () => {
    if (planTimer.current !== null) window.clearTimeout(planTimer.current);
  }, []);

  /** 盤を出し直す前に、読んだ日記と読み込み中の印をすべて捨てる */
  const clear = useCallback(() => {
    requested.current.clear();
    setCells({});
  }, []);

  const remove = useCallback((key: string, diaryId: number) => {
    setCells((prev) => {
      const cell = prev[key];
      if (!cell || !("diaries" in cell)) return prev;
      return { ...prev, [key]: { diaries: cell.diaries.filter((diary) => diary.id !== diaryId) } };
    });
  }, []);

  return { cells, load, clear, remove };
}
