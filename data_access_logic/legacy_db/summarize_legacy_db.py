#!/usr/bin/env python3
from __future__ import annotations

from itertools import groupby

from data_access_logic.entrypoint import Entrypoint
from data_access_logic.legacy_db import reading
from data_access_logic.legacy_db.record import LegacyDbSummary, LegacyUser


class SummarizeLegacyDb(Entrypoint):
    """以前の SQLite の db ファイルに、誰の日記が何件、いつからいつまであるかを返す。db(RDS)には触れない。
    `ImportLegacyDb` の `source_user_id` を選ぶのに使う。"""

    def __init__(self, sqlite_bytes: bytes):
        self.sqlite_bytes = sqlite_bytes

    def result(self) -> LegacyDbSummary:
        with reading.opened(self.sqlite_bytes) as conn:
            diaries = sorted(reading.diaries(conn), key=lambda row: row.user_id)
            comment_counts: dict[str, int] = {}
            linked, unlinked = reading.comments(conn)
            for comment in linked:
                comment_counts[comment.user_id] = comment_counts.get(comment.user_id, 0) + 1
        users = []
        for user_id, rows in groupby(diaries, key=lambda row: row.user_id):
            times = [row.time for row in rows]
            users.append(LegacyUser(user_id=user_id, diaries=len(times), comments=comment_counts.get(user_id, 0),
                                    first_time=min(times), last_time=max(times)))
        return LegacyDbSummary(users=sorted(users, key=lambda user: user.diaries, reverse=True), unlinked_comments=unlinked)
