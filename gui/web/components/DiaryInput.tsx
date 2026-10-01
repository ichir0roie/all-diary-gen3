"use client";

import { useEffect, useState } from "react";
import FutureSendModal from "@/components/FutureSendModal";
import SimilarDiariesModal from "@/components/SimilarDiariesModal";
import { commitDiary, searchSimilarDiaries, type SimilarDiaries } from "@/lib/api";
import { isSubmitKey } from "@/lib/keys";
import { T } from "@/lib/text";

// 打つ手が止まってから似た日記を探すまで。打つたびに API を呼ばないようにする
const SEARCH_DELAY_MS = 600;

type Props = {
  onPosted: () => void;
  // 似た日記の週を開く
  onJump: (day: string) => void;
};

/** 日記を書く欄。書いた時刻は API が決める。書いている文章に似た日記の数を右下に出し、押すと一覧を開く */
export default function DiaryInput({ onPosted, onJump }: Props) {
  const [text, setText] = useState("");
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [similar, setSimilar] = useState<SimilarDiaries | null>(null);
  const [dialog, setDialog] = useState<"similar" | "future" | null>(null);

  useEffect(() => {
    if (text.trim().length < 2) {
      setSimilar(null);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      searchSimilarDiaries(text, controller.signal)
        .then(setSimilar)
        // 似た日記は書く助けにすぎないので、探せなくても書く邪魔をしない(数を出さないだけ)
        .catch(() => controller.signal.aborted || setSimilar(null));
    }, SEARCH_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [text]);

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
      <div className="editor">
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
        {similar !== null && similar.total > 0 && (
          <button
            type="button"
            className="similar-count"
            title={T.similar.hint(similar.total)}
            onClick={() => setDialog("similar")}
          >
            {T.similar.count(similar.total)}
          </button>
        )}
      </div>
      <button type="button" onClick={() => setDialog("future")}>{T.future.open}</button>
      <button type="button" className="primary" disabled={!canPost} onClick={post}>
        {posting ? T.diary.posting : T.diary.post}
      </button>
      {error && <div className="status error">{error}</div>}
      {dialog === "similar" && similar && (
        <SimilarDiariesModal similar={similar} onJump={onJump} onClose={() => setDialog(null)} />
      )}
      {dialog === "future" && (
        <FutureSendModal initialText={text} onSent={() => setText("")} onClose={() => setDialog(null)} />
      )}
    </div>
  );
}
