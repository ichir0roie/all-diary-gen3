"use client";

import { useState } from "react";
import Modal from "@/components/Modal";
import { T } from "@/lib/text";

type Props = {
  title: string;
  message: string;
  quote?: string;
  confirmLabel: string;
  onConfirm: () => Promise<void>;
  onClose: () => void;
};

/** 消す前に確かめるモーダル */
export default function ConfirmDialog({ title, message, quote, confirmLabel, onConfirm, onClose }: Props) {
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirm = async () => {
    setWorking(true);
    setError(null);
    try {
      await onConfirm();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setWorking(false);
    }
  };

  return (
    <Modal
      title={title}
      onClose={onClose}
      actions={
        <>
          <button type="button" onClick={onClose}>{T.diary.cancel}</button>
          <button type="button" className="danger" disabled={working} onClick={confirm}>
            {confirmLabel}
          </button>
        </>
      }
    >
      <p>{message}</p>
      {quote !== undefined && <div className="quote">{quote}</div>}
      {error && <div className="status error">{error}</div>}
    </Modal>
  );
}
