#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.diary.form import DiaryCreateForm
from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import CommitEntrypoint, record_of
from db.schema import Diary


class CommitDiary(CommitEntrypoint):
    def __init__(self, user_id: str, diary: DiaryCreateForm):
        self.user_id = user_id
        self.diary = diary

    def execute(self, s: Session) -> DiaryRecord:
        record = Diary(user_id=self.user_id)
        self.diary.write_to(record)
        record.time = self.diary.time or datetime.now(JST)
        s.add(record)
        self.finalize(s, record)
        return record_of(s, DiaryRecord, record)
