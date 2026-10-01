#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.csv_file.record import Imported
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.legacy_db import reading
from data_access_logic.legacy_db.record import LegacyImported
from data_access_logic.query.import_query import existing_comments, existing_diaries
from db.schema import Comment, Diary


class ImportLegacyDb(CommitEntrypoint):
    """以前の SQLite の db ファイルから、`source_user_id`(以前の Cognito のユーザーの sub。`SummarizeLegacyDb` で選ぶ)の日記と
    その日記へのコメントを、`user_id` の人の行として足す。以前の id は `migration_id` に残す。
    時刻と本文が同じ日記・コメントが db に既にあれば足さないので、新しい db ファイルで取り込み直せば、増えた分だけが入る。
    コメントは、このファイルの中の日記の id で日記を引く(既にあった日記へのコメントも、その日記に付ける)。"""

    def __init__(self, user_id: str, sqlite_bytes: bytes, source_user_id: str):
        self.user_id = user_id
        self.sqlite_bytes = sqlite_bytes
        self.source_user_id = source_user_id

    def execute(self, s: Session) -> LegacyImported:
        with reading.opened(self.sqlite_bytes) as conn:
            legacy_diaries = reading.diaries(conn, self.source_user_id)
            legacy_comments, _ = reading.comments(conn, self.source_user_id)
        if not legacy_diaries:
            raise ValueError(f"db ファイルに user_id={self.source_user_id} の日記が無い")

        unique_diaries = {(row.time, row.text): row for row in legacy_diaries}
        existing = existing_diaries(s, self.user_id, unique_diaries)
        added_diaries = {key: Diary(user_id=self.user_id, migration_id=row.id, time=row.time, text=row.text)
                         for key, row in unique_diaries.items() if key not in existing}
        s.add_all(added_diaries.values())
        s.flush()
        new_ids = {**existing, **{key: diary.id for key, diary in added_diaries.items()}}
        diary_ids = {row.id: new_ids[(row.time, row.text)] for row in legacy_diaries}

        unique_comments = {(diary_ids[row.diary_id], row.time, row.text): row for row in legacy_comments}
        existing_keys = existing_comments(s, unique_comments)
        added_comments = [(key, row) for key, row in unique_comments.items() if key not in existing_keys]
        s.add_all(Comment(user_id=self.user_id, diary_id=diary_id, migration_id=row.id, time=row.time, text=row.text)
                  for (diary_id, _, _), row in added_comments)
        return LegacyImported(
            diaries=Imported(added=len(added_diaries), skipped=len(legacy_diaries) - len(added_diaries)),
            comments=Imported(added=len(added_comments), skipped=len(legacy_comments) - len(added_comments)))
