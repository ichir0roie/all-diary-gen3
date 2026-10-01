"""日記を書き直す・消す・未来へ送る・読み返す(同じ月日・日ごとの数・似た日記)入口。"""
from datetime import date, datetime, timedelta

import pytest

from data_access_logic.comment.commit_comment import CommitComment
from data_access_logic.comment.form import CommentCreateForm
from data_access_logic.constants import JST
from data_access_logic.diary.count_diaries_by_day import CountDiariesByDay
from data_access_logic.diary.delete_diary import DeleteDiary
from data_access_logic.diary.form import DiaryUpdateForm, FutureDiaryCreateForm
from data_access_logic.diary.list_diaries import ListDiaries
from data_access_logic.diary.list_future_diaries import ListFutureDiaries
from data_access_logic.diary.list_on_this_day import ListOnThisDay, same_day_in
from data_access_logic.diary.read_diary import ReadDiary
from data_access_logic.diary.search_similar_diaries import SearchSimilarDiaries, grams
from data_access_logic.diary.send_future_diary import SendFutureDiary
from data_access_logic.diary.update_diary import UpdateDiary
from data_access_logic.entrypoint import UnknownRecordError
from db.schema import Comment, Diary, get_env_session


def add_diaries(user_id: str, *diaries: tuple[datetime, str], written_at: datetime | None = None) -> list[int]:
    with get_env_session() as s:
        rows = [Diary(user_id=user_id, time=time, text=text, written_at=written_at) for time, text in diaries]
        s.add_all(rows)
        s.commit()
        return [row.id for row in rows]


def test_update_diary(shown, book):
    result = shown(UpdateDiary(book.user_id, book.diary_ids[1], DiaryUpdateForm(text="書き直した日記")))

    assert (result["text"], result["time"]) == ("書き直した日記", "2024-07-02T21:00:00+09:00")
    assert [comment["id"] for comment in result["comments"]] == [book.comment_id]


def test_update_other_users_diary(book):
    with pytest.raises(UnknownRecordError):
        UpdateDiary(book.user_id, book.other_diary_id, DiaryUpdateForm(text="書き直せない")).run()


def test_delete_diary_with_comments(shown, book):
    result = shown(DeleteDiary(book.user_id, book.diary_ids[1]))

    assert result == {"id": book.diary_ids[1], "comments": 1}
    assert [diary["id"] for diary in ListDiaries(book.user_id).run()] == [book.diary_ids[0], book.diary_ids[2]]
    with get_env_session() as s:
        assert s.get(Comment, book.comment_id) is None


def test_delete_other_users_diary(book):
    with pytest.raises(UnknownRecordError):
        DeleteDiary(book.user_id, book.other_diary_id).run()


def test_send_future_diary(shown, book):
    deliver_on = (datetime.now(JST) + timedelta(days=10)).date()

    sent = shown(SendFutureDiary(book.user_id, FutureDiaryCreateForm(text="十日後の自分へ", deliver_on=deliver_on)))

    assert sent["time"] == f"{deliver_on.isoformat()}T00:00:00+09:00"
    assert "text" not in sent
    assert shown(ListFutureDiaries(book.user_id)) == [sent]
    # 届くまでは、読むことも、書き直すことも、コメントを足すこともできない
    assert sent["id"] not in [diary["id"] for diary in ListDiaries(book.user_id).run()]
    for entrypoint in (ReadDiary(book.user_id, sent["id"]), DeleteDiary(book.user_id, sent["id"]),
                       UpdateDiary(book.user_id, sent["id"], DiaryUpdateForm(text="のぞく")),
                       CommitComment(book.user_id, CommentCreateForm(diary_id=sent["id"], text="のぞく"))):
        with pytest.raises(UnknownRecordError):
            entrypoint.run()


def test_send_future_diary_to_today(book):
    with pytest.raises(ValueError, match="明日より後"):
        SendFutureDiary(book.user_id, FutureDiaryCreateForm(text="今日には送れない", deliver_on=datetime.now(JST).date())).run()


