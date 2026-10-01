#!/usr/bin/env python3
"""日記の API。リポジトリのルートから次で起動する(`DIARY_DATABASE_URL` などは他の python と同じ)。

    .venv/bin/python -m uvicorn gui.api.app:app --port 8766 --reload
"""
from __future__ import annotations

import hmac
import logging
import os
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from data_access_logic.comment.commit_comment import CommitComment
from data_access_logic.comment.delete_comment import DeleteComment
from data_access_logic.comment.form import CommentCreateForm, CommentUpdateForm
from data_access_logic.comment.list_comments import ListComments
from data_access_logic.comment.read_comment import ReadComment
from data_access_logic.comment.record import CommentRecord, DeletedComment
from data_access_logic.comment.update_comment import UpdateComment
from data_access_logic.csv_file.export_comment_csv import ExportCommentCsv
from data_access_logic.csv_file.export_diary_csv import ExportDiaryCsv
from data_access_logic.csv_file.import_comment_csv import ImportCommentCsv
from data_access_logic.csv_file.import_diary_csv import ImportDiaryCsv
from data_access_logic.csv_file.record import Imported
from data_access_logic.diary.commit_diary import CommitDiary
from data_access_logic.diary.count_diaries_by_day import CountDiariesByDay
from data_access_logic.diary.delete_diary import DeleteDiary
from data_access_logic.diary.form import DiaryCreateForm, DiaryUpdateForm, FutureDiaryCreateForm
from data_access_logic.diary.list_diaries import ListDiaries
from data_access_logic.diary.list_future_diaries import ListFutureDiaries
from data_access_logic.diary.list_on_this_day import ListOnThisDay
from data_access_logic.diary.read_diary import ReadDiary
from data_access_logic.diary.record import (DayCount, DeletedDiary, DiaryRecord, FutureDiaryRecord, OnThisDayYear,
                                            SimilarDiaries)
from data_access_logic.diary.search_similar_diaries import SearchSimilarDiaries
from data_access_logic.diary.send_future_diary import SendFutureDiary
from data_access_logic.diary.update_diary import UpdateDiary
from data_access_logic.entrypoint import UnknownRecordError
from data_access_logic.legacy_db.import_legacy_db import ImportLegacyDb
from data_access_logic.legacy_db.record import LegacyDbSummary, LegacyImported
from data_access_logic.legacy_db.summarize_legacy_db import SummarizeLegacyDb
from data_access_logic.logs import configure_logging
from db.schema import engine, get_env_session
from gui.api.models import FILE_BODY, CsvImportRequest, CsvKind, Health, SimilarSearchRequest
from gui.api.user import user_id_dep

logger = logging.getLogger(__name__)
configure_logging()

app = FastAPI(title="all-diary API", version="0.1.0")

# 公開の URL(Lambda の関数 URL)に置くときの合言葉。呼ぶ側ごとに `名前=鍵` をカンマで区切って持つ(例: gui=…)。
# 画面の Next.js のサーバー(`gui/web/app/api`)が付けて流す。空ならローカル向けとして確かめない
API_KEY_HEADER = "x-diary-api-key"


