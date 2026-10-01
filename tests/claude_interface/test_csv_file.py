"""claude が CLI から `show()` で呼ぶ、CSV の出し入れ(`data_access_logic/csv_file/`)の入口。"""
import uuid
from datetime import datetime, timedelta

import pytest

from data_access_logic.csv_file.export_comment_csv import ExportCommentCsv
from data_access_logic.csv_file.export_diary_csv import ExportDiaryCsv
from data_access_logic.csv_file.import_comment_csv import ImportCommentCsv
from data_access_logic.csv_file.import_diary_csv import ImportDiaryCsv
from data_access_logic.constants import JST
from data_access_logic.diary.form import FutureDiaryCreateForm
from data_access_logic.diary.list_diaries import ListDiaries
from data_access_logic.diary.list_future_diaries import ListFutureDiaries
from data_access_logic.diary.send_future_diary import SendFutureDiary
from db.schema import get_env_session

# 以前の db から書き出した CSV の形(列の並び・時刻の書式)
LEGACY_DIARY_CSV = """user_id,text,id,time
someone,一日目,11,2021-01-02 09:00:00.000000
someone,"改行を
含む日記",12,2021-01-04 09:00:00.000000
someone,同じ時刻でも本文が違えば別の日記,13,2021-01-04 09:00:00.000000
someone,同じ時刻でも本文が違えば別の日記,14,2021-01-04 09:00:00.000000
"""
LEGACY_COMMENT_CSV = """diary_id,text,id,time
11,一日目へのコメント,1,2024-07-31 22:14:37.186000
13,二日目へのコメント,2,2024-07-31 22:15:10.586000
"""


def test_import_legacy_csv(shown):
    user_id = f"test-{uuid.uuid4()}"

    diaries = shown(ImportDiaryCsv(user_id, LEGACY_DIARY_CSV))
    comments = shown(ImportCommentCsv(user_id, LEGACY_COMMENT_CSV))

    assert diaries == {"added": 3, "skipped": 1}
    assert comments == {"added": 2, "skipped": 0}
    listed = ListDiaries(user_id).run()
    assert [(diary["text"], diary["time"]) for diary in listed] == [
        ("一日目", "2021-01-02T09:00:00+09:00"), ("改行を\n含む日記", "2021-01-04T09:00:00+09:00"),
        ("同じ時刻でも本文が違えば別の日記", "2021-01-04T09:00:00+09:00")]
    assert [[comment["text"] for comment in diary["comments"]] for diary in listed] == [
        ["一日目へのコメント"], [], ["二日目へのコメント"]]


def test_import_again_skips_existing(book):
    with get_env_session() as s:
        exported = ExportDiaryCsv(book.user_id).execute(s)

    assert ImportDiaryCsv(book.user_id, exported.text).run() == {"added": 0, "skipped": 3}


def test_import_comment_without_diary(book):
    with pytest.raises(ValueError, match="diary_id=\\[999\\]"):
        ImportCommentCsv(book.user_id, "diary_id,text,id,time\n999,宛先の無いコメント,1,2024-07-31 22:14:37.186000\n").run()


def test_export_and_import_into_another_user(shown, book):
    diary_csv = shown(ExportDiaryCsv(book.user_id))
    comment_csv = shown(ExportCommentCsv(book.user_id))
    another_user_id = f"test-{uuid.uuid4()}"

    assert diary_csv["rows"] == 3
    assert diary_csv["text"].splitlines()[:2] == [
        "id,text,time,written_at", f"{book.diary_ids[0]},7 月 1 日の日記,2024-07-01 21:00:00.000000,"]
    assert comment_csv["text"].splitlines() == [
        "id,diary_id,text,time", f"{book.comment_id},{book.diary_ids[1]},7 月 2 日へのコメント,2024-07-02 22:00:00.000000"]
    assert ImportDiaryCsv(another_user_id, diary_csv["text"]).run() == {"added": 3, "skipped": 0}
    assert ImportCommentCsv(another_user_id, comment_csv["text"]).run() == {"added": 1, "skipped": 0}
    copied = ListDiaries(another_user_id).run()
    assert [len(diary["comments"]) for diary in copied] == [0, 1, 0]


def test_future_diary_stays_sealed_through_csv(shown, book):
    deliver_on = (datetime.now(JST) + timedelta(days=30)).date()
    SendFutureDiary(book.user_id, FutureDiaryCreateForm(text="未来の自分へ", deliver_on=deliver_on)).run()
    another_user_id = f"test-{uuid.uuid4()}"

    exported = shown(ExportDiaryCsv(book.user_id))
    assert ImportDiaryCsv(another_user_id, exported["text"]).run() == {"added": 4, "skipped": 0}
    assert [diary["time"][:10] for diary in ListFutureDiaries(another_user_id).run()] == [deliver_on.isoformat()]
    assert len(ListDiaries(another_user_id).run()) == 3
