#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import SessionEntrypoint, UnknownRecordError, loading
from data_access_logic.query.common_query import delivered
from db.schema import Comment, Diary, Tag


class ListTaggedDiaries(SessionEntrypoint):
    """`tag_ids` のタグのどれかが、日記か、そのコメントのどれかに付いた日記を、コメント付きで新しい順に並べる。
    まだ届いていない未来の日記は除く。"""

    def __init__(self, user_id: str, tag_ids: list[int]):
        self.user_id = user_id
        self.tag_ids = tag_ids

    def execute(self, s: Session) -> list[DiaryRecord]:
        own_tag_ids = set(s.scalars(select(Tag.id).where(Tag.id.in_(self.tag_ids), Tag.user_id == self.user_id)))
        # 他の人のタグも、無いタグと同じに扱う(在ることを漏らさない)
        unknown = sorted(set(self.tag_ids) - own_tag_ids)
        if unknown:
            raise UnknownRecordError(f"id={unknown} の tag が見つからない")
        commented = select(Comment.diary_id).where(Comment.tag_id.in_(own_tag_ids))
        query = (select(Diary)
                 .where(Diary.user_id == self.user_id, delivered(),
                        or_(Diary.tag_id.in_(own_tag_ids), Diary.id.in_(commented)))
                 .order_by(Diary.time.desc(), Diary.id.desc()))
        return [DiaryRecord.model_validate(row) for row in s.scalars(loading(query, DiaryRecord))]
