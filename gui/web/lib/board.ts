import { addDays, addYears, today } from "@/lib/date";

// 日記の盤(components/DiaryBoard.tsx)の行・列と日付の対応。行 r は `origin` から r 日後、列 c は c 年前

export const DAY_MS = 24 * 60 * 60 * 1000;
// 上下へは一度に一週間ぶん足す(日の行は低いので、一行ずつだと描き直しの回数が増える)
export const ROWS_PER_STEP = 7;

export type Span = { first: number; last: number };
/** `rows` と `cols` が描いている範囲。`minCol` は今年の列 */
export type Board = { origin: string; rows: Span; cols: Span; minCol: number };
/** 列 `col` の `rows` の日を読む予定 */
export type Plan = { col: number; rows: Span };

export const span = ({ first, last }: Span) => Array.from({ length: Math.max(0, last - first + 1) }, (_, i) => first + i);
export const inSpan = (n: number, { first, last }: Span) => first <= n && n <= last;
export const sameSpan = (a: Span, b: Span) => a.first === b.first && a.last === b.last;

export const cellKey = (row: number, col: number) => `${row}:${col}`;
export const parseKey = (key: string) => key.split(":").map(Number) as [number, number];

export const cellEnd = (origin: string, row: number, col: number) => addYears(addDays(origin, row), -col);
/** 年をずらすと 2/29 の前後で日が飛んだり重なったりするので、一つ前の行の終わりの次の日から始める。
 * うるう年の列では 2/29 が 3/1 の枡に入り、うるう年から見た列では 3/1 の枡が空になる(始めが終わりより後) */
export const cellStart = (origin: string, row: number, col: number) => addDays(cellEnd(origin, row - 1, col), 1);

export const inCell = (origin: string, row: number, col: number, day: string) =>
  cellStart(origin, row, col) <= day && day <= cellEnd(origin, row, col);

/** 日本時間の `day` の 0 時 */
export const dayStartMs = (day: string) => Date.parse(`${day}T00:00:00+09:00`);

/** `day` を 0 行目にして、その前後一週間と今年・去年から描き始める */
export function newBoard(day: string): Board {
  return {
    origin: day,
    rows: { first: -ROWS_PER_STEP, last: ROWS_PER_STEP },
    cols: { first: 0, last: 1 },
    // まだ来ていない年には日記が無いので、左へは今年の列までしか足さない
    minCol: Number(day.slice(0, 4)) - Number(today().slice(0, 4)),
  };
}

/** 描いている枡のうち `requested` でない所を、列ごとにひと続きの範囲にまとめる */
export function missingPlans(b: Board, requested: (key: string) => boolean): Plan[] {
  const plans: Plan[] = [];
  for (const col of span(b.cols)) {
    let first: number | null = null;
    for (const row of [...span(b.rows), b.rows.last + 1]) {
      const missing = row <= b.rows.last && !requested(cellKey(row, col));
      if (missing && first === null) first = row;
      if (!missing && first !== null) {
        plans.push({ col, rows: { first, last: row - 1 } });
        first = null;
      }
    }
  }
  return plans;
}
