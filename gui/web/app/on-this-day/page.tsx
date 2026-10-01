"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DiaryCard from "@/components/DiaryCard";
import { listOnThisDay, type OnThisDayYear } from "@/lib/api";
import { addDays, monthDay, today } from "@/lib/date";
import { T } from "@/lib/text";

// 同じ月日の前後に何日まで含めるか(API の上限は 30 日)
const AROUND_OPTIONS = [0, 1, 3, 7];

/** 同じ月日の日記を、書き始めた年から今年まで、年ごとに縦に並べる */
export default function OnThisDay() {
  // next build が書き出す HTML に建てた日の日付が残らないよう、今日はブラウザで開いてから決める
  const [day, setDay] = useState<string | null>(null);
  const [aroundDays, setAroundDays] = useState(0);
  const [years, setYears] = useState<OnThisDayYear[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setDay(today()), []);

  useEffect(() => {
    if (day === null) return;
    let current = true;
    setYears(null);
    setError(null);
    listOnThisDay(day, aroundDays)
      .then((found) => current && setYears(found))
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, [day, aroundDays]);

  if (day === null) return <div className="status info">{T.loading}</div>;
  const thisYear = Number(day.slice(0, 4));

  const removeDiary = (id: number) =>
    setYears((found) => found?.map((year) => ({ ...year, diaries: year.diaries.filter((diary) => diary.id !== id) })) ?? null);

  return (
    <div className="on-this-day-page">
      <div className="toolbar">
        <button type="button" onClick={() => setDay(addDays(day, -1))}>{T.onThisDay.dayEarlier}</button>
        <button type="button" onClick={() => setDay(addDays(day, 1))}>{T.onThisDay.dayLater}</button>
        <button type="button" className="ghost" onClick={() => setDay(today())}>{T.onThisDay.today}</button>
        <label className="inline-field">
          {T.onThisDay.around}
          <select value={aroundDays} onChange={(e) => setAroundDays(Number(e.target.value))}>
            {AROUND_OPTIONS.map((days) => (
              <option key={days} value={days}>{T.onThisDay.aroundOption(days)}</option>
            ))}
          </select>
        </label>
      </div>
      <h1>{T.onThisDay.heading(monthDay(day))}</h1>
      {error && <div className="status error">{T.cannotReachApi(error)}</div>}
      {years === null && !error && <div className="status info">{T.loading}</div>}
      {years?.length === 0 && <div className="empty">{T.onThisDay.noDiaryYet}</div>}
      {years?.map((year) => (
        <section key={year.year} className="on-this-day-year">
          <h2>
            {T.onThisDay.yearsAgo(year.year, thisYear - year.year)}
            {aroundDays > 0 && (
              <span className="span">{T.onThisDay.span(monthDay(year.start_date), monthDay(year.end_date))}</span>
            )}
            <Link className="open-week" href={`/?${new URLSearchParams({ day: addDays(year.start_date, aroundDays) })}`}>
              {T.diary.openWeek}
            </Link>
          </h2>
          {year.diaries.length === 0 && <div className="empty">{T.diary.empty}</div>}
          {year.diaries.map((diary) => (
            <DiaryCard key={`${diary.id}-${diary.comments.length}`} diary={diary} onDeleted={removeDiary} />
          ))}
        </section>
      ))}
    </div>
  );
}
