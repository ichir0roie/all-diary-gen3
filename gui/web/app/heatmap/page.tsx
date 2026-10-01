"use client";

import { useEffect, useState } from "react";
import Heatmap, { type Metric } from "@/components/Heatmap";
import { countDiariesByDay, type DayCount } from "@/lib/api";
import { T } from "@/lib/text";

const METRICS: Metric[] = ["diaries", "chars"];

/** 日記を書いた日を、年ごとのカレンダーに濃さで並べる */
export default function HeatmapPage() {
  const [counts, setCounts] = useState<DayCount[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metric, setMetric] = useState<Metric>("diaries");

  useEffect(() => {
    let current = true;
    countDiariesByDay()
      .then((found) => current && setCounts(found))
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, []);

  return (
    <div className="heatmap-page">
      <div className="toolbar">
        <h1>{T.heatmap.title}</h1>
        <div className="segmented" role="radiogroup" aria-label={T.heatmap.metric}>
          {METRICS.map((name) => (
            <button
              key={name}
              type="button"
              role="radio"
              aria-checked={metric === name}
              className={metric === name ? "active" : ""}
              onClick={() => setMetric(name)}
            >
              {T.heatmap.metrics[name]}
            </button>
          ))}
        </div>
      </div>
      {error && <div className="status error">{T.cannotReachApi(error)}</div>}
      {counts === null && !error && <div className="status info">{T.loading}</div>}
      {counts?.length === 0 && <div className="empty">{T.heatmap.noDiaryYet}</div>}
      {counts && counts.length > 0 && <Heatmap counts={counts} metric={metric} />}
    </div>
  );
}
