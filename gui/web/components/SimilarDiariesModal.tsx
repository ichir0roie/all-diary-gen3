"use client";

import Modal from "@/components/Modal";
import type { SimilarDiaries } from "@/lib/api";
import { dateTime, dayOf } from "@/lib/date";
import { T } from "@/lib/text";

type Props = {
  similar: SimilarDiaries;
  // その日記の週を開く
  onJump: (day: string) => void;
  onClose: () => void;
};

/** 書いている日記に似た日記の一覧。似ている順 */
export default function SimilarDiariesModal({ similar, onJump, onClose }: Props) {
  return (
    <Modal title={T.similar.title(similar.total)} onClose={onClose}>
      {similar.total > similar.diaries.length && (
        <p className="hint">{T.similar.more(similar.diaries.length, similar.total)}</p>
      )}
      <ul className="similar-list">
        {similar.diaries.map(({ diary, score }) => (
          <li key={diary.id}>
            <div className="time">
              {dateTime(diary.time)}
              <span className="badge">{T.similar.score(score)}</span>
              <button
                type="button"
                className="ghost link"
                onClick={() => {
                  onJump(dayOf(diary.time));
                  onClose();
                }}
              >
                {T.diary.openWeek}
              </button>
            </div>
            <div className="text">{diary.text}</div>
          </li>
        ))}
      </ul>
    </Modal>
  );
}
