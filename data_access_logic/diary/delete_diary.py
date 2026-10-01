#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import DeletedDiary
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import own_diary
from db.schema import Comment


class DeleteDiary(CommitEntrypoint):
    """日記を、付いたコメントごと消す。"""

    def __init__(self, user_id: str, diary_id: int):
        self.user_id = user_id
        self.diary_id = diary_id

    def execute(self, s: Session) -> DeletedDiary:
        record = own_diary(s, self.diary_id, self.user_id)
        comments = s.scalars(select(Comment).where(Comment.diary_id == record.id)).all()
        for comment in comments:
            s.delete(comment)
        # コメントが日記を指しているので、コメントを先に消してから日記を消す
        s.flush()
        s.delete(record)
        s.flush()
        return DeletedDiary(id=self.diary_id, comments=len(comments))
