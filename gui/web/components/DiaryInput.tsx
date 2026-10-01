"use client";

import { useState } from "react";
import FutureSendModal from "@/components/FutureSendModal";
import { commitDiary } from "@/lib/api";
import { isSubmitKey } from "@/lib/keys";
import { T } from "@/lib/text";

/** 日記を書く欄。書いた時刻は API が決める。未来へ送るモーダルもここから開く */
export default function DiaryInput({ onPosted }: { onPosted: () => void }) {
  const [text, setText] = useState("");
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [future, setFuture] = useState(false);

  const canPost = !posting && text.trim() !== "";

  const post = async () => {
    setPosting(true);
    setError(null);
    try {
      await commitDiary(text);
      setText("");
      onPosted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="diary-input">
      <textarea
        value={text}
        rows={Math.max(2, text.split("\n").length)}
        placeholder={T.diary.placeholder}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (!isSubmitKey(e)) return;
          e.preventDefault();
          if (canPost) post();
        }}
      />
      <button type="button" onClick={() => setFuture(true)}>{T.future.open}</button>
      <button type="button" className="primary" disabled={!canPost} onClick={post}>
        {posting ? T.diary.posting : T.diary.post}
      </button>
      {error && <div className="status error">{error}</div>}
      {future && <FutureSendModal initialText={text} onSent={() => setText("")} onClose={() => setFuture(false)} />}
    </div>
  );
}
