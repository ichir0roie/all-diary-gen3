#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.diary.record import FutureDiaryRecord
from data_access_logic.entrypoint import SessionEntrypoint
from db.schema import Diary


class ListFutureDiaries(SessionEntrypoint):
    """まだ届いていない未来の日記を、届く順に並べる。本文は返さない。"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def execute(self, s: Session) -> list[FutureDiaryRecord]:
        query = (select(Diary)
                 .where(Diary.user_id == self.user_id, Diary.written_at.is_not(None), Diary.time > datetime.now(JST))
                 .order_by(Diary.time, Diary.id))
        return [FutureDiaryRecord.model_validate(row) for row in s.scalars(query)]
