#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.entrypoint import CommitEntrypoint
from data_access_logic.query.common_query import refuse_taken_tag_name
from data_access_logic.tag.form import TagCreateForm
from data_access_logic.tag.record import TagRecord
from db.schema import Tag


class CommitTag(CommitEntrypoint):
    """タグを作る。同じ人の中で、既にある名前は作れない。"""

    def __init__(self, user_id: str, tag: TagCreateForm):
        self.user_id = user_id
        self.tag = tag

    def execute(self, s: Session) -> TagRecord:
        refuse_taken_tag_name(s, self.user_id, self.tag.name)
        record = Tag(user_id=self.user_id)
        self.tag.write_to(record)
        s.add(record)
        self.finalize(s, record)
        return TagRecord.model_validate(record)
