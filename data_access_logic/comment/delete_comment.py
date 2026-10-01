#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.comment.record import DeletedComment
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import own_row
from db.schema import Comment


class DeleteComment(CommitEntrypoint):
    def __init__(self, user_id: str, comment_id: int):
        self.user_id = user_id
        self.comment_id = comment_id

    def execute(self, s: Session) -> DeletedComment:
        record = own_row(s, Comment, self.comment_id, self.user_id)
        deleted = DeletedComment.model_validate(record)
        s.delete(record)
        s.flush()
        return deleted
