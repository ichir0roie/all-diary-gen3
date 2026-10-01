#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.csv_file.record import Imported
from data_access_logic.csv_file.rows import DiaryCsvRow, read_rows
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.import_query import DiaryKey, existing_diaries
from db.schema import Diary


class ImportDiaryCsv(CommitEntrypoint):
    """日記の CSV(`id,text,time`)を `user_id` の人の日記として足す。CSV の id は `migration_id` に残し、
    コメントの CSV の `diary_id` はそれで日記を引く。時刻と本文が同じ日記は、CSV の中では一件にし、db に既にあれば足さない。"""

    def __init__(self, user_id: str, csv_text: str):
        self.user_id = user_id
        self.csv_text = csv_text

    def execute(self, s: Session) -> Imported:
        rows = read_rows(self.csv_text, DiaryCsvRow)
        # 同じ日記が二行あれば先の行を取り、その id を migration_id に残す(コメントの CSV が指すのは先の行の id と見る)
        unique: dict[DiaryKey, DiaryCsvRow] = {}
        for row in rows:
            unique.setdefault((row.time, row.text), row)
        existing = existing_diaries(s, self.user_id, unique)
        added = [row for key, row in unique.items() if key not in existing]
        s.add_all(Diary(user_id=self.user_id, migration_id=row.id, time=row.time, text=row.text) for row in added)
        return Imported(added=len(added), skipped=len(rows) - len(added))
