"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DiaryCard from "@/components/DiaryCard";
import { commitDiary, listDiaries, type DiaryRecord } from "@/lib/api";
import { addDays, nowMinute, today } from "@/lib/date";
import { isSubmitKey } from "@/lib/keys";
import { T } from "@/lib/text";

// 日記は一日の終わりに書くことが多いので、書き足す日記もその頃に置く
const DEFAULT_TIME = "21:00";

/** 書かなかった過去の日に、日付と時刻を選んで日記を書き足す。選んだ日に既にある日記も並べる */
export default function Past() {
  // next build が書き出す HTML に建てた日の日付が残らないよう、日付はブラウザで開いてから決める
  const [day, setDay] = useState<string | null>(null);
  const [time, setTime] = useState(DEFAULT_TIME);
  const [text, setText] = useState("");
  const [posting, setPosting] = useState(false);
  const [postedDay, setPostedDay] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [diaries, setDiaries] = useState<DiaryRecord[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => setDay(addDays(today(), -1)), []);

  useEffect(() => {
    // 日付の欄を消した間("")は読まない
    if (!day) return;
    let current = true;
    setDiaries(null);
    setListError(null);
    listDiaries(day, day)
      .then((found) => current && setDiaries(found))
      .catch((e) => current && setListError(e.message));
    return () => {
      current = false;
    };
  }, [day, reload]);

  if (day === null) return <div className="status info">{T.loading}</div>;
  const inFuture = `${day}T${time}` > nowMinute();
  const canPost = !posting && text.trim() !== "" && day !== "" && time !== "" && !inFuture;

  const post = async () => {
    setPosting(true);
    setError(null);
    try {
      await commitDiary(text, `${day}T${time}:00+09:00`);
      setText("");
      setPostedDay(day);
      setReload(reload + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="past-page">
      <h1>{T.past.title}</h1>
      <p className="hint">{T.past.hint}</p>
      <div className="toolbar">
        <label className="inline-field">
          {T.past.day}
          <input type="date" max={today()} value={day} onChange={(e) => setDay(e.target.value)} />
        </label>
        <label className="inline-field">
          {T.past.time}
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} />
        </label>
      </div>
      <div className="past-input">
        <textarea
          value={text}
          rows={Math.max(4, text.split("\n").length)}
          placeholder={T.past.placeholder}
          onChange={(e) => {
            setText(e.target.value);
            setPostedDay(null);
          }}
          onKeyDown={(e) => {
            if (!isSubmitKey(e)) return;
            e.preventDefault();
            if (canPost) post();
          }}
        />
        <button type="button" className="primary" disabled={!canPost} onClick={post}>
          {posting ? T.diary.posting : T.diary.post}
        </button>
        {inFuture && <div className="status error">{T.past.notFuture}</div>}
        {postedDay && <div className="status ok">{T.past.posted(postedDay)}</div>}
        {error && <div className="status error">{error}</div>}
      </div>
      {day !== "" && (
        <>
          <h2>
            {T.past.onDay(day)}
            <Link className="open-week" href={`/?${new URLSearchParams({ day })}`}>{T.diary.openWeek}</Link>
          </h2>
          {listError && <div className="status error">{T.cannotReachApi(listError)}</div>}
          {diaries === null && !listError && <div className="status info">{T.loading}</div>}
          {diaries?.length === 0 && <div className="empty">{T.diary.empty}</div>}
          {diaries?.map((diary) => (
            <DiaryCard
              key={`${diary.id}-${diary.comments.length}`}
              diary={diary}
              onDeleted={(id) => setDiaries(diaries.filter((other) => other.id !== id))}
            />
          ))}
        </>
      )}
    </div>
  );
}
