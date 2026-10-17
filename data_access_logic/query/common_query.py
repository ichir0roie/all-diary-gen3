#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session

from data_access_logic.constants import JST
from data_access_logic.entrypoint import UnknownRecordError
from db.schema import Comment, Diary, Tag


def own_row[M: Diary | Comment | Tag](s: Session, model: type[M], id_: int, user_id: str) -> M:
    """`user_id` の人が書いた行だけを返す。他の人の行も、無い行と同じに扱う(在ることを漏らさない)。"""
    row = s.get(model, id_)
    if row is None or row.user_id != user_id:
        raise UnknownRecordError(f"id={id_} の {model.__tablename__} が見つからない")
    return row


def in_days(column, start_date: date | None, end_date: date | None) -> list[ColumnElement[bool]]:
    """日本時間の `start_date` の 0 時から、`end_date` の翌日の 0 時の前まで。省いた端は限らない。"""
    conditions = []
    if start_date is not None:
        conditions.append(column >= datetime.combine(start_date, time(), JST))
    if end_date is not None:
        conditions.append(column < datetime.combine(end_date + timedelta(days=1), time(), JST))
    return conditions


def delivered() -> ColumnElement[bool]:
    """封をした未来の日記(届く時刻の前)を除く。"""
    return or_(Diary.written_at.is_(None), Diary.time <= datetime.now(JST))


def own_diary(s: Session, diary_id: int, user_id: str) -> Diary:
    """`own_row` に加え、まだ届いていない未来の日記も、無い行と同じに扱う(届くまで読むことも書き足すこともできない)。"""
    diary = own_row(s, Diary, diary_id, user_id)
    if diary.written_at is not None and diary.time > datetime.now(JST):
        raise UnknownRecordError(f"id={diary_id} の diary が見つからない")
    return diary


def refuse_taken_tag_name(s: Session, user_id: str, name: str, exclude_tag_id: int | None = None) -> None:
    """同じ人が同じ名前のタグを既に持っていれば止める(名前を変えるときは、変える当のタグを除いて比べる)。"""
    query = select(Tag.id).where(Tag.user_id == user_id, Tag.name == name)
    if exclude_tag_id is not None:
        query = query.where(Tag.id != exclude_tag_id)
    if s.scalar(query) is not None:
        raise ValueError(f"タグ「{name}」は既にある")


def own_tags(s: Session, user_id: str, tag_ids: list[int]) -> list[Tag]:
    """`tag_ids` のタグ。他の人のタグが混ざれば、無いタグと同じに扱って止める(在ることを漏らさない)。"""
    tags = list(s.scalars(select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)))
    unknown = sorted(set(tag_ids) - {tag.id for tag in tags})
    if unknown:
        raise UnknownRecordError(f"id={unknown} の tag が見つからない")
    return tags


def tags_to_match(s: Session, user_id: str) -> list[Tag]:
    """`user_id` の人のタグを、本文に当てはめる順に(名前の長いものから。「旅行」より「海外旅行」を先に)。"""
    return list(s.scalars(select(Tag)
                          .where(Tag.user_id == user_id)
                          .order_by(func.char_length(Tag.name).desc(), Tag.name, Tag.id)))


def tag_in_text(tags: list[Tag], text: str) -> Tag | None:
    """`tags`(`tags_to_match` の順)のうち、`text` に名前が含まれる最初のタグ。"""
    return next((tag for tag in tags if tag.name in text), None)
