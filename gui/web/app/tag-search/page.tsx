"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import DiaryCard from "@/components/DiaryCard";
import TagEditor from "@/components/TagEditor";
import { listTaggedDiaries, listTags, type DiaryRecord, type TagUsage } from "@/lib/api";
import { dayOf } from "@/lib/date";
import { T } from "@/lib/text";

/** 今あるタグを押して選び(いくつでも)、選んだタグのどれかが付いた日記を新しい順に並べる。
 * 一覧の右の「Edit」で、タグを作る・名前を変える・消す表に切り替える。
 * `/tag-search?tag=ID&tag=ID` はそのタグを選んだところから出す */
export default function TagSearch() {
  const [usages, setUsages] = useState<TagUsage[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [chosenIds, setChosenIds] = useState<number[]>([]);
  const [editing, setEditing] = useState(false);
  // タグを書き換えるたびに足し、タグの一覧と、選んだタグの日記を読み直す(名前・数が変わり、消したタグは日記から外れている)
  const [reload, setReload] = useState(0);
  const loaded = useRef(false);

  useEffect(() => {
    let current = true;
    listTags()
      .then((found) => {
        if (!current) return;
        setUsages(found);
        const ids = found.map((usage) => usage.tag.id);
        // アドレスは開いたときに一度だけ読む(下で選んだタグを書き戻すので)。読み直したときは、消したタグを選びから外す
        if (loaded.current) {
          setChosenIds((chosen) => chosen.filter((id) => ids.includes(id)));
        } else {
          const opened = new URLSearchParams(window.location.search).getAll("tag");
          setChosenIds(ids.filter((id) => opened.includes(String(id))));
          loaded.current = true;
        }
      })
      .catch((e) => current && setListError(e.message));
    return () => {
      current = false;
    };
  }, [reload]);

  // 「Open week」から戻ったときに同じタグを出せるよう、選んだタグをアドレスに残す
  useEffect(() => {
    if (usages === null) return;
    const query = new URLSearchParams(chosenIds.map((id) => ["tag", String(id)])).toString();
    window.history.replaceState(null, "", `${window.location.pathname}${query ? `?${query}` : ""}`);
  }, [usages, chosenIds]);

  const toggle = (id: number) =>
    setChosenIds((ids) => (ids.includes(id) ? ids.filter((other) => other !== id) : [...ids, id]));

  return (
    <div className="tag-search-page">
      <h1>{T.tagSearch.title}</h1>
      {listError && <div className="status error">{T.cannotReachApi(listError)}</div>}
      {usages === null && !listError && <div className="status info">{T.loading}</div>}
      {usages && (
        <div className="tag-search-tags">
          {editing ? (
            <TagEditor usages={usages} onChanged={() => setReload((count) => count + 1)} />
          ) : (
            <div className="tag-choices">
              {usages.length === 0 && <div className="empty">{T.tagSearch.noTagYet}</div>}
              {usages.map((usage) => (
                <button
                  key={usage.tag.id}
                  type="button"
                  className={`tag-chip ${chosenIds.includes(usage.tag.id) ? "chosen" : ""}`}
                  aria-pressed={chosenIds.includes(usage.tag.id)}
                  onClick={() => toggle(usage.tag.id)}
                >
                  {usage.tag.name}
                </button>
              ))}
              {chosenIds.length > 0 && (
                <button type="button" className="ghost" onClick={() => setChosenIds([])}>{T.tagSearch.clear}</button>
              )}
            </div>
          )}
          <button type="button" className="link edit" onClick={() => setEditing(!editing)}>
            {editing ? T.tagSearch.done : T.tagSearch.edit}
          </button>
        </div>
      )}
      {!editing && <p className="hint">{T.tagSearch.hint}</p>}
      {usages && usages.length > 0 && chosenIds.length === 0 && <div className="empty">{T.tagSearch.choose}</div>}
      {/* 選び直したり、タグを書き換えたりしたら、前の結果を残さず読み直す */}
      {chosenIds.length > 0 && (
        <TaggedDiaries key={`${[...chosenIds].sort((a, b) => a - b).join(",")}/${reload}`} tagIds={chosenIds} />
      )}
    </div>
  );
}

function TaggedDiaries({ tagIds }: { tagIds: number[] }) {
  const [diaries, setDiaries] = useState<DiaryRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    listTaggedDiaries(tagIds)
      .then((found) => current && setDiaries(found))
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, [tagIds]);

  return (
    <>
      {error && <div className="status error">{T.cannotReachApi(error)}</div>}
      {diaries === null && !error && <div className="status info">{T.loading}</div>}
      {diaries && (
        <>
          <h2>{T.tagSearch.found(diaries.length)}</h2>
          {diaries.length === 0 && <div className="empty">{T.tagSearch.none}</div>}
          {diaries.map((diary) => (
            <div key={`${diary.id}-${diary.comments.length}`} className="tag-search-item">
              <div className="meta">
                <Link href={`/?${new URLSearchParams({ day: dayOf(diary.time) })}`}>{T.diary.openWeek}</Link>
              </div>
              <DiaryCard diary={diary} onDeleted={(id) => setDiaries(diaries.filter((other) => other.id !== id))} />
            </div>
          ))}
        </>
      )}
    </>
  );
}
