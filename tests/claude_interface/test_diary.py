"""claude が CLI から `show()` で呼ぶ、日記(`data_access_logic/diary/`)の入口。"""
from datetime import date

import pytest

from data_access_logic.diary.commit_diary import CommitDiary
from data_access_logic.diary.form import DiaryCreateForm
from data_access_logic.diary.list_diaries import ListDiaries
from data_access_logic.diary.read_diary import ReadDiary
from data_access_logic.entrypoint import UnknownRecordError


def test_list_diaries(shown, book):
    result = shown(ListDiaries(book.user_id, start_date=date(2024, 7, 2), end_date=date(2024, 7, 3)))

    assert [diary["id"] for diary in result] == book.diary_ids[1:]
    assert result[0]["time"] == "2024-07-02T21:00:00+09:00"
    assert [comment["text"] for comment in result[0]["comments"]] == ["7 月 2 日へのコメント"]
    assert result[1]["comments"] == []


def test_list_diaries_without_span(shown, book):
    result = shown(ListDiaries(book.user_id))

    assert [diary["id"] for diary in result] == book.diary_ids


def test_read_diary(shown, book):
    result = shown(ReadDiary(book.user_id, book.diary_ids[1]))

    assert (result["id"], result["text"]) == (book.diary_ids[1], "7 月 2 日の日記")
    assert [comment["id"] for comment in result["comments"]] == [book.comment_id]


def test_read_other_users_diary(book):
    with pytest.raises(UnknownRecordError):
        ReadDiary(book.user_id, book.other_diary_id).run()


def test_commit_diary(shown, book):
    result = shown(CommitDiary(book.user_id, DiaryCreateForm(text="時差の無い時刻は日本時間", time="2024-07-04 08:30:00")))

    assert (result["text"], result["time"], result["comments"]) == ("時差の無い時刻は日本時間", "2024-07-04T08:30:00+09:00", [])
    assert result["id"] in [diary["id"] for diary in ListDiaries(book.user_id, start_date=date(2024, 7, 4)).run()]


def test_commit_diary_now(shown, book):
    result = shown(CommitDiary(book.user_id, DiaryCreateForm(text="今の時刻で書く")))

    assert result["time"].endswith("+09:00")