def test_delivered_future_diary(book):
    written_at = datetime(2024, 6, 1, 8, 0, tzinfo=JST)
    [diary_id] = add_diaries(book.user_id, (datetime(2024, 7, 2, 0, 0, tzinfo=JST), "届いた日記"), written_at=written_at)

    listed = ListDiaries(book.user_id, start_date=date(2024, 7, 2), end_date=date(2024, 7, 2)).run()

    assert [(diary["id"], diary["written_at"]) for diary in listed] == [
        (diary_id, "2024-06-01T08:00:00+09:00"), (book.diary_ids[1], None)]
    assert ListFutureDiaries(book.user_id).run() == []


def test_same_day_in_leap_year():
    assert same_day_in(2023, date(2024, 2, 29)) == date(2023, 2, 28)
    assert same_day_in(2020, date(2024, 2, 29)) == date(2020, 2, 29)


def test_list_on_this_day(shown, book):
    add_diaries(book.user_id, (datetime(2022, 7, 2, 7, 0, tzinfo=JST), "二年前の同じ日"),
                (datetime(2022, 7, 4, 7, 0, tzinfo=JST), "二年前の二日後"))

    result = shown(ListOnThisDay(book.user_id, date(2025, 7, 2)))
    around = ListOnThisDay(book.user_id, date(2025, 7, 2), around_days=1).run()

    assert [(year["year"], [diary["text"] for diary in year["diaries"]]) for year in result] == [
        (2025, []), (2024, ["7 月 2 日の日記"]), (2023, []), (2022, ["二年前の同じ日"])]
    assert (result[1]["start_date"], result[1]["end_date"]) == ("2024-07-02", "2024-07-02")
    assert [len(year["diaries"]) for year in around] == [0, 3, 0, 1]


def test_list_on_this_day_without_diaries(book):
    assert ListOnThisDay(f"{book.user_id}-none", date(2025, 7, 2)).run() == []


def test_count_diaries_by_day(shown, book):
    # 日本時間の 7 月 1 日 23 時 30 分は、UTC ではまだ 14 時 30 分。日本時間の暦の日で数える
    add_diaries(book.user_id, (datetime(2024, 7, 1, 23, 30, tzinfo=JST), "夜更け"))

    result = shown(CountDiariesByDay(book.user_id))

    assert result == [{"day": "2024-07-01", "diaries": 2, "chars": len("7 月 1 日の日記") + len("夜更け")},
                      {"day": "2024-07-02", "diaries": 1, "chars": len("7 月 2 日の日記")},
                      {"day": "2024-07-03", "diaries": 1, "chars": len("7 月 3 日の日記")}]
    assert [day["day"] for day in CountDiariesByDay(book.user_id, start_date=date(2024, 7, 2)).run()] == [
        "2024-07-02", "2024-07-03"]


def test_grams():
    assert grams("した。駅前の本屋") == ["駅前", "前の", "の本", "本屋"]
    assert grams("ABC") == ["ab", "bc"]
    assert grams("ですね、そうです") == []


def test_search_similar_diaries(shown, book):
    near, close, _ = add_diaries(
        book.user_id, (datetime(2023, 5, 1, 21, 0, tzinfo=JST), "駅前の本屋で文庫本を二冊買った。"),
        (datetime(2023, 5, 2, 21, 0, tzinfo=JST), "仕事帰りに駅前の本屋に寄った。"),
        (datetime(2023, 5, 3, 21, 0, tzinfo=JST), "カレーを作りすぎた。"))

    result = shown(SearchSimilarDiaries(book.user_id, "今日も駅前の本屋で文庫本を探した"))

    assert result["total"] == 2
    assert [diary["diary"]["id"] for diary in result["diaries"]] == [near, close]
    assert 0 < result["diaries"][1]["score"] < result["diaries"][0]["score"] <= 1
    assert SearchSimilarDiaries(book.user_id, "ですね").run() == {"total": 0, "diaries": []}
    assert SearchSimilarDiaries(book.other_user_id, "駅前の本屋").run() == {"total": 0, "diaries": []}

