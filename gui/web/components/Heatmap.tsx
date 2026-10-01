"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type { DayCount } from "@/lib/api";
import { addDays, today, weekday } from "@/lib/date";
import { T } from "@/lib/text";

export type Metric = "diaries" | "chars";

// 濃さの段。0 は書かなかった日
const LEVELS = [0, 1, 2, 3, 4] as const;
type Level = (typeof LEVELS)[number];

type Props = {
  counts: DayCount[];
  metric: Metric;
};

/** 書いた日の値を 1〜4 の段に分ける境目。件数はそのまま(1, 2, 3, 4 件以上)、文字数は書いた日の四分位で切る */
function thresholds(counts: DayCount[], metric: Metric): number[] {
  if (metric === "diaries") return [1, 2, 3];
  const values = counts.map((count) => count.chars).sort((a, b) => a - b);
  return [0.25, 0.5, 0.75].map((q) => values[Math.floor(q * (values.length - 1))]);
}

function levelOf(value: number, bounds: number[]): Level {
  if (value <= 0) return 0;
  const index = bounds.findIndex((bound) => value <= bound);
  return (index === -1 ? 4 : index + 1) as Level;
}

/** 一年ぶんのカレンダー(列が週、行が曜日。日曜が上)。年の始まりの週の、前の年の日は空けておく */
function yearDays(year: number): (string | null)[] {
  const first = `${year}-01-01`;
  const days: (string | null)[] = Array(weekday(first)).fill(null);
  for (let day = first; day.startsWith(String(year)); day = addDays(day, 1)) days.push(day);
  return days;
}

/** 年ごとに、日記を書いた日を濃さで並べる。日を押すとその週の日記を開く */
export default function Heatmap({ counts, metric }: Props) {
  const router = useRouter();
  const [hovered, setHovered] = useState<string | null>(null);
  // next build が書き出す HTML に建てた日の日付が残らないよう、今日はブラウザで開いてから決める
  const [now, setNow] = useState<string | null>(null);
  useEffect(() => setNow(today()), []);

  const byDay = useMemo(() => new Map(counts.map((count) => [count.day, count])), [counts]);
  const bounds = useMemo(() => thresholds(counts, metric), [counts, metric]);

  if (now === null) return <div className="status info">{T.loading}</div>;
  const firstYear = Number(counts[0].day.slice(0, 4));
  const lastYear = Math.max(Number(now.slice(0, 4)), Number(counts[counts.length - 1].day.slice(0, 4)));
  const years = Array.from({ length: lastYear - firstYear + 1 }, (_, i) => lastYear - i);

  const hoveredCount = hovered === null ? null : (byDay.get(hovered) ?? { day: hovered, diaries: 0, chars: 0 });

  return (
    <div className="heatmap">
      <div className="heatmap-head">
        <div className="readout" aria-live="polite">
          {hoveredCount ? T.heatmap.cell(hoveredCount.day, hoveredCount.diaries, hoveredCount.chars) : T.heatmap.readoutHint}
        </div>
        <div className="legend" aria-hidden>
          {T.heatmap.less}
          {LEVELS.map((level) => (
            <span key={level} className={`cell level-${level}`} />
          ))}
          {T.heatmap.more}
        </div>
      </div>
      {years.map((year) => {
        const days = yearDays(year);
        const total = days.reduce(
          (sum, day) => {
            const count = day ? byDay.get(day) : undefined;
            return count ? { diaries: sum.diaries + count.diaries, chars: sum.chars + count.chars } : sum;
          },
          { diaries: 0, chars: 0 },
        );
        const weeks = Math.ceil(days.length / 7);
        return (
          <section key={year} className="heatmap-year">
            <h2>
              {year}
              <span className="total">{T.heatmap.yearTotal(total.diaries, total.chars)}</span>
            </h2>
            <div className="heatmap-scroll">
              <div className="heatmap-grid" style={{ gridTemplateColumns: `auto repeat(${weeks}, var(--cell))` }}>
                {T.heatmap.months.map((name, month) => {
                  const index = days.indexOf(`${year}-${String(month + 1).padStart(2, "0")}-01`);
                  return (
                    <span key={name} className="month" style={{ gridRow: 1, gridColumn: Math.floor(index / 7) + 2 }}>
                      {name}
                    </span>
                  );
                })}
                {T.heatmap.weekdays.map((name, row) => (
                  <span key={row} className="weekday" style={{ gridRow: row + 2, gridColumn: 1 }}>
                    {name}
                  </span>
                ))}
                {days.map((day, index) => {
                  if (day === null) return null;
                  const count = byDay.get(day);
                  const level = levelOf(count ? count[metric] : 0, bounds);
                  const label = T.heatmap.cell(day, count?.diaries ?? 0, count?.chars ?? 0);
                  return (
                    <button
                      key={day}
                      type="button"
                      className={`cell level-${level}${day === now ? " today" : ""}`}
                      style={{ gridRow: (index % 7) + 2, gridColumn: Math.floor(index / 7) + 2 }}
                      title={label}
                      aria-label={label}
                      onMouseEnter={() => setHovered(day)}
                      onMouseLeave={() => setHovered(null)}
                      onFocus={() => setHovered(day)}
                      onClick={() => router.push(`/?${new URLSearchParams({ day })}`)}
                    />
                  );
                })}
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}
