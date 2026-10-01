#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import SessionEntrypoint, loading
from data_access_logic.query.common_query import in_days
from db.schema import Diary


class ListDiaries(SessionEntrypoint):
    """`user_id` の人の日記を、コメント付きで時刻の順に並べる。`start_date` / `end_date` は日本時間の日付で、両端を含む。"""

    def __init__(self, user_id: str, start_date: date | None = None, end_date: date | None = None):
        self.user_id = user_id
        self.start_date = start_date
        self.end_date = end_date

    def execute(self, s: Session) -> list[DiaryRecord]:
        query = (select(Diary)
                 .where(Diary.user_id == self.user_id, *in_days(Diary.time, self.start_date, self.end_date))
                 .order_by(Diary.time, Diary.id))
        return [DiaryRecord.model_validate(row) for row in s.scalars(loading(query, DiaryRecord))]
