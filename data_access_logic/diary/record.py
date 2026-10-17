from datetime import date
from typing import ClassVar

from sqlalchemy.orm import selectinload

from data_access_logic.comment.record import CommentRecord
from data_access_logic.material import JstTime, Material
from data_access_logic.tag.record import TagRecord
from db.schema import Comment, Diary


class DiaryRecord(Material):
    LOAD_OPTIONS: ClassVar[tuple] = (selectinload(Diary.tag), selectinload(Diary.comments).selectinload(Comment.tag))

    id: int
    time: JstTime
    # 未来へ送った日記の、書いた時刻(`time` は届いた時刻)。ふだんの日記は None
    written_at: JstTime | None
    tag: TagRecord | None
    text: str
    comments: list[CommentRecord]


class DeletedDiary(Material):
    id: int
    # 日記と一緒に消したコメントの数
    comments: int


class FutureDiaryRecord(Material):
    """封をした未来の日記。届くまで本文は返さない。"""

    id: int
    # 届く時刻
    time: JstTime
    written_at: JstTime


class OnThisDayYear(Material):
    """ある年の、同じ月日の前後の日記。"""

    year: int
    start_date: date
    end_date: date
    diaries: list[DiaryRecord]


class DiarySpan(Material):
    """頼まれた日付の範囲(両端を含む)と、その間の日記。"""

    start_date: date
    end_date: date
    diaries: list[DiaryRecord]


class DayCount(Material):
    """日本時間の暦の日ごとの、日記の件数と文字数。"""

    day: date
    diaries: int
    chars: int


class SimilarDiary(Material):
    # 0 から 1。探した文章の言葉(二文字ずつ)のうち、この日記に出てくるものの重みの割合
    score: float
    diary: DiaryRecord


class SimilarDiaries(Material):
    # 似た日記の数。`diaries` は似ている順の頭の何件か
    total: int
    diaries: list[SimilarDiary]
