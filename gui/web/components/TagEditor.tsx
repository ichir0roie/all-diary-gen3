"use client";

import { useState } from "react";
import ConfirmDialog from "@/components/ConfirmDialog";
import { commitTag, deleteTag, updateTag, type TagUsage } from "@/lib/api";
import { T } from "@/lib/text";

type Props = {
  usages: TagUsage[];
  /** タグを作った・名前を変えた・消したあと。呼ぶ側が一覧を読み直す(数と名前の順が変わる) */
  onChanged: () => void;
};

/** タグを作る・名前を変える・消す。消したタグが付いていた日記・コメントは、タグ無しに戻る */
export default function TagEditor({ usages, onChanged }: Props) {
  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);
  // 名前を変えている途中のタグと、打っている名前
  const [renaming, setRenaming] = useState<{ id: number; name: string } | null>(null);
  const [deleting, setDeleting] = useState<TagUsage | null>(null);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  // 失敗は欄の下に出す
  const run = async (work: () => Promise<unknown>) => {
    setResult(null);
    try {
      await work();
      onChanged();
      return true;
    } catch (e) {
      setResult({ ok: false, message: e instanceof Error ? e.message : String(e) });
      return false;
    }
  };

  const add = async () => {
    setAdding(true);
    if (await run(() => commitTag(newName))) setNewName("");
    setAdding(false);
  };

  const rename = async () => {
    if (!renaming) return;
    if (await run(() => updateTag(renaming.id, renaming.name))) setRenaming(null);
  };

  const canAdd = !adding && newName.trim() !== "";

  return (
    <div className="tag-editor">
      <p className="hint">{T.tag.hint}</p>
      <form
        className="toolbar"
        onSubmit={(e) => {
          e.preventDefault();
          if (canAdd) add();
        }}
      >
        <input
          type="text"
          className="text-input"
          value={newName}
          placeholder={T.tag.newName}
          onChange={(e) => setNewName(e.target.value)}
        />
        <button type="submit" className="primary" disabled={!canAdd}>{T.tag.add}</button>
      </form>
      {result && <div className={`status ${result.ok ? "ok" : "error"}`}>{result.message}</div>}
      {usages.length === 0 && <div className="empty">{T.tag.noTagYet}</div>}
      {usages.length > 0 && (
        <table className="list tag-list">
          <thead>
            <tr>
              <th>{T.tag.name}</th>
              <th>{T.tag.usage}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {usages.map((usage) => (
              <tr key={usage.tag.id}>
                <td>
                  {renaming?.id === usage.tag.id ? (
                    <form
                      className="rename"
                      onSubmit={(e) => {
                        e.preventDefault();
                        rename();
                      }}
                    >
                      <input
                        type="text"
                        className="text-input"
                        value={renaming.name}
                        autoFocus
                        onChange={(e) => setRenaming({ id: usage.tag.id, name: e.target.value })}
                        onKeyDown={(e) => e.key === "Escape" && setRenaming(null)}
                      />
                      <button type="submit" className="primary" disabled={renaming.name.trim() === ""}>{T.tag.save}</button>
                      <button type="button" onClick={() => setRenaming(null)}>{T.tag.cancel}</button>
                    </form>
                  ) : (
                    <span className="tag-chip">{usage.tag.name}</span>
                  )}
                </td>
                <td className="usage">{T.tag.usageCount(usage.diaries, usage.comments)}</td>
                <td className="actions">
                  <button type="button" onClick={() => setRenaming({ id: usage.tag.id, name: usage.tag.name })}>
                    {T.tag.rename}
                  </button>
                  <button type="button" className="danger" onClick={() => setDeleting(usage)}>{T.tag.delete}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {deleting && (
        <ConfirmDialog
          title={T.tag.deleteTitle}
          message={T.tag.deleteConfirm(deleting.tag.name, deleting.diaries, deleting.comments)}
          confirmLabel={T.tag.delete}
          onClose={() => setDeleting(null)}
          onConfirm={async () => {
            await deleteTag(deleting.tag.id);
            if (renaming?.id === deleting.tag.id) setRenaming(null);
            setResult({ ok: true, message: T.tag.deleted(deleting.tag.name) });
            onChanged();
          }}
        />
      )}
    </div>
  );
}
