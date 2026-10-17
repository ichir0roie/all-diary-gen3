#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.diary.record import DiaryRecord
from data_access_logic.entrypoint import CommitEntrypoint, record_of
from data_access_logic.query.common_query import own_diary, own_row
from data_access_logic.tag.form import TagChoiceForm
from db.schema import Tag


class SetDiaryTag(CommitEntrypoint):
    """日記にタグを付ける(`tag_id` が None なら外す)。付けられるのは自分のタグだけ。本文と時刻は変えない。"""

    def __init__(self, user_id: str, diary_id: int, tag: TagChoiceForm):
        self.user_id = user_id
        self.diary_id = diary_id
        self.tag = tag

    def execute(self, s: Session) -> DiaryRecord:
        record = own_diary(s, self.diary_id, self.user_id)
        if self.tag.tag_id is not None:
            own_row(s, Tag, self.tag.tag_id, self.user_id)
        self.tag.write_to(record)
        self.finalize(s, record)
        return record_of(s, DiaryRecord, record)
