"use client";

import { useRouter } from "next/navigation";
import { useState, type MouseEvent } from "react";
import ConfirmDialog from "@/components/ConfirmDialog";
import PopupMenu, { type MenuItem } from "@/components/PopupMenu";
import TextDialog from "@/components/TextDialog";
import {
  commitComment,
  deleteComment,
  deleteDiary,
  updateComment,
  updateDiary,
  type CommentRecord,
  type DiaryRecord,
} from "@/lib/api";
import { dateOnly, dateTime } from "@/lib/date";
import { T } from "@/lib/text";

type Dialog =
  | { kind: "comment" }
  | { kind: "editDiary" }
  | { kind: "deleteDiary" }
  | { kind: "editComment"; comment: CommentRecord }
  | { kind: "deleteComment"; comment: CommentRecord };

type Props = {
  diary: DiaryRecord;
  // 消したあと、並べている側が一覧から除く
  onDeleted: (diaryId: number) => void;
};

/** 日記一件とコメント。日記を押すと「コメント・似た日記・書き直す・消す」、コメントを押すと「書き直す・消す」のメニューを開く。
 * 書き足し・書き直しはこのカードの中だけで反映する(週を読み直さない) */
export default function DiaryCard({ diary: initial, onDeleted }: Props) {
  const router = useRouter();
  const [diary, setDiary] = useState(initial);
  const [comments, setComments] = useState<CommentRecord[]>(initial.comments);
  const [menu, setMenu] = useState<{ x: number; y: number; items: MenuItem[] } | null>(null);
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const close = () => setDialog(null);

  // 文字を選ぼうとしてドラッグしたときは、メニューを開かない
  const openMenu = (e: MouseEvent, items: MenuItem[]) => {
    e.stopPropagation();
    if (window.getSelection()?.toString()) return;
    setMenu({ x: e.clientX, y: e.clientY, items });
  };

  const diaryItems: MenuItem[] = [
    { label: T.diary.comment, onSelect: () => setDialog({ kind: "comment" }) },
    { label: T.diary.similar, onSelect: () => router.push(`/similar?${new URLSearchParams({ diary: String(diary.id) })}`) },
    { label: T.diary.edit, onSelect: () => setDialog({ kind: "editDiary" }) },
    { label: T.diary.delete, onSelect: () => setDialog({ kind: "deleteDiary" }), danger: true },
  ];
  const commentItems = (comment: CommentRecord): MenuItem[] => [
    { label: T.diary.edit, onSelect: () => setDialog({ kind: "editComment", comment }) },
    { label: T.diary.delete, onSelect: () => setDialog({ kind: "deleteComment", comment }), danger: true },
  ];

  return (
    <>
      <article className="diary-card" onClick={(e) => openMenu(e, diaryItems)} title={T.diary.menu}>
        <div className="time">
          {dateTime(diary.time)}
          {diary.written_at && <span className="badge">{T.diary.fromPast(dateOnly(diary.written_at))}</span>}
        </div>
        <div className="text">{diary.text}</div>
        {comments.length > 0 && (
          <ul className="comments">
            {comments.map((comment) => (
              <li key={comment.id} onClick={(e) => openMenu(e, commentItems(comment))}>
                <div className="time">{dateTime(comment.time)}</div>
                <div className="text">{comment.text}</div>
              </li>
            ))}
          </ul>
        )}
      </article>
      {menu && <PopupMenu {...menu} onClose={() => setMenu(null)} />}
      {dialog?.kind === "comment" && (
        <TextDialog
          title={T.comment.title}
          quote={diary.text}
          placeholder={T.comment.placeholder}
          onClose={close}
          onSave={async (text) => {
            const comment = await commitComment(diary.id, text);
            setComments([...comments, comment]);
          }}
        />
      )}
      {dialog?.kind === "editDiary" && (
        <TextDialog
          title={T.diary.editTitle}
          initialText={diary.text}
          onClose={close}
          onSave={async (text) => setDiary(await updateDiary(diary.id, text))}
        />
      )}
      {dialog?.kind === "deleteDiary" && (
        <ConfirmDialog
          title={T.diary.deleteTitle}
          message={T.diary.deleteConfirm(comments.length)}
          quote={diary.text}
          confirmLabel={T.diary.delete}
          onClose={close}
          onConfirm={async () => {
            await deleteDiary(diary.id);
            onDeleted(diary.id);
          }}
        />
      )}
      {dialog?.kind === "editComment" && (
        <TextDialog
          title={T.comment.editTitle}
          quote={diary.text}
          initialText={dialog.comment.text}
          onClose={close}
          onSave={async (text) => {
            const updated = await updateComment(dialog.comment.id, text);
            setComments(comments.map((comment) => (comment.id === updated.id ? updated : comment)));
          }}
        />
      )}
      {dialog?.kind === "deleteComment" && (
        <ConfirmDialog
          title={T.comment.deleteTitle}
          message={T.comment.deleteConfirm}
          quote={dialog.comment.text}
          confirmLabel={T.diary.delete}
          onClose={close}
          onConfirm={async () => {
            await deleteComment(dialog.comment.id);
            setComments(comments.filter((comment) => comment.id !== dialog.comment.id));
          }}
        />
      )}
    </>
  );
}
