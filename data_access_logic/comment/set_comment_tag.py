#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.comment.record import CommentRecord
from data_access_logic.entrypoint import CommitEntrypoint, record_of
from data_access_logic.query.common_query import own_row
from data_access_logic.tag.form import TagChoiceForm
from db.schema import Comment, Tag


class SetCommentTag(CommitEntrypoint):
    """コメントにタグを付ける(`tag_id` が None なら外す)。付けられるのは自分のタグだけ。本文と時刻は変えない。"""

    def __init__(self, user_id: str, comment_id: int, tag: TagChoiceForm):
        self.user_id = user_id
        self.comment_id = comment_id
        self.tag = tag

    def execute(self, s: Session) -> CommentRecord:
        record = own_row(s, Comment, self.comment_id, self.user_id)
        if self.tag.tag_id is not None:
            own_row(s, Tag, self.tag.tag_id, self.user_id)
        self.tag.write_to(record)
        self.finalize(s, record)
        return record_of(s, CommentRecord, record)