def _parse_api_keys(raw: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    for entry in filter(None, (entry.strip() for entry in raw.split(","))):
        name, _, key = (part.strip() for part in entry.partition("="))
        if not name or not key:
            raise ValueError("DIARY_API_KEYS は `名前=鍵` をカンマで区切って書く")
        keys[name] = key
    return keys


_API_KEYS = _parse_api_keys(os.environ.get("DIARY_API_KEYS", ""))
# 合言葉なしで通すパス。Lambda Web Adapter の起動確認が叩く
_PUBLIC_PATHS = {"/api/ping"}


@app.middleware("http")
async def _require_api_key(request: Request, call_next):
    if _API_KEYS and request.url.path not in _PUBLIC_PATHS:
        given = request.headers.get(API_KEY_HEADER, "").encode()
        caller = next((name for name, key in _API_KEYS.items() if hmac.compare_digest(given, key.encode())), None)
        if caller is None:
            return JSONResponse(status_code=401, content={"detail": f"{API_KEY_HEADER} が無いか違う"})
        logger.info(f"{caller}: {request.method} {request.url.path}")
    return await call_next(request)


def session_dep() -> Iterator[Session]:
    with get_env_session() as s:
        yield s


UserId = Annotated[str, Depends(user_id_dep)]
Db = Annotated[Session, Depends(session_dep)]


@app.exception_handler(UnknownRecordError)
async def _unknown_record(_request: Request, error: UnknownRecordError):
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ValueError)
async def _bad_value(_request: Request, error: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


@app.exception_handler(OperationalError)
async def _db_unreachable(_request: Request, error: OperationalError):
    return JSONResponse(status_code=503, content={"detail": str(error.orig or error)})


@app.get("/api/ping")
def ping() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(dialect=engine.dialect.name)


@app.get("/api/diaries", response_model=list[DiaryRecord])
def list_diaries(user_id: UserId, s: Db, start_date: date | None = None, end_date: date | None = None) -> list[DiaryRecord]:
    """日本時間の `start_date` から `end_date` まで(両端を含む)の日記を、コメント付きで時刻の順に返す。"""
    return ListDiaries(user_id, start_date=start_date, end_date=end_date).execute(s)


@app.post("/api/diaries/similar", response_model=SimilarDiaries)
def search_similar_diaries(request: SimilarSearchRequest, user_id: UserId, s: Db) -> SimilarDiaries:
    """`text` に似た日記の数と、似ている順の頭の何件か。"""
    return SearchSimilarDiaries(user_id, request.text).execute(s)


@app.get("/api/on-this-day", response_model=list[OnThisDayYear])
def list_on_this_day(day: date, user_id: UserId, s: Db, around_days: int = 0) -> list[OnThisDayYear]:
    """`day` と同じ月日の前後 `around_days` 日の日記を、年ごとに新しい年から。"""
    return ListOnThisDay(user_id, day, around_days).execute(s)


@app.get("/api/diary-counts", response_model=list[DayCount])
def count_diaries_by_day(user_id: UserId, s: Db, start_date: date | None = None,
                         end_date: date | None = None) -> list[DayCount]:
    """日本時間の暦の日ごとの、日記の件数と文字数。書いた日だけ。"""
    return CountDiariesByDay(user_id, start_date=start_date, end_date=end_date).execute(s)


@app.get("/api/future-diaries", response_model=list[FutureDiaryRecord])
def list_future_diaries(user_id: UserId, s: Db) -> list[FutureDiaryRecord]:
    """まだ届いていない未来の日記の、届く時刻と書いた時刻。本文は返さない。"""
    return ListFutureDiaries(user_id).execute(s)


@app.post("/api/future-diaries", response_model=FutureDiaryRecord, status_code=201)
def send_future_diary(diary: FutureDiaryCreateForm, user_id: UserId, s: Db) -> FutureDiaryRecord:
    with s.begin():
        return SendFutureDiary(user_id, diary).execute(s)


@app.get("/api/diaries/{diary_id}", response_model=DiaryRecord)
def read_diary(diary_id: int, user_id: UserId, s: Db) -> DiaryRecord:
    return ReadDiary(user_id, diary_id).execute(s)


@app.post("/api/diaries", response_model=DiaryRecord, status_code=201)
def commit_diary(diary: DiaryCreateForm, user_id: UserId, s: Db) -> DiaryRecord:
    with s.begin():
        return CommitDiary(user_id, diary).execute(s)


@app.patch("/api/diaries/{diary_id}", response_model=DiaryRecord)
def update_diary(diary_id: int, diary: DiaryUpdateForm, user_id: UserId, s: Db) -> DiaryRecord:
    with s.begin():
        return UpdateDiary(user_id, diary_id, diary).execute(s)


@app.delete("/api/diaries/{diary_id}", response_model=DeletedDiary)
def delete_diary(diary_id: int, user_id: UserId, s: Db) -> DeletedDiary:
    """日記を、付いたコメントごと消す。"""
    with s.begin():
        return DeleteDiary(user_id, diary_id).execute(s)


@app.get("/api/diaries/{diary_id}/comments", response_model=list[CommentRecord])
def list_comments(diary_id: int, user_id: UserId, s: Db) -> list[CommentRecord]:
    return ListComments(user_id, diary_id).execute(s)


@app.get("/api/comments/{comment_id}", response_model=CommentRecord)
def read_comment(comment_id: int, user_id: UserId, s: Db) -> CommentRecord:
    return ReadComment(user_id, comment_id).execute(s)


@app.post("/api/comments", response_model=CommentRecord, status_code=201)
def commit_comment(comment: CommentCreateForm, user_id: UserId, s: Db) -> CommentRecord:
    with s.begin():
        return CommitComment(user_id, comment).execute(s)


@app.patch("/api/comments/{comment_id}", response_model=CommentRecord)
def update_comment(comment_id: int, comment: CommentUpdateForm, user_id: UserId, s: Db) -> CommentRecord:
    with s.begin():
        return UpdateComment(user_id, comment_id, comment).execute(s)


@app.delete("/api/comments/{comment_id}", response_model=DeletedComment)
def delete_comment(comment_id: int, user_id: UserId, s: Db) -> DeletedComment:
    with s.begin():
        return DeleteComment(user_id, comment_id).execute(s)


@app.post("/api/csv/{kind}", response_model=Imported)
def import_csv(kind: CsvKind, request: CsvImportRequest, user_id: UserId, s: Db) -> Imported:
    """CSV を取り込む。コメントは、先に取り込んだ日記の CSV の id を `diary_id` で指す。"""
    entrypoint = ImportDiaryCsv if kind == "diary" else ImportCommentCsv
    with s.begin():
        return entrypoint(user_id, request.text).execute(s)


@app.get("/api/csv/{kind}", response_class=Response,
         responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}})
