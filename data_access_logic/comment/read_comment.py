#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.comment.record import CommentRecord
from data_access_logic.entrypoint import SessionEntrypoint
from data_access_logic.query.common_query import own_row
from db.schema import Comment


class ReadComment(SessionEntrypoint):
    def __init__(self, user_id: str, comment_id: int):
        self.user_id = user_id
        self.comment_id = comment_id

    def execute(self, s: Session) -> CommentRecord:
        return CommentRecord.model_validate(own_row(s, Comment, self.comment_id, self.user_id))
