#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.comment.form import CommentUpdateForm
from data_access_logic.comment.record import CommentRecord
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import own_row
from db.schema import Comment


class UpdateComment(CommitEntrypoint):
    """コメントの本文を書き直す。書いた時刻は変えない。"""

    def __init__(self, user_id: str, comment_id: int, comment: CommentUpdateForm):
        self.user_id = user_id
        self.comment_id = comment_id
        self.comment = comment

    def execute(self, s: Session) -> CommentRecord:
        record = own_row(s, Comment, self.comment_id, self.user_id)
        self.comment.write_to(record)
        self.finalize(s, record)
        return CommentRecord.model_validate(record)
