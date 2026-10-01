"use client";

import { useState } from "react";
import { exportCsv, type CsvKind } from "@/lib/api";
import { T } from "@/lib/text";

const KINDS: CsvKind[] = ["diary", "comment"];

/** 自分の日記・コメントを、取り込み直せる形の CSV で書き出す */
export default function ExportPanel() {
  const [error, setError] = useState<string | null>(null);

  const download = async (kind: CsvKind) => {
    setError(null);
    try {
      const url = URL.createObjectURL(await exportCsv(kind));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${kind}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <section className="panel">
      <h2>{T.data.exportTitle}</h2>
      <p className="hint">{T.data.exportHint}</p>
      {error && <div className="status error">{error}</div>}
      <div className="toolbar">
        {KINDS.map((kind) => (
          <button key={kind} type="button" onClick={() => download(kind)}>
            {T.data.export(T.data.kinds[kind])}
          </button>
        ))}
      </div>
    </section>
  );
}
