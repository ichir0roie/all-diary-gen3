from typing import ClassVar

from sqlalchemy.orm import selectinload

from data_access_logic.material import JstTime, Material
from data_access_logic.tag.record import TagRecord
from db.schema import Comment


class CommentRecord(Material):
    LOAD_OPTIONS: ClassVar[tuple] = (selectinload(Comment.tag),)

    id: int
    diary_id: int
    time: JstTime
    tag: TagRecord | None
    text: str


class DeletedComment(Material):
    id: int
    diary_id: int
