"use client";

import { useState } from "react";
import Modal from "@/components/Modal";
import { isSubmitKey } from "@/lib/keys";
import { T } from "@/lib/text";

type Props = {
  title: string;
  // 何に向けて書くか(コメントなら元の日記)。無ければ出さない
  quote?: string;
  initialText?: string;
  placeholder?: string;
  saveLabel?: string;
  onSave: (text: string) => Promise<void>;
  onClose: () => void;
};

/** 文章を一つ書いて保存するモーダル(コメントを書く・日記やコメントを書き直す)。Ctrl+Enter でも保存する */
export default function TextDialog({ title, quote, initialText = "", placeholder, saveLabel = T.comment.save, onSave, onClose }: Props) {
  const [text, setText] = useState(initialText);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSave = !saving && text.trim() !== "" && text !== initialText;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSave(text);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  };

  return (
    <Modal
      title={title}
      onClose={onClose}
      actions={
        <>
          <button type="button" onClick={onClose}>{T.comment.cancel}</button>
          <button type="button" className="primary" disabled={!canSave} onClick={save}>
            {saveLabel}
          </button>
        </>
      }
    >
      {quote !== undefined && <div className="quote">{quote}</div>}
      <textarea
        value={text}
        placeholder={placeholder}
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
  );
}