def export_csv(kind: CsvKind, user_id: UserId, s: Db) -> Response:
    """取り込み直せる形の CSV を返す。"""
    entrypoint = ExportDiaryCsv if kind == "diary" else ExportCommentCsv
    dump = entrypoint(user_id).execute(s)
    return Response(content=dump.text, media_type="text/csv; charset=utf-8",
                    headers={"content-disposition": f'attachment; filename="{kind}.csv"'})


@app.post("/api/legacy-db/summary", response_model=LegacyDbSummary, openapi_extra=FILE_BODY)
async def summarize_legacy_db(request: Request, _user_id: UserId) -> LegacyDbSummary:
    """以前の SQLite の db ファイル(本文にそのまま)に、誰の日記が何件あるか。db には触れない。"""
    # 本文は async でしか読めない。読んだあとの重い処理は、イベントループを塞がないようスレッドで回す
    return await run_in_threadpool(SummarizeLegacyDb(await request.body()).result)


@app.post("/api/legacy-db/import", response_model=LegacyImported, openapi_extra=FILE_BODY)
async def import_legacy_db(request: Request, source_user_id: str, user_id: UserId) -> LegacyImported:
    """以前の SQLite の db ファイル(本文にそのまま)から、`source_user_id` の日記とコメントを取り込む。"""
    return await run_in_threadpool(_import_legacy_db, user_id, await request.body(), source_user_id)


def _import_legacy_db(user_id: str, sqlite_bytes: bytes, source_user_id: str) -> LegacyImported:
    with get_env_session() as s, s.begin():
        return ImportLegacyDb(user_id, sqlite_bytes, source_user_id).execute(s)
