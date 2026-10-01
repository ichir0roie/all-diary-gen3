import ExportPanel from "@/components/ExportPanel";
import ImportCsvPanel from "@/components/ImportCsvPanel";
import ImportLegacyDbPanel from "@/components/ImportLegacyDbPanel";
import { T } from "@/lib/text";

/** 日記とコメントの取り込み(以前の db ファイル・CSV)と書き出し */
export default function Data() {
  return (
    <div className="data-page">
      <h1>{T.data.title}</h1>
      <ImportLegacyDbPanel />
      <ImportCsvPanel />
      <ExportPanel />
    </div>
  );
}
