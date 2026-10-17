#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import own_row
from data_access_logic.tag.record import DeletedTag
from db.schema import Comment, Diary, Tag


class DeleteTag(CommitEntrypoint):
    """タグを消す。付いていた日記・コメントは消さず、タグ無し(`tag_id` が NULL)に戻す。"""

    def __init__(self, user_id: str, tag_id: int):
        self.user_id = user_id
        self.tag_id = tag_id

    def execute(self, s: Session) -> DeletedTag:
        record = own_row(s, Tag, self.tag_id, self.user_id)
        deleted = DeletedTag(
            id=record.id,
            diaries=s.scalar(select(func.count()).where(Diary.tag_id == record.id)) or 0,
            comments=s.scalar(select(func.count()).where(Comment.tag_id == record.id)) or 0)
        # 日記・コメントの tag_id は、外部キーの ON DELETE SET NULL で db が NULL にする
        s.delete(record)
        s.flush()
        return deleted
