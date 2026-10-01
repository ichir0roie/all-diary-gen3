#!/usr/bin/env python3
from __future__ import annotations

import calendar
from datetime import date, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.diary.record import DiaryRecord, OnThisDayYear
from data_access_logic.entrypoint import SessionEntrypoint, loading
from data_access_logic.query.common_query import delivered, in_days
from db.schema import Diary

# 年ごとの範囲が隣の年と重ならないよう、前後の幅に上限を置く
MAX_AROUND_DAYS = 30


def same_day_in(year: int, day: date) -> date:
    """`day` と同じ月日の、`year` 年の日。2 月 29 日は、うるう年でない年では 2 月 28 日にする。"""
    return day.replace(year=year, day=min(day.day, calendar.monthrange(year, day.month)[1]))


class ListOnThisDay(SessionEntrypoint):
    """`day` と同じ月日の前後 `around_days` 日の日記を、書き始めた年から `day` の年まで、年ごとに新しい年から並べる。
    日記の無い年も空で返す(書かなかった年が分かるように)。"""

    def __init__(self, user_id: str, day: date, around_days: int = 0):
        if not 0 <= around_days <= MAX_AROUND_DAYS:
            raise ValueError(f"around_days は 0 から {MAX_AROUND_DAYS} にする")
        self.user_id = user_id
        self.day = day
        self.around_days = around_days

    def execute(self, s: Session) -> list[OnThisDayYear]:
        own = and_(Diary.user_id == self.user_id, delivered())
        first_time = s.scalar(select(func.min(Diary.time)).where(own))
        if first_time is None:
            return []
        around = timedelta(days=self.around_days)
        spans = []
        for year in range(self.day.year, min(first_time.astimezone(JST).year, self.day.year) - 1, -1):
            center = same_day_in(year, self.day)
            spans.append(OnThisDayYear(year=year, start_date=center - around, end_date=center + around, diaries=[]))
        query = (select(Diary)
                 .where(own, or_(*(and_(*in_days(Diary.time, span.start_date, span.end_date)) for span in spans)))
                 .order_by(Diary.time, Diary.id))
        for row in s.scalars(loading(query, DiaryRecord)):
            written_on = row.time.astimezone(JST).date()
            span = next(span for span in spans if span.start_date <= written_on <= span.end_date)
            span.diaries.append(DiaryRecord.model_validate(row))
        return spans
