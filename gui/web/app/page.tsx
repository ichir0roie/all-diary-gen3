"use client";

import { useEffect, useState } from "react";
import DiaryInput from "@/components/DiaryInput";
import DiaryWeek from "@/components/DiaryWeek";
import { addDays, addYears, isDay, today } from "@/lib/date";
import { T } from "@/lib/text";

// 同じ週を何年ぶん横に並べるか。狭い画面では今年の一列だけを出す(globals.css)
const YEAR_COUNT = 3;
// 今日より少し先まで入れておくと、書いたばかりの日記が週の真ん中より下に来ず、読み返しやすい
const DAYS_AHEAD = 3;

/** 同じ時期の一週間を、今年・去年・一昨年と横に並べて読み比べる */
export default function Home() {
  const [yearOffset, setYearOffset] = useState(0);
  const [dayOffset, setDayOffset] = useState(DAYS_AHEAD);
  const [reload, setReload] = useState(0);
  // next build が書き出す HTML に建てた日の日付が残らないよう、今日はブラウザで開いてから決める
  const [baseDay, setBaseDay] = useState<string | null>(null);

  // 他の画面(同じ日・ヒートマップ)から `/?day=YYYY-MM-DD` で開かれたら、その日の週を出す
  useEffect(() => {
    const day = new URLSearchParams(window.location.search).get("day");
    setBaseDay(isDay(day) ? day : today());
  }, []);

  const jump = (day: string) => {
    setBaseDay(day);
    setYearOffset(0);
    setDayOffset(DAYS_AHEAD);
    window.history.replaceState(null, "", `/?${new URLSearchParams({ day })}`);
  };

  if (baseDay === null) return <div className="status info">{T.loading}</div>;
  const endDay = addDays(baseDay, dayOffset);
  const columns = Array.from({ length: YEAR_COUNT }, (_, i) => addYears(endDay, yearOffset - i));

  return (
    <div className="diary-page">
      <div className="toolbar">
        <button type="button" onClick={() => setYearOffset(yearOffset + 1)}>{T.diary.yearLater}</button>
        <button type="button" onClick={() => setYearOffset(yearOffset - 1)}>{T.diary.yearEarlier}</button>
        <button type="button" onClick={() => setDayOffset(dayOffset + 7)}>{T.diary.weekLater}</button>
        <button type="button" onClick={() => setDayOffset(dayOffset - 7)}>{T.diary.weekEarlier}</button>
        <button
          type="button"
          className="ghost"
          onClick={() => {
            setBaseDay(today());
            setYearOffset(0);
            setDayOffset(DAYS_AHEAD);
            window.history.replaceState(null, "", "/");
          }}
        >
          {T.diary.today}
        </button>
      </div>
      <div className="diary-years">
        {columns.map((day) => (
          <DiaryWeek key={day} endDay={day} reload={reload} />
        ))}
      </div>
      <DiaryInput
        onJump={jump}
        onPosted={() => {
          // 開いたまま日をまたいだあとでも、書いたばかりの日記が範囲に入るよう、今日を取り直す
          setBaseDay(today());
          setReload(reload + 1);
        }}
      />
    </div>
  );
}
