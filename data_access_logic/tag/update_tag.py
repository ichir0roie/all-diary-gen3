#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import own_row, refuse_taken_tag_name
from data_access_logic.tag.form import TagUpdateForm
from data_access_logic.tag.record import TagRecord
from db.schema import Tag


class UpdateTag(CommitEntrypoint):
    """タグの名前を変える。付けた日記・コメントは、そのまま新しい名前のタグを持つ。"""

    def __init__(self, user_id: str, tag_id: int, tag: TagUpdateForm):
        self.user_id = user_id
        self.tag_id = tag_id
        self.tag = tag

    def execute(self, s: Session) -> TagRecord:
        record = own_row(s, Tag, self.tag_id, self.user_id)
        refuse_taken_tag_name(s, self.user_id, self.tag.name, exclude_tag_id=record.id)
        self.tag.write_to(record)
        self.finalize(s, record)
        return TagRecord.model_validate(record)
