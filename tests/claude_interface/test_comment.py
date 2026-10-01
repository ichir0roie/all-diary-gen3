"""claude が CLI から `show()` で呼ぶ、コメント(`data_access_logic/comment/`)の入口。"""
import pytest

from data_access_logic.comment.commit_comment import CommitComment
from data_access_logic.comment.form import CommentCreateForm
from data_access_logic.comment.list_comments import ListComments
from data_access_logic.comment.read_comment import ReadComment
from data_access_logic.entrypoint import UnknownRecordError


def test_list_comments(shown, book):
    result = shown(ListComments(book.user_id, book.diary_ids[1]))

    assert [comment["id"] for comment in result] == [book.comment_id]


def test_read_comment(shown, book):
    result = shown(ReadComment(book.user_id, book.comment_id))

    assert result == {"id": book.comment_id, "diary_id": book.diary_ids[1], "time": "2024-07-02T22:00:00+09:00",
                      "text": "7 月 2 日へのコメント"}


def test_commit_comment(shown, book):
    result = shown(CommitComment(book.user_id, CommentCreateForm(
        diary_id=book.diary_ids[0], text="あとから書き足す", time="2024-07-05T12:00:00+09:00")))

    assert (result["diary_id"], result["text"], result["time"]) == (
        book.diary_ids[0], "あとから書き足す", "2024-07-05T12:00:00+09:00")


def test_commit_comment_to_other_users_diary(book):
    with pytest.raises(UnknownRecordError):
        CommitComment(book.user_id, CommentCreateForm(diary_id=book.other_diary_id, text="書けない")).run()
