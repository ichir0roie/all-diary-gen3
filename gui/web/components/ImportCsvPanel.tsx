"use client";

import { useRef, useState } from "react";
import { importCsv, type CsvKind } from "@/lib/api";
import { T } from "@/lib/text";

const KINDS: CsvKind[] = ["diary", "comment"];

/** 日記・コメントの CSV を取り込む。以前の db から書き出した CSV もそのまま読める */
export default function ImportCsvPanel() {
  const [kind, setKind] = useState<CsvKind>("diary");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const upload = async () => {
    if (!file) return;
    setBusy(true);
    setResult(null);
    try {
      const imported = await importCsv(kind, await file.text());
      setResult({ ok: true, message: T.data.imported(T.data.kinds[kind], imported.added, imported.skipped) });
      setFile(null);
      if (fileInput.current) fileInput.current.value = "";
    } catch (e) {
      setResult({ ok: false, message: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <h2>{T.data.csvTitle}</h2>
      <p className="hint">{T.data.csvHint}</p>
      <div className="field">
        <label htmlFor="csv-kind">{T.data.kind}</label>
        <select id="csv-kind" value={kind} onChange={(e) => setKind(e.target.value as CsvKind)}>
          {KINDS.map((value) => (
            <option key={value} value={value}>{T.data.kinds[value]}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="csv-file">{T.data.csvFile}</label>
        <input
          id="csv-file"
          ref={fileInput}
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            setResult(null);
          }}
        />
      </div>
      {result && <div className={`status ${result.ok ? "ok" : "error"}`}>{result.message}</div>}
      <button type="button" className="primary" disabled={!file || busy} onClick={upload}>
        {busy ? T.data.importing : T.data.import}
      </button>
    </section>
  );
}
