"use client";

import { useEffect, useState } from "react";
import Modal from "@/components/Modal";
import { listFutureDiaries, sendFutureDiary, type FutureDiaryRecord } from "@/lib/api";
import { addDays, addYears, dateOnly, today } from "@/lib/date";
import { T } from "@/lib/text";

type Props = {
  // 書く欄に書きかけの文章。ここから書き始める
  initialText: string;
  // 送れたら、書く欄を空にする
  onSent: () => void;
  onClose: () => void;
};

/** 日記を未来へ送る。届ける日を選び、その日の 0 時(日本時間)まで封をする。まだ届いていない日記の届く日も出す(本文は出さない) */
export default function FutureSendModal({ initialText, onSent, onClose }: Props) {
  const tomorrow = addDays(today(), 1);
  const [text, setText] = useState(initialText);
  const [deliverOn, setDeliverOn] = useState(addYears(today(), 1));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sentOn, setSentOn] = useState<string | null>(null);
  const [pending, setPending] = useState<FutureDiaryRecord[] | null>(null);

  useEffect(() => {
    let current = true;
    listFutureDiaries()
      .then((found) => current && setPending(found))
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, [sentOn]);

  const canSend = !sending && sentOn === null && text.trim() !== "" && deliverOn >= tomorrow;

  const send = async () => {
    setSending(true);
    setError(null);
    try {
      const sent = await sendFutureDiary(text, deliverOn);
      setSentOn(dateOnly(sent.time));
      onSent();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal
      title={T.future.title}
      onClose={onClose}
      actions={
        <>
          <button type="button" onClick={onClose}>{T.diary.cancel}</button>
          <button type="button" className="primary" disabled={!canSend} onClick={send}>
            {sending ? T.future.sending : T.future.send}
          </button>
        </>
      }
    >
      <p className="hint">{T.future.hint}</p>
      <textarea
        value={text}
        placeholder={T.future.placeholder}
        autoFocus
        disabled={sentOn !== null}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="field">
        <label htmlFor="deliver-on">{T.future.deliverOn}</label>
        <input
          id="deliver-on"
          type="date"
          min={tomorrow}
          value={deliverOn}
          disabled={sentOn !== null}
          onChange={(e) => setDeliverOn(e.target.value)}
        />
      </div>
      {sentOn && <div className="status ok">{T.future.sent(sentOn)}</div>}
      {error && <div className="status error">{error}</div>}
      <div className="field">
        <label>{T.future.pending}</label>
        {pending?.length === 0 && <div className="hint">{T.future.nonePending}</div>}
        {pending && pending.length > 0 && (
          <ul className="pending-list">
            {pending.map((letter) => (
              <li key={letter.id}>{T.future.pendingItem(dateOnly(letter.time), dateOnly(letter.written_at))}</li>
            ))}
          </ul>
        )}
      </div>
    </Modal>
  );
}
