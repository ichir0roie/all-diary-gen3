#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import DayCount
from data_access_logic.entrypoint import SessionEntrypoint
from data_access_logic.query.common_query import delivered, in_days
from db.schema import Diary


class CountDiariesByDay(SessionEntrypoint):
    """日本時間の暦の日ごとに、日記の件数と文字数を数える。書いた日だけを日の順に返す。本文は返さない。
    `start_date` / `end_date` は両端を含み、省いた端は限らない。"""

    def __init__(self, user_id: str, start_date: date | None = None, end_date: date | None = None):
        self.user_id = user_id
        self.start_date = start_date
        self.end_date = end_date

    def execute(self, s: Session) -> list[DayCount]:
        # timezone() は時差付きの時刻を、その地域の時差の無い時刻にする。その日付が日本時間の暦の日
        day = func.date(func.timezone("Asia/Tokyo", Diary.time)).label("day")
        query = (select(day, func.count().label("diaries"), func.sum(func.char_length(Diary.text)).label("chars"))
                 .where(Diary.user_id == self.user_id, delivered(), *in_days(Diary.time, self.start_date, self.end_date))
                 .group_by(day)
                 .order_by(day))
        return [DayCount.model_validate(row) for row in s.execute(query)]
