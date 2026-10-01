"""claude が CLI から `show()` で呼ぶ、以前の SQLite の db ファイルの取り込み(`data_access_logic/legacy_db/`)の入口。"""
import os
import sqlite3
import tempfile
import uuid

import pytest

from tests.legacy_files import LEGACY, LEGACY_COMMENTS, LEGACY_DIARIES, OLD_ME, OLD_OTHER, legacy_db
from data_access_logic.diary.list_diaries import ListDiaries
from data_access_logic.legacy_db.import_legacy_db import ImportLegacyDb
from data_access_logic.legacy_db.summarize_legacy_db import SummarizeLegacyDb


def test_summarize_legacy_db(shown):
    result = shown(SummarizeLegacyDb(LEGACY))

    assert result["users"] == [
        {"user_id": OLD_ME, "diaries": 3, "comments": 3,
         "first_time": "2026-03-01T21:00:00+09:00", "last_time": "2026-09-30T22:30:15.123000+09:00"},
        {"user_id": OLD_OTHER, "diaries": 1, "comments": 1,
         "first_time": "2026-03-01T21:00:00+09:00", "last_time": "2026-03-01T21:00:00+09:00"}]
    assert result["unlinked_comments"] == 1


def test_import_legacy_db(shown):
    user_id = f"test-{uuid.uuid4()}"

    result = shown(ImportLegacyDb(user_id, LEGACY, OLD_ME))

    # 同じ時刻でも本文の違う日記・コメントは、別の行として残す
    assert result == {"diaries": {"added": 3, "skipped": 0}, "comments": {"added": 3, "skipped": 0}}
    listed = ListDiaries(user_id).run()
    assert [(diary["text"], [comment["text"] for comment in diary["comments"]]) for diary in listed] == [
        ("三月一日", ["翌朝のコメント", "翌朝のコメントの続き"]), ("九月末", ["バイナリの diary_id"]), ("九月末の続き", [])]


def test_import_newer_legacy_db_adds_only_new_rows():
    user_id = f"test-{uuid.uuid4()}"
    ImportLegacyDb(user_id, LEGACY, OLD_ME).run()
    # 後から取り出した db ファイルには、日記とコメントが増えている(既にある日記へのコメントも)
    newer = legacy_db(LEGACY_DIARIES + [(6, OLD_ME, "2026-10-01 07:00:00.000000", "十月一日")],
                      LEGACY_COMMENTS + [(7, OLD_ME, 2, "2026-10-01 08:00:00.000000", "九月末へ")])

    result = ImportLegacyDb(user_id, newer, OLD_ME).run()

    assert result == {"diaries": {"added": 1, "skipped": 3}, "comments": {"added": 1, "skipped": 3}}
    assert [len(diary["comments"]) for diary in ListDiaries(user_id).run()] == [2, 2, 0, 0]


def test_import_unknown_source_user():
    with pytest.raises(ValueError, match="日記が無い"):
        ImportLegacyDb(f"test-{uuid.uuid4()}", LEGACY, "nobody").run()


def test_not_a_sqlite_file():
    with pytest.raises(ValueError, match="SQLite の db ファイルではない"):
        SummarizeLegacyDb(b"id,text,time\n").run()


def test_not_a_legacy_db():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "other.db")
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE something (id INTEGER)")
        conn.commit()
        conn.close()
        with open(path, "rb") as f:
            other = f.read()

    with pytest.raises(ValueError, match="表 comment, diary が無い"):
        SummarizeLegacyDb(other).run()
