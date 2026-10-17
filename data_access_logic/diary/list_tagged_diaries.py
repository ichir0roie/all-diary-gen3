#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import SessionEntrypoint, loading
from data_access_logic.query.common_query import delivered, own_tags
from db.schema import Comment, Diary


class ListTaggedDiaries(SessionEntrypoint):
    """`tag_ids` のタグのどれかが、日記か、そのコメントのどれかに付いた日記と、本文にそのタグの名前が含まれる日記を、
    コメント付きで新しい順に並べる。まだ届いていない未来の日記は除く。"""

    def __init__(self, user_id: str, tag_ids: list[int]):
        self.user_id = user_id
        self.tag_ids = tag_ids

    def execute(self, s: Session) -> list[DiaryRecord]:
        tags = own_tags(s, self.user_id, self.tag_ids)
        tag_ids = [tag.id for tag in tags]
        commented = select(Comment.diary_id).where(Comment.tag_id.in_(tag_ids))
        mentioned = [Diary.text.contains(tag.name, autoescape=True) for tag in tags]
        query = (select(Diary)
                 .where(Diary.user_id == self.user_id, delivered(),
                        or_(Diary.tag_id.in_(tag_ids), Diary.id.in_(commented), *mentioned))
                 .order_by(Diary.time.desc(), Diary.id.desc()))
        return [DiaryRecord.model_validate(row) for row in s.scalars(loading(query, DiaryRecord))]
