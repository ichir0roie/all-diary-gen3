#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import SessionEntrypoint, record_of
from data_access_logic.query.common_query import own_row
from db.schema import Diary


class ReadDiary(SessionEntrypoint):
    def __init__(self, user_id: str, diary_id: int):
        self.user_id = user_id
        self.diary_id = diary_id

    def execute(self, s: Session) -> DiaryRecord:
        return record_of(s, DiaryRecord, own_row(s, Diary, self.diary_id, self.user_id))
