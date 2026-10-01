// 日付は日本時間の暦の日として "YYYY-MM-DD" の文字列で持つ(API の start_date / end_date と同じ形)。
// 足し引きは UTC の 0 時の Date で行い、ブラウザの時差の影響を受けないようにする
const TIME_ZONE = "Asia/Tokyo";

const toDay = (date: Date) => date.toISOString().slice(0, 10);
const fromDay = (day: string) => new Date(`${day}T00:00:00Z`);

/** 日本時間の今日。sv-SE の書式が "YYYY-MM-DD" になる */
export const today = () => new Intl.DateTimeFormat("sv-SE", { timeZone: TIME_ZONE }).format(new Date());

export function addDays(day: string, days: number): string {
  const date = fromDay(day);
  date.setUTCDate(date.getUTCDate() + days);
  return toDay(date);
}

export function addYears(day: string, years: number): string {
  const date = fromDay(day);
  date.setUTCFullYear(date.getUTCFullYear() + years);
  return toDay(date);
}

/** "MM/DD" */
export const monthDay = (day: string) => day.slice(5).replace("-", "/");

const timeFormat = new Intl.DateTimeFormat("ja-JP", {
  timeZone: TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
});

/** API の時刻(ISO 8601)を、日本時間の "YYYY/MM/DD HH:mm" にする */
export const dateTime = (iso: string) => timeFormat.format(new Date(iso));

const dayFormat = new Intl.DateTimeFormat("ja-JP", { timeZone: TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" });

/** API の時刻(ISO 8601)を、日本時間の "YYYY/MM/DD" にする */
export const dateOnly = (iso: string) => dayFormat.format(new Date(iso));

/** API の時刻(ISO 8601)の、日本時間の暦の日("YYYY-MM-DD") */
export const dayOf = (iso: string) => new Intl.DateTimeFormat("sv-SE", { timeZone: TIME_ZONE }).format(new Date(iso));

/** 0 が日曜 */
export const weekday = (day: string) => fromDay(day).getUTCDay();

export const isDay = (value: string | null): value is string => value !== null && /^\d{4}-\d{2}-\d{2}$/.test(value);
