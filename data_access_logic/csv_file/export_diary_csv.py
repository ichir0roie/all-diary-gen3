#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.csv_file.record import CsvDump
from data_access_logic.csv_file.rows import DiaryCsvRow, write_rows
from data_access_logic.entrypoint import SessionEntrypoint
from db.schema import Diary


class ExportDiaryCsv(SessionEntrypoint):
    """`user_id` の人の日記を、`ImportDiaryCsv` で取り込み直せる CSV(`id,text,time`)にする。"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def execute(self, s: Session) -> CsvDump:
        rows = [DiaryCsvRow.model_validate(row)
                for row in s.scalars(select(Diary).where(Diary.user_id == self.user_id).order_by(Diary.time, Diary.id))]
        return CsvDump(text=write_rows(rows, ["id", "text", "time"]), rows=len(rows))
