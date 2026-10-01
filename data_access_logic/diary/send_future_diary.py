#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, time

from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.diary.form import FutureDiaryCreateForm
from data_access_logic.diary.record import FutureDiaryRecord
from data_access_logic.entrypoint import CommitEntrypoint
from db.schema import Diary


class SendFutureDiary(CommitEntrypoint):
    """日記を未来へ送る。`deliver_on`(日本時間)の 0 時に、その時刻の日記として届く。届くまではどの入口も本文を読まない。"""

    def __init__(self, user_id: str, diary: FutureDiaryCreateForm):
        self.user_id = user_id
        self.diary = diary

    def execute(self, s: Session) -> FutureDiaryRecord:
        now = datetime.now(JST)
        if self.diary.deliver_on <= now.date():
            raise ValueError(f"届ける日({self.diary.deliver_on})は明日より後にする")
        record = Diary(user_id=self.user_id, written_at=now, time=datetime.combine(self.diary.deliver_on, time(), JST))
        self.diary.write_to(record)
        s.add(record)
        self.finalize(s, record)
        return FutureDiaryRecord.model_validate(record)
