#!/usr/bin/env python3
"""取り込み(CSV・以前の db ファイル)が、取り込み直しても行を重ねないための問い合わせ。時刻と本文がどちらも同じ行を同じものとみなす。"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.schema import Comment, Diary

type DiaryKey = tuple[datetime, str]
type CommentKey = tuple[int, datetime, str]


def existing_diaries(s: Session, user_id: str, keys: Iterable[DiaryKey]) -> dict[DiaryKey, int]:
    """`keys`(時刻と本文)のうち、`user_id` の人の日記に既にあるものと、その日記の id。"""
    wanted = set(keys)
    if not wanted:
        return {}
    rows = s.execute(select(Diary.time, Diary.text, Diary.id)
                     .where(Diary.user_id == user_id, Diary.time.in_([time for time, _ in wanted]))).all()
    return {(time, text): id_ for time, text, id_ in rows if (time, text) in wanted}


def existing_comments(s: Session, keys: Iterable[CommentKey]) -> set[CommentKey]:
    """`keys`(日記の id・時刻・本文)のうち、既にあるコメント。"""
    wanted = set(keys)
    if not wanted:
        return set()
    rows = s.execute(select(Comment.diary_id, Comment.time, Comment.text)
                     .where(Comment.diary_id.in_({diary_id for diary_id, _, _ in wanted}))).all()
    return {(diary_id, time, text) for diary_id, time, text in rows if (diary_id, time, text) in wanted}
