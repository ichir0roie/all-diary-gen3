#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import ColumnElement
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
