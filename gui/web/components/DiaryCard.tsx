"use client";

import { useState } from "react";
import Modal from "@/components/Modal";
import { commitComment, type CommentRecord, type DiaryRecord } from "@/lib/api";
import { dateTime } from "@/lib/date";
import { isSubmitKey } from "@/lib/keys";
import { T } from "@/lib/text";

/** 日記一件とコメント。押すとコメントを書くモーダルを開く。足したコメントはこのカードの中だけで並べ直す(週を読み直さない) */
export default function DiaryCard({ diary }: { diary: DiaryRecord }) {
  const [comments, setComments] = useState<CommentRecord[]>(diary.comments);
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = () => {
    setOpen(false);
    setText("");
    setError(null);
  };

  const canSave = !saving && text.trim() !== "";

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const comment = await commitComment(diary.id, text);
      setComments([...comments, comment]);
      close();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <article className="diary-card" onClick={() => setOpen(true)} title={T.comment.open}>
        <div className="time">{dateTime(diary.time)}</div>
        <div className="text">{diary.text}</div>
        {comments.length > 0 && (
          <ul className="comments">
            {comments.map((comment) => (
              <li key={comment.id}>
                <div className="time">{dateTime(comment.time)}</div>
                <div className="text">{comment.text}</div>
              </li>
            ))}
          </ul>
        )}
      </article>
      {open && (
        <Modal
          title={T.comment.title}
          onClose={close}
          actions={
            <>
              <button type="button" onClick={close}>{T.comment.cancel}</button>
              <button type="button" className="primary" disabled={!canSave} onClick={save}>
                {T.comment.save}
              </button>
            </>
          }
        >
          <div className="quote">{diary.text}</div>
          <textarea
            value={text}
            placeholder={T.comment.placeholder}
            autoFocus
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (!isSubmitKey(e)) return;
              e.preventDefault();
              if (canSave) save();
            }}
          />
          {error && <div className="status error">{error}</div>}
        </Modal>
      )}
    </>
  );
}
