#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy.orm import Session

from data_access_logic.diary.record import SimilarDiaries
from data_access_logic.diary.search_similar_diaries import SearchSimilarDiaries
from data_access_logic.entrypoint import SessionEntrypoint
from data_access_logic.query.common_query import own_diary


class ListSimilarDiaries(SessionEntrypoint):
    """日記一件に似た日記を、似ている順に `limit` 件まで返す(元の日記は除く)。似ているかの決め方は `SearchSimilarDiaries`。"""

    def __init__(self, user_id: str, diary_id: int, limit: int = 50):
        self.user_id = user_id
        self.diary_id = diary_id
        self.limit = limit

    def execute(self, s: Session) -> SimilarDiaries:
        diary = own_diary(s, self.diary_id, self.user_id)
        return SearchSimilarDiaries(self.user_id, diary.text, limit=self.limit, exclude_diary_id=diary.id).execute(s)
