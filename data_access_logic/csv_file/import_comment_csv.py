#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.csv_file.record import Imported
from data_access_logic.csv_file.rows import CommentCsvRow, read_rows
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.import_query import CommentKey, existing_comments
from db.schema import Comment, Diary


class ImportCommentCsv(CommitEntrypoint):
    """コメントの CSV(`id,diary_id,text,time`)を `user_id` の人のコメントとして足す。`diary_id` は日記の CSV の id で、
    先に取り込んだ日記(`migration_id`)を指す。同じ日記の、時刻と本文が同じコメントは、CSV の中では一件にし、db に既にあれば足さない。"""

    def __init__(self, user_id: str, csv_text: str):
        self.user_id = user_id
        self.csv_text = csv_text

    def execute(self, s: Session) -> Imported:
        rows = read_rows(self.csv_text, CommentCsvRow)
        diary_ids = self._diary_ids(s, {row.diary_id for row in rows})
        unique: dict[CommentKey, CommentCsvRow] = {}
        for row in rows:
            unique.setdefault((diary_ids[row.diary_id], row.time, row.text), row)
        existing = existing_comments(s, unique)
        added = [(key, row) for key, row in unique.items() if key not in existing]
        s.add_all(Comment(user_id=self.user_id, diary_id=diary_id, migration_id=row.id, time=row.time, text=row.text)
                  for (diary_id, _, _), row in added)
        return Imported(added=len(added), skipped=len(rows) - len(added))

    def _diary_ids(self, s: Session, migration_ids: set[int]) -> dict[int, int]:
        found = s.execute(select(Diary.migration_id, Diary.id)
                          .where(Diary.user_id == self.user_id, Diary.migration_id.in_(list(migration_ids)))).all()
        duplicated = sorted(migration_id for migration_id, count in Counter(m for m, _ in found).items() if count > 1)
        if duplicated:
            raise ValueError(f"diary_id={duplicated} を migration_id に持つ日記が複数ある。どの日記へのコメントか決められない")
        diary_ids = {migration_id: id_ for migration_id, id_ in found if migration_id is not None}
        missing = sorted(migration_ids - set(diary_ids))
        if missing:
            raise ValueError(f"diary_id={missing} の日記が無い。先に日記の CSV を取り込む")
        return diary_ids
