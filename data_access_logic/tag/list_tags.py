#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data_access_logic.entrypoint import SessionEntrypoint
from data_access_logic.tag.record import TagRecord, TagUsage
from db.schema import Comment, Diary, Tag


class ListTags(SessionEntrypoint):
    """`user_id` の人のタグを名前の順に、付けた日記・コメントの数と並べる。"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def execute(self, s: Session) -> list[TagUsage]:
        diaries = select(func.count()).where(Diary.tag_id == Tag.id).correlate(Tag).scalar_subquery()
        comments = select(func.count()).where(Comment.tag_id == Tag.id).correlate(Tag).scalar_subquery()
        query = (select(Tag, diaries.label("diaries"), comments.label("comments"))
                 .where(Tag.user_id == self.user_id)
                 .order_by(Tag.name, Tag.id))
        return [TagUsage(tag=TagRecord.model_validate(row.Tag), diaries=row.diaries, comments=row.comments)
                for row in s.execute(query)]
