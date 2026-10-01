#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import ColumnElement, or_
from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.entrypoint import UnknownRecordError
from db.schema import Comment, Diary


def own_row[M: Diary | Comment](s: Session, model: type[M], id_: int, user_id: str) -> M:
    """`user_id` の人が書いた行だけを返す。他の人の行も、無い行と同じに扱う(在ることを漏らさない)。"""
    row = s.get(model, id_)
    if row is None or row.user_id != user_id:
        raise UnknownRecordError(f"id={id_} の {model.__tablename__} が見つからない")
    return row


def in_days(column, start_date: date | None, end_date: date | None) -> list[ColumnElement[bool]]:
    """日本時間の `start_date` の 0 時から、`end_date` の翌日の 0 時の前まで。省いた端は限らない。"""
    conditions = []
    if start_date is not None:
        conditions.append(column >= datetime.combine(start_date, time(), JST))
    if end_date is not None:
        conditions.append(column < datetime.combine(end_date + timedelta(days=1), time(), JST))
    return conditions


def delivered() -> ColumnElement[bool]:
    """封をした未来の日記(届く時刻の前)を除く。"""
    return or_(Diary.written_at.is_(None), Diary.time <= datetime.now(JST))


def own_diary(s: Session, diary_id: int, user_id: str) -> Diary:
    """`own_row` に加え、まだ届いていない未来の日記も、無い行と同じに扱う(届くまで読むことも書き足すこともできない)。"""
    diary = own_row(s, Diary, diary_id, user_id)
    if diary.written_at is not None and diary.time > datetime.now(JST):
        raise UnknownRecordError(f"id={diary_id} の diary が見つからない")
    return diary
