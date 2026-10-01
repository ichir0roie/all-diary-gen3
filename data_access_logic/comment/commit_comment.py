#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from data_access_logic.comment.form import CommentCreateForm
from data_access_logic.comment.record import CommentRecord
from data_access_logic.constants import JST
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import own_diary
from db.schema import Comment


class CommitComment(CommitEntrypoint):
    """自分の日記にだけコメントを足せる。まだ届いていない未来の日記には足せない。"""

    def __init__(self, user_id: str, comment: CommentCreateForm):
        self.user_id = user_id
        self.comment = comment

    def execute(self, s: Session) -> CommentRecord:
        own_diary(s, self.comment.diary_id, self.user_id)
        record = Comment(user_id=self.user_id)
        self.comment.write_to(record)
        record.time = self.comment.time or datetime.now(JST)
        s.add(record)
        self.finalize(s, record)
        return CommentRecord.model_validate(record)
