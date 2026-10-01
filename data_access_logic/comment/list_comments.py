#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from data_access_logic.comment.record import CommentRecord
from data_access_logic.entrypoint import SessionEntrypoint
from db.schema import Comment


class ListComments(SessionEntrypoint):
    """日記一件に付いたコメントを時刻の順に並べる。他の人の日記なら空。"""

    def __init__(self, user_id: str, diary_id: int):
        self.user_id = user_id
        self.diary_id = diary_id

    def execute(self, s: Session) -> list[CommentRecord]:
        query = (select(Comment)
                 .where(Comment.user_id == self.user_id, Comment.diary_id == self.diary_id)
                 .order_by(Comment.time, Comment.id))
        return [CommentRecord.model_validate(row) for row in s.scalars(query)]
