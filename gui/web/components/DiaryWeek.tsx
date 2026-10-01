"use client";

import { useEffect, useState } from "react";
import DiaryCard from "@/components/DiaryCard";
import { listDiaries, type DiaryRecord } from "@/lib/api";
import { addDays, monthDay } from "@/lib/date";
import { T } from "@/lib/text";

// `endDay` を含めて、その前の何日ぶんを並べるか
const SPAN_DAYS = 7;

type Props = {
  endDay: string;
  // 増えたら読み直す(日記を足したあと)
  reload: number;
};

/** `endDay` までの一週間の日記を、古い順に縦に並べる */
export default function DiaryWeek({ endDay, reload }: Props) {
  const startDay = addDays(endDay, -SPAN_DAYS);
  const [diaries, setDiaries] = useState<DiaryRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    listDiaries(startDay, endDay)
      .then((found) => current && setDiaries(found))
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, [startDay, endDay, reload]);

  return (
    <section className="diary-week">
      <h2>{T.diary.span(endDay.slice(0, 4), monthDay(startDay), monthDay(endDay))}</h2>
      {error && <div className="status error">{T.cannotReachApi(error)}</div>}
      {diaries === null && !error && <div className="status info">{T.loading}</div>}
      {diaries?.length === 0 && <div className="empty">{T.diary.empty}</div>}
      {diaries?.map((diary) => <DiaryCard key={`${diary.id}-${diary.comments.length}`} diary={diary} />)}
    </section>
  );
}
