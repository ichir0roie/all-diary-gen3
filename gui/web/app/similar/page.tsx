"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import DiaryCard from "@/components/DiaryCard";
import { listSimilarDiaries, readDiary, searchSimilarDiaries, type DiaryRecord, type SimilarDiaries } from "@/lib/api";
import { dayOf } from "@/lib/date";
import { T } from "@/lib/text";

// 打つ手が止まってから探すまで。打つたびに API を呼ばないようにする
const SEARCH_DELAY_MS = 600;

/** 似た日記。`/similar?diary=ID`(日記のメニューの「Similar diaries」から来る)はその日記に似た日記を、
 * `/similar` は打った文章に似た日記を、似ている順に並べる */
export default function Similar() {
  return (
    <div className="similar-page">
      <h1>{T.similar.title}</h1>
      {/* useSearchParams は Suspense の中で読む(next build が、読む前の形を書き出せるように) */}
      <Suspense fallback={<div className="status info">{T.loading}</div>}>
        <SimilarView />
      </Suspense>
    </div>
  );
}

function SimilarView() {
  const raw = useSearchParams().get("diary");
  const diaryId = raw !== null && /^\d+$/.test(raw) ? Number(raw) : null;
  // 似た日記の「Similar diaries」から別の日記へ移ったときは、前の日記の結果を残さず読み直す
  return diaryId === null ? <TextSearch /> : <FromDiary key={diaryId} diaryId={diaryId} />;
}

function FromDiary({ diaryId }: { diaryId: number }) {
  const router = useRouter();
  const [source, setSource] = useState<DiaryRecord | null>(null);
  const [similar, setSimilar] = useState<SimilarDiaries | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    Promise.all([readDiary(diaryId), listSimilarDiaries(diaryId)])
      .then(([found, near]) => {
        if (!current) return;
        setSource(found);
        setSimilar(near);
      })
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, [diaryId]);

  return (
    <>
      <h2>
        {T.similar.source}
        <Link className="back" href="/similar">{T.similar.backToSearch}</Link>
      </h2>
      {error && <div className="status error">{T.cannotReachApi(error)}</div>}
      {source === null && !error && <div className="status info">{T.loading}</div>}
      {source && <DiaryCard diary={source} onDeleted={() => router.replace("/similar")} />}
      {similar && <SimilarList similar={similar} onChange={setSimilar} />}
    </>
  );
}

function TextSearch() {
  const [text, setText] = useState("");
  const [similar, setSimilar] = useState<SimilarDiaries | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (text.trim().length < 2) {
      setSimilar(null);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setError(null);
      searchSimilarDiaries(text, controller.signal)
        .then(setSimilar)
        .catch((e) => controller.signal.aborted || setError(e.message));
    }, SEARCH_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [text]);

  return (
    <>
      <div className="field search">
        <label htmlFor="similar-text">{T.similar.searchLabel}</label>
        <textarea
          id="similar-text"
          value={text}
          placeholder={T.similar.searchPlaceholder}
          autoFocus
          onChange={(e) => setText(e.target.value)}
        />
      </div>
      <p className="hint">{T.similar.hint}</p>
      {error && <div className="status error">{T.cannotReachApi(error)}</div>}
      {similar && <SimilarList similar={similar} onChange={setSimilar} />}
    </>
  );
}

/** 似ている順の一覧。それぞれに一致の割合と、その週を開くリンクを添える */
function SimilarList({ similar, onChange }: { similar: SimilarDiaries; onChange: (similar: SimilarDiaries) => void }) {
  const removeDiary = (id: number) =>
    onChange({ total: similar.total - 1, diaries: similar.diaries.filter(({ diary }) => diary.id !== id) });

  return (
    <>
      <h2>{T.similar.found(similar.total)}</h2>
      {similar.total === 0 && <div className="empty">{T.similar.none}</div>}
      {similar.total > similar.diaries.length && (
        <p className="hint">{T.similar.more(similar.diaries.length, similar.total)}</p>
      )}
      {similar.diaries.map(({ diary, score }) => (
        <div key={`${diary.id}-${diary.comments.length}`} className="similar-item">
          <div className="meta">
            <span className="badge">{T.similar.score(score)}</span>
            <Link href={`/?${new URLSearchParams({ day: dayOf(diary.time) })}`}>{T.diary.openWeek}</Link>
          </div>
          <DiaryCard diary={diary} onDeleted={removeDiary} />
        </div>
      ))}
    </>
  );
}
