"use client";

import { memo } from "react";
import DiaryCard from "@/components/DiaryCard";
import { weekday } from "@/lib/date";
import { T } from "@/lib/text";
import type { Cell } from "@/lib/useBoardCells";

type Props = {
  col: number;
  cellKey: string;
  start: string;
  end: string;
  when: "past" | "today" | "future";
  cell: Cell | undefined;
  onDeleted: (cellKey: string, diaryId: number) => void;
};

const dayLabel = (day: string) => T.diary.day(day.replaceAll("-", "/"), T.diary.weekdays[weekday(day)]);

/** 盤(components/DiaryBoard.tsx)の一枡。ある年の `start` から `end` の日記。盤の行・列が増えたり減ったりするたびに
 * 全部を描き直さないよう、読み終えた枡だけを描き直す */
const BoardCell = memo(function BoardCell({ col, cellKey, start, end, when, cell, onDeleted }: Props) {
  return (
    <section className={`diary-board-cell ${when}`} data-col={col}>
      {start <= end && <div className="day">{start === end ? dayLabel(end) : T.diary.days(dayLabel(start), dayLabel(end))}</div>}
      {cell === undefined && start <= end && <div className="loading">{T.loading}</div>}
      {cell && "error" in cell && <div className="status error">{T.cannotReachApi(cell.error)}</div>}
      {cell &&
        "diaries" in cell &&
        cell.diaries.map((diary) => (
          <DiaryCard key={`${diary.id}-${diary.comments.length}`} diary={diary} onDeleted={(id) => onDeleted(cellKey, id)} />
        ))}
    </section>
  );
});

export default BoardCell;
