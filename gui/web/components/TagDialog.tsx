"use client";

import { useEffect, useState } from "react";
import Modal from "@/components/Modal";
import { commitTag, listTags, type TagRecord } from "@/lib/api";
import { isSubmitKey } from "@/lib/keys";
import { T } from "@/lib/text";

// 選んだもの。"new" は欄に打った名前で新しく作る
type Choice = number | null | "new";

type Props = {
  title: string;
  // 何にタグを付けるか(日記・コメントの本文)
  quote: string;
  initialTag: TagRecord | null;
  // 選んだタグを付ける。null ならタグを外す
  onSave: (tagId: number | null) => Promise<void>;
  onClose: () => void;
};

/** 日記・コメントのタグを、既にあるタグから選ぶか、打った名前で新しく作って付けるモーダル */
export default function TagDialog({ title, quote, initialTag, onSave, onClose }: Props) {
  const [tags, setTags] = useState<TagRecord[] | null>(null);
  const [query, setQuery] = useState("");
  const [choice, setChoice] = useState<Choice>(initialTag?.id ?? null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    listTags()
      .then((found) => current && setTags(found.map((usage) => usage.tag)))
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, []);

  // API と同じく、前後の空白を落として比べる
  const name = query.trim();
  const exact = tags?.find((tag) => tag.name === name);
  const shown = tags?.filter((tag) => tag.name.includes(name)) ?? [];
  const canCreate = name !== "" && tags !== null && !exact;
  const canSave = !saving && tags !== null && (choice === "new" ? canCreate : choice !== (initialTag?.id ?? null));

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSave(choice === "new" ? (await commitTag(name)).id : choice);
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
          <button type="button" onClick={onClose}>{T.tag.cancel}</button>
          <button type="button" className="primary" disabled={!canSave} onClick={save}>
            {T.tag.save}
          </button>
        </>
      }
    >
      <div className="quote">{quote}</div>
      <input
        type="text"
        className="text-input"
        value={query}
        placeholder={T.tag.search}
        autoFocus
        onChange={(e) => {
          setQuery(e.target.value);
          if (choice === "new") setChoice(initialTag?.id ?? null);
        }}
        onKeyDown={(e) => {
          if (isSubmitKey(e)) {
            e.preventDefault();
            if (canSave) save();
            return;
          }
          // Enter は、打った名前のタグを選ぶ(無ければ作る方を選ぶ)。日本語の変換を確定する Enter は除く
          if (e.key !== "Enter" || e.nativeEvent.isComposing) return;
          e.preventDefault();
          if (exact) setChoice(exact.id);
          else if (canCreate) setChoice("new");
        }}
      />
      {tags === null && !error && <div className="status info">{T.loading}</div>}
      {tags !== null && (
        <div className="tag-choices">
          <button type="button" className={choice === null ? "chosen" : ""} onClick={() => setChoice(null)}>
            {T.tag.none}
          </button>
          {shown.map((tag) => (
            <button
              key={tag.id}
              type="button"
              className={`tag-chip ${choice === tag.id ? "chosen" : ""}`}
              onClick={() => setChoice(tag.id)}
            >
              {tag.name}
            </button>
          ))}
          {canCreate && (
            <button type="button" className={`create ${choice === "new" ? "chosen" : ""}`} onClick={() => setChoice("new")}>
              {T.tag.create(name)}
            </button>
          )}
        </div>
      )}
      {tags?.length === 0 && name === "" && <p className="hint">{T.tag.noTagYet}</p>}
      {error && <div className="status error">{error}</div>}
    </Modal>
  );
}
