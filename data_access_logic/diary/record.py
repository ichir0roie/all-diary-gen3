from typing import ClassVar

from sqlalchemy.orm import selectinload

from data_access_logic.comment.record import CommentRecord
from data_access_logic.material import JstTime, Material
from db.schema import Diary


class DiaryRecord(Material):
    LOAD_OPTIONS: ClassVar[tuple] = (selectinload(Diary.comments),)

    id: int
    time: JstTime
    text: str
    comments: list[CommentRecord]
