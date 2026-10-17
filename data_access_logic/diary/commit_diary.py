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
    """日記を書く。`time` を省けば今の時刻、渡せばその時刻(過去の日の書き足し)。未来の日は `SendFutureDiary` で封をして送る。"""

    def __init__(self, user_id: str, diary: DiaryCreateForm):
        self.user_id = user_id
        self.diary = diary

    def execute(self, s: Session) -> DiaryRecord:
        now = datetime.now(JST)
        if self.diary.time is not None and self.diary.time > now:
            raise ValueError(f"日記の時刻({self.diary.time.isoformat()})は今より前にする。未来へは future-diaries で送る")
        record = Diary(user_id=self.user_id)
        self.diary.write_to(record)
        record.time = self.diary.time or now
        s.add(record)
        self.finalize(s, record)
        return record_of(s, DiaryRecord, record)
