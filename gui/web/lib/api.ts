import { fetchAuthSession } from "aws-amplify/auth";
import { loginRequired } from "./auth";
import type { components } from "./openapi";

export type DiaryRecord = components["schemas"]["DiaryRecord"];
export type CommentRecord = components["schemas"]["CommentRecord"];
export type Imported = components["schemas"]["Imported"];
export type CsvKind = "diary" | "comment";
export type DeletedDiary = components["schemas"]["DeletedDiary"];
export type DeletedComment = components["schemas"]["DeletedComment"];
export type FutureDiaryRecord = components["schemas"]["FutureDiaryRecord"];
export type OnThisDayYear = components["schemas"]["OnThisDayYear"];
export type DayCount = components["schemas"]["DayCount"];
export type SimilarDiaries = components["schemas"]["SimilarDiaries"];

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  // アクセストークン(1 時間)が切れていれば、更新のトークンで取り直してクッキーに置く。route handler はクッキーのトークンを確かめる
  if (loginRequired) await fetchAuthSession();
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // 本文が JSON でないときは statusText のまま
    }
    throw new ApiError(response.status, detail);
  }
  return response;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  return (await (await request(path, init)).json()) as T;
}

/** 日本時間の `startDate` から `endDate` まで(両端を含む。"YYYY-MM-DD")の日記を、コメント付きで返す。 */
export const listDiaries = (startDate: string, endDate: string) =>
  api<DiaryRecord[]>(`/api/diaries?${new URLSearchParams({ start_date: startDate, end_date: endDate })}`);

/** 時刻は API が書き込んだ時刻にする。 */
export const commitDiary = (text: string) =>
  api<DiaryRecord>("/api/diaries", { method: "POST", body: JSON.stringify({ text }) });

export const commitComment = (diaryId: number, text: string) =>
  api<CommentRecord>("/api/comments", { method: "POST", body: JSON.stringify({ diary_id: diaryId, text }) });

export const updateDiary = (diaryId: number, text: string) =>
  api<DiaryRecord>(`/api/diaries/${diaryId}`, { method: "PATCH", body: JSON.stringify({ text }) });

/** 付いたコメントごと消す */
export const deleteDiary = (diaryId: number) => api<DeletedDiary>(`/api/diaries/${diaryId}`, { method: "DELETE" });

export const updateComment = (commentId: number, text: string) =>
  api<CommentRecord>(`/api/comments/${commentId}`, { method: "PATCH", body: JSON.stringify({ text }) });

export const deleteComment = (commentId: number) =>
  api<DeletedComment>(`/api/comments/${commentId}`, { method: "DELETE" });

/** `deliverOn`("YYYY-MM-DD"、日本時間)の 0 時に届く日記を送る。届くまで本文は読めない */
export const sendFutureDiary = (text: string, deliverOn: string) =>
  api<FutureDiaryRecord>("/api/future-diaries", { method: "POST", body: JSON.stringify({ text, deliver_on: deliverOn }) });

/** まだ届いていない日記の、届く時刻と書いた時刻(本文は無い) */
export const listFutureDiaries = () => api<FutureDiaryRecord[]>("/api/future-diaries");

/** `day` と同じ月日の前後 `aroundDays` 日の日記を、年ごとに新しい年から */
export const listOnThisDay = (day: string, aroundDays: number) =>
  api<OnThisDayYear[]>(`/api/on-this-day?${new URLSearchParams({ day, around_days: String(aroundDays) })}`);

/** 日ごとの日記の件数と文字数。書いた日だけ */
export const countDiariesByDay = () => api<DayCount[]>("/api/diary-counts");

export const searchSimilarDiaries = (text: string, signal?: AbortSignal) =>
  api<SimilarDiaries>("/api/diaries/similar", { method: "POST", body: JSON.stringify({ text }), signal });

export const importCsv = (kind: CsvKind, text: string) =>
  api<Imported>(`/api/csv/${kind}`, { method: "POST", body: JSON.stringify({ text }) });

export const exportCsv = async (kind: CsvKind) => (await request(`/api/csv/${kind}`)).blob();

export type LegacyDbSummary = components["schemas"]["LegacyDbSummary"];
export type LegacyUser = components["schemas"]["LegacyUser"];
export type LegacyImported = components["schemas"]["LegacyImported"];

const FILE_HEADERS = { "Content-Type": "application/octet-stream" };

/** 以前の SQLite の db ファイルに、誰の日記が何件あるか。ファイルは本文にそのまま載せる */
export const summarizeLegacyDb = (file: Blob) =>
  api<LegacyDbSummary>("/api/legacy-db/summary", { method: "POST", headers: FILE_HEADERS, body: file });

export const importLegacyDb = (file: Blob, sourceUserId: string) =>
  api<LegacyImported>(`/api/legacy-db/import?${new URLSearchParams({ source_user_id: sourceUserId })}`, {
    method: "POST",
    headers: FILE_HEADERS,
    body: file,
  });
