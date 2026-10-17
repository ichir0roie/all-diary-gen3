"use client";

import { useSyncExternalStore } from "react";
import DiaryBoard from "@/components/DiaryBoard";
import DiaryWeeks from "@/components/DiaryWeeks";
import { T } from "@/lib/text";

// globals.css の狭い画面(max-width: 640px)の外側
const WIDE = "(min-width: 641px)";

const subscribe = (onChange: () => void) => {
  const query = window.matchMedia(WIDE);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
};

/** パソコンでは週と年を上下左右にどこまでも読める盤、スマホでは今年の一週間を出す */
export default function Home() {
  const wide = useSyncExternalStore(subscribe, () => window.matchMedia(WIDE).matches, () => null);
  if (wide === null) return <div className="status info">{T.loading}</div>;
  return wide ? <DiaryBoard /> : <DiaryWeeks />;
}
