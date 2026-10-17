#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import TextTagged
from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import delivered, own_tags, tag_in_text, tags_to_match
from db.schema import Diary


class TagDiariesByText(CommitEntrypoint):
    """本文に `tag_ids` のタグのどれかの名前が含まれ、まだタグの無い日記に、タグを付ける。付けるタグは `CommitDiary` と同じく、
    自分のタグのうち本文に名前が含まれる、名前の長いもの。手で付けたかもしれないので、タグの付いた日記は書き換えない。
    まだ届いていない未来の日記には付けない。"""

    def __init__(self, user_id: str, tag_ids: list[int]):
        if not tag_ids:
            raise ValueError("tag_ids を一つ以上渡す")
        self.user_id = user_id
        self.tag_ids = tag_ids

    def execute(self, s: Session) -> TextTagged:
        mentioned = [Diary.text.contains(tag.name, autoescape=True) for tag in own_tags(s, self.user_id, self.tag_ids)]
        query = select(Diary).where(Diary.user_id == self.user_id, Diary.tag_id.is_(None), delivered(), or_(*mentioned))
        tags = tags_to_match(s, self.user_id)
        tagged = 0
        for diary in s.scalars(query).all():
            tag = tag_in_text(tags, diary.text)
            if tag is not None:
                diary.tag_id = tag.id
                tagged += 1
        s.flush()
        return TextTagged(diaries=tagged)
