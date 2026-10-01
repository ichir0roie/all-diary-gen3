#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.csv_file.record import CsvDump
from data_access_logic.csv_file.rows import CommentCsvRow, write_rows
from data_access_logic.entrypoint import SessionEntrypoint
from db.schema import Comment


class ExportCommentCsv(SessionEntrypoint):
    """`user_id` の人のコメントを、`ImportCommentCsv` で取り込み直せる CSV(`id,diary_id,text,time`)にする。
    `diary_id` は日記の id(`ExportDiaryCsv` の id)。"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def execute(self, s: Session) -> CsvDump:
        rows = [CommentCsvRow.model_validate(row)
                for row in s.scalars(select(Comment).where(Comment.user_id == self.user_id)
                                     .order_by(Comment.time, Comment.id))]
        return CsvDump(text=write_rows(rows, ["id", "diary_id", "text", "time"]), rows=len(rows))
