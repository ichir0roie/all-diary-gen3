#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.diary.form import DaySpanForm
from data_access_logic.diary.record import DiarySpan, DiaryRecord
from data_access_logic.entrypoint import SessionEntrypoint, loading
from data_access_logic.query.common_query import delivered, in_days
from db.schema import Diary

# 画面は見えている所の範囲(年の列ごとに一つか二つ)だけを頼むので、それを大きく越える頼みは断る
MAX_SPANS = 100


class ListDiariesInSpans(SessionEntrypoint):
    """`spans` の範囲ごとに、`user_id` の人の日記をコメント付きで時刻の順に並べ、頼まれた順に返す。まだ届いていない未来の日記は除く。
    範囲が重なれば、その日記はどちらにも入る。いくつもの範囲を一度の問い合わせで読む(画面が年ごとの列をまとめて読む)。"""

    def __init__(self, user_id: str, spans: list[DaySpanForm]):
        if not 1 <= len(spans) <= MAX_SPANS:
            raise ValueError(f"spans は 1 個から {MAX_SPANS} 個にする")
        if any(span.start_date > span.end_date for span in spans):
            raise ValueError("start_date は end_date より後にしない")
        self.user_id = user_id
        self.spans = spans

    def execute(self, s: Session) -> list[DiarySpan]:
        results = [DiarySpan(start_date=span.start_date, end_date=span.end_date, diaries=[]) for span in self.spans]
        query = (select(Diary)
                 .where(Diary.user_id == self.user_id, delivered(),
                        or_(*(and_(*in_days(Diary.time, span.start_date, span.end_date)) for span in self.spans)))
                 .order_by(Diary.time, Diary.id))
        for row in s.scalars(loading(query, DiaryRecord)):
            written_on = row.time.astimezone(JST).date()
            diary = DiaryRecord.model_validate(row)
            for result in results:
                if result.start_date <= written_on <= result.end_date:
                    result.diaries.append(diary)
        return results
