"use client";

import { useState } from "react";
import { importLegacyDb, summarizeLegacyDb, type LegacyDbSummary } from "@/lib/api";
import { dateTime } from "@/lib/date";
import { T } from "@/lib/text";

/** 以前の API の SQLite の db ファイルを取り込む。ファイルを選ぶと中の人ごとの件数を読み、選んだ人の日記とコメントを自分の行として足す */
export default function ImportLegacyDbPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<LegacyDbSummary | null>(null);
  const [sourceUserId, setSourceUserId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  const fail = (e: unknown) => setResult({ ok: false, message: e instanceof Error ? e.message : String(e) });

  const choose = async (chosen: File | null) => {
    setFile(chosen);
    setSummary(null);
    setSourceUserId(null);
    setResult(null);
    if (!chosen) return;
    setBusy(true);
    try {
      const read = await summarizeLegacyDb(chosen);
      setSummary(read);
      // 件数の多い順に並ぶので、一番多い人(ふつうは自分)を初めから選んでおく
      setSourceUserId(read.users[0]?.user_id ?? null);
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };

  const upload = async () => {
    if (!file || !sourceUserId) return;
    setBusy(true);
    setResult(null);
    try {
      const imported = await importLegacyDb(file, sourceUserId);
      setResult({
        ok: true,
        message: [
          T.data.imported(T.data.kinds.diary, imported.diaries.added, imported.diaries.skipped),
          T.data.imported(T.data.kinds.comment, imported.comments.added, imported.comments.skipped),
        ].join(" "),
      });
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <h2>{T.data.dbTitle}</h2>
      <p className="hint">{T.data.dbHint}</p>
      <div className="field">
        <label htmlFor="db-file">{T.data.dbFile}</label>
        <input id="db-file" type="file" accept=".db,.sqlite,.sqlite3" onChange={(e) => choose(e.target.files?.[0] ?? null)} />
      </div>
      {busy && !summary && <div className="status info">{T.data.reading}</div>}
      {summary && summary.users.length === 0 && <div className="status info">{T.data.noUsers}</div>}
      {summary && summary.users.length > 0 && (
        <table className="list">
          <thead>
            <tr>
              <th />
              <th>{T.data.sourceUser}</th>
              <th>{T.data.kinds.diary}</th>
              <th>{T.data.kinds.comment}</th>
              <th>{T.data.period}</th>
            </tr>
          </thead>
          <tbody>
            {summary.users.map((user) => (
              <tr key={user.user_id} onClick={() => setSourceUserId(user.user_id)}>
                <td>
                  <input
                    type="radio"
                    name="source-user"
                    aria-label={user.user_id}
                    checked={sourceUserId === user.user_id}
                    onChange={() => setSourceUserId(user.user_id)}
                  />
                </td>
                <td><code>{user.user_id}</code></td>
                <td>{user.diaries}</td>
                <td>{user.comments}</td>
                <td>{T.data.span(dateTime(user.first_time), dateTime(user.last_time))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {summary && summary.unlinked_comments > 0 && <div className="status info">{T.data.unlinked(summary.unlinked_comments)}</div>}
      {result && <div className={`status ${result.ok ? "ok" : "error"}`}>{result.message}</div>}
      <button type="button" className="primary" disabled={!file || !sourceUserId || busy} onClick={upload}>
        {busy && summary ? T.data.importing : T.data.import}
      </button>
    </section>
  );
}
