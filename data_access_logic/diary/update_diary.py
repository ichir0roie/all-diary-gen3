#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.diary.form import DiaryUpdateForm
from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import CommitEntrypoint, record_of
from data_access_logic.query.common_query import own_diary


class UpdateDiary(CommitEntrypoint):
    """日記の本文を書き直す。書いた時刻は変えない。"""

    def __init__(self, user_id: str, diary_id: int, diary: DiaryUpdateForm):
        self.user_id = user_id
        self.diary_id = diary_id
        self.diary = diary

    def execute(self, s: Session) -> DiaryRecord:
        record = own_diary(s, self.diary_id, self.user_id)
        self.diary.write_to(record)
        self.finalize(s, record)
        return record_of(s, DiaryRecord, record)
