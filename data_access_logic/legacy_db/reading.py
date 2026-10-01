#!/usr/bin/env python3
"""以前の API(`all_diary_backend`)の SQLite の db ファイルを読む。

以前の表は `diary(id, user_id, migration_id, time, text)` と `comment(id, user_id, migration_id, time, text, diary_id)`。
時刻は日本時間を時差無しで持っている(`.docs/postgres.md` の「時刻」)。
以前の CSV の取り込み(pandas)が書いたコメントの `diary_id` は、整数でなく 8 バイトのバイナリ(numpy の int64 のまま)で入っていて、
SQL の結合では日記に結び付かない。そのため、コメントは python で日記を引く。
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

from pydantic import BaseModel, ConfigDict

from data_access_logic.material import JstTime

SQLITE_HEADER = b"SQLite format 3\x00"
LEGACY_TABLES = {"diary", "comment"}


class LegacyDiaryRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    user_id: str
    time: JstTime
    text: str


class LegacyCommentRow(LegacyDiaryRow):
    diary_id: int


@contextmanager
def opened(sqlite_bytes: bytes) -> Iterator[sqlite3.Connection]:
    """受け取ったファイルを読むだけで開く。sqlite3 はファイルの道でしか開けないので、一時ファイルに書いてから開く。"""
    if not sqlite_bytes.startswith(SQLITE_HEADER):
        raise ValueError("SQLite の db ファイルではない")
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "legacy.db")
        with open(path, "wb") as f:
            f.write(sqlite_bytes)
        conn = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            missing = sorted(LEGACY_TABLES - tables)
            if missing:
                raise ValueError(f"以前の日記の db ではない(表 {', '.join(missing)} が無い)")
            yield conn
        except sqlite3.DatabaseError as e:
            raise ValueError(f"db ファイルが読めない: {e}") from e
        finally:
            conn.close()


def diaries(conn: sqlite3.Connection, source_user_id: str | None = None) -> list[LegacyDiaryRow]:
    query = "SELECT id, user_id, time, text FROM diary"
    rows = conn.execute(query + " WHERE user_id = ? ORDER BY time, id", (source_user_id,)) if source_user_id is not None \
        else conn.execute(query + " ORDER BY time, id")
    return [LegacyDiaryRow.model_validate(dict(row)) for row in rows]


def _integer(value: int | bytes) -> int:
    return int.from_bytes(value, "little", signed=True) if isinstance(value, bytes) else value


def comments(conn: sqlite3.Connection, source_user_id: str | None = None) -> tuple[list[LegacyCommentRow], int]:
    """日記の持ち主で絞ったコメントと、どの日記にも結び付かないコメントの数。
    持ち主はコメントの `user_id` でなく日記の持ち主で見る(以前の db は、他の人の日記へのコメントも書けた)。"""
    owners: dict[int, str] = dict(conn.execute("SELECT id, user_id FROM diary").fetchall())
    found = []
    unlinked = 0
    for row in conn.execute("SELECT id, time, text, diary_id FROM comment ORDER BY time, id"):
        diary_id = _integer(row["diary_id"])
        owner = owners.get(diary_id)
        if owner is None:
            unlinked += 1
        elif source_user_id is None or owner == source_user_id:
            found.append(LegacyCommentRow(id=row["id"], user_id=owner, time=row["time"], text=row["text"], diary_id=diary_id))
    return found, unlinked
