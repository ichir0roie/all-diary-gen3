#!/usr/bin/env python3
from __future__ import annotations

import math
import operator
from functools import reduce

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from data_access_logic.diary.record import DiaryRecord, SimilarDiaries, SimilarDiary
from data_access_logic.entrypoint import SessionEntrypoint, loading
from data_access_logic.query.common_query import delivered
from db.schema import Diary

# 探す文章から取る二文字の組の数の上限。長い文章でも、問い合わせ一回の LIKE の数をこれで抑える
MAX_GRAMS = 48
# 探した文章の言葉の重みのうち、これだけの割合が出てくる日記を「似ている」とする
MIN_SCORE = 0.3


def _is_hiragana(char: str) -> bool:
    return "ぁ" <= char <= "ゟ"


def grams(text: str) -> list[str]:
    """文章を二文字ずつに切る(日本語は単語の区切りが無いので、二文字の組を言葉の代わりにする)。
    句読点・空白をまたぐ組と、ひらがなだけの組(「した」「って」のような、どの日記にも出る組)は捨てる。出てくる順で重ねない。"""
    found: dict[str, None] = {}
    for first, second in zip(text, text[1:]):
        if first.isalnum() and second.isalnum() and not (_is_hiragana(first) and _is_hiragana(second)):
            found.setdefault((first + second).lower())
    unique = list(found)
    if len(unique) <= MAX_GRAMS:
        return unique
    # 長い文章は、頭に偏らないよう全体から等間隔に取る
    return [unique[i * len(unique) // MAX_GRAMS] for i in range(MAX_GRAMS)]


class SearchSimilarDiaries(SessionEntrypoint):
    """`text` に似た日記を、似ている順に `limit` 件まで返す。`total` は似た日記の全部の数。

    文章を二文字の組に切り、組ごとに、その人の日記のうちいくつに出てくるかで重みを付ける(どの日記にも出る組ほど軽い)。
    `text` の組の重みのうち `MIN_SCORE` 以上が出てくる日記を、似た日記とする。拡張(pg_trgm など)は使わず、LIKE で数える。"""

    def __init__(self, user_id: str, text: str, limit: int = 50):
        self.user_id = user_id
        self.text = text
        self.limit = limit

    def execute(self, s: Session) -> SimilarDiaries:
        none = SimilarDiaries(total=0, diaries=[])
        found = grams(self.text)
        if not found:
            return none
        own = and_(Diary.user_id == self.user_id, delivered())
        matches = [Diary.text.icontains(gram, autoescape=True) for gram in found]
        counts = s.execute(select(func.count(), *(func.count().filter(match) for match in matches)).where(own)).one()
        total_diaries, frequencies = counts[0], counts[1:]
        # 日記が一件も持たない組は、どの日記の点も上げないので除く(書いたことのない言葉で、他の言葉の一致が薄まらないように)
        weighted = [(match, math.log((total_diaries + 1) / (frequency + 1)))
                    for match, frequency in zip(matches, frequencies) if frequency > 0]
        full = sum(weight for _, weight in weighted)
        if full <= 0:
            return none
        matched = reduce(operator.add, (case((match, weight), else_=0.0) for match, weight in weighted))
        score = (matched / full).label("score")
        query = (select(Diary, score, func.count().over().label("total"))
                 .where(own, score >= MIN_SCORE)
                 .order_by(score.desc(), Diary.time.desc(), Diary.id)
                 .limit(self.limit))
        rows = s.execute(loading(query, DiaryRecord)).all()
        if not rows:
            return none
        return SimilarDiaries(total=rows[0].total, diaries=[
            SimilarDiary(score=round(row.score, 3), diary=DiaryRecord.model_validate(row.Diary)) for row in rows])
