"""claude が CLI から `show()` で呼ぶ、タグ(`data_access_logic/tag/`)と、日記・コメントにタグを付ける入口。"""
import pytest
from pydantic import ValidationError

from data_access_logic.comment.read_comment import ReadComment
from data_access_logic.comment.set_comment_tag import SetCommentTag
from data_access_logic.diary.list_diaries import ListDiaries
from data_access_logic.diary.list_tagged_diaries import ListTaggedDiaries
from data_access_logic.diary.read_diary import ReadDiary
from data_access_logic.diary.set_diary_tag import SetDiaryTag
from data_access_logic.entrypoint import UnknownRecordError
from data_access_logic.tag.commit_tag import CommitTag
from data_access_logic.tag.delete_tag import DeleteTag
from data_access_logic.tag.form import TagChoiceForm, TagCreateForm, TagUpdateForm
from data_access_logic.tag.list_tags import ListTags
from data_access_logic.tag.update_tag import UpdateTag


def test_commit_tag(shown, book):
    result = shown(CommitTag(book.user_id, TagCreateForm(name="  旅行 ")))

    assert result["name"] == "旅行"
    assert shown(ListTags(book.user_id)) == [{"tag": result, "diaries": 0, "comments": 0}]


def test_commit_taken_tag_name(shown, book):
    shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))

    with pytest.raises(ValueError, match="既にある"):
        shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))


def test_same_tag_name_for_other_user(shown, book):
    shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    shown(CommitTag(book.other_user_id, TagCreateForm(name="旅行")))

    assert [usage["tag"]["name"] for usage in shown(ListTags(book.user_id))] == ["旅行"]


def test_blank_tag_name():
    with pytest.raises(ValidationError):
        TagCreateForm(name="  ")


def test_list_tags(shown, book):
    trip = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    shown(CommitTag(book.user_id, TagCreateForm(name="仕事")))
    shown(SetDiaryTag(book.user_id, book.diary_ids[0], TagChoiceForm(tag_id=trip["id"])))
    shown(SetDiaryTag(book.user_id, book.diary_ids[1], TagChoiceForm(tag_id=trip["id"])))
    shown(SetCommentTag(book.user_id, book.comment_id, TagChoiceForm(tag_id=trip["id"])))

    result = shown(ListTags(book.user_id))

    assert [(usage["tag"]["name"], usage["diaries"], usage["comments"]) for usage in result] == [
        ("仕事", 0, 0), ("旅行", 2, 1)]


def test_set_diary_tag(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))

    tagged = shown(SetDiaryTag(book.user_id, book.diary_ids[1], TagChoiceForm(tag_id=tag["id"])))
    untagged = shown(SetDiaryTag(book.user_id, book.diary_ids[1], TagChoiceForm(tag_id=None)))

    assert (tagged["tag"], tagged["text"]) == (tag, "7 月 2 日の日記")
    assert untagged["tag"] is None
    assert shown(ReadDiary(book.user_id, book.diary_ids[1]))["tag"] is None


def test_set_comment_tag(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))

    result = shown(SetCommentTag(book.user_id, book.comment_id, TagChoiceForm(tag_id=tag["id"])))

    assert (result["tag"], result["text"]) == (tag, "7 月 2 日へのコメント")
    assert shown(ReadComment(book.user_id, book.comment_id))["tag"] == tag
    diary = shown(ReadDiary(book.user_id, book.diary_ids[1]))
    assert (diary["tag"], diary["comments"][0]["tag"]) == (None, tag)


def test_set_other_users_tag(shown, book):
    other_tag = shown(CommitTag(book.other_user_id, TagCreateForm(name="別の人のタグ")))

    with pytest.raises(UnknownRecordError):
        shown(SetDiaryTag(book.user_id, book.diary_ids[0], TagChoiceForm(tag_id=other_tag["id"])))
    with pytest.raises(UnknownRecordError):
        shown(SetCommentTag(book.user_id, book.comment_id, TagChoiceForm(tag_id=other_tag["id"])))


def test_set_tag_to_other_users_diary(shown, book):
    tag = shown(CommitTag(book.other_user_id, TagCreateForm(name="旅行")))

    with pytest.raises(UnknownRecordError):
        shown(SetDiaryTag(book.other_user_id, book.diary_ids[0], TagChoiceForm(tag_id=tag["id"])))


def test_update_tag(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    shown(SetDiaryTag(book.user_id, book.diary_ids[0], TagChoiceForm(tag_id=tag["id"])))

    result = shown(UpdateTag(book.user_id, tag["id"], TagUpdateForm(name="旅")))

    assert result == {"id": tag["id"], "name": "旅"}
    assert shown(ReadDiary(book.user_id, book.diary_ids[0]))["tag"] == result


def test_update_tag_to_taken_name(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    shown(CommitTag(book.user_id, TagCreateForm(name="仕事")))

    shown(UpdateTag(book.user_id, tag["id"], TagUpdateForm(name="旅行")))  # 自分と同じ名前のままは通す
    with pytest.raises(ValueError, match="既にある"):
        shown(UpdateTag(book.user_id, tag["id"], TagUpdateForm(name="仕事")))


def test_update_other_users_tag(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))

    with pytest.raises(UnknownRecordError):
        shown(UpdateTag(book.other_user_id, tag["id"], TagUpdateForm(name="書き換えられない")))


def test_delete_tag(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    shown(SetDiaryTag(book.user_id, book.diary_ids[0], TagChoiceForm(tag_id=tag["id"])))
    shown(SetDiaryTag(book.user_id, book.diary_ids[1], TagChoiceForm(tag_id=tag["id"])))
    shown(SetCommentTag(book.user_id, book.comment_id, TagChoiceForm(tag_id=tag["id"])))

    result = shown(DeleteTag(book.user_id, tag["id"]))

    assert result == {"id": tag["id"], "diaries": 2, "comments": 1}
    assert shown(ListTags(book.user_id)) == []
    diaries = shown(ListDiaries(book.user_id))
    assert [diary["id"] for diary in diaries] == book.diary_ids
    assert [diary["tag"] for diary in diaries] == [None, None, None]
    assert shown(ReadComment(book.user_id, book.comment_id))["tag"] is None


def test_delete_other_users_tag(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))

    with pytest.raises(UnknownRecordError):
        shown(DeleteTag(book.other_user_id, tag["id"]))


def test_list_tagged_diaries(shown, book):
    trip = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    work = shown(CommitTag(book.user_id, TagCreateForm(name="仕事")))
    food = shown(CommitTag(book.user_id, TagCreateForm(name="食事")))
    shown(SetDiaryTag(book.user_id, book.diary_ids[0], TagChoiceForm(tag_id=trip["id"])))
    shown(SetCommentTag(book.user_id, book.comment_id, TagChoiceForm(tag_id=trip["id"])))
    shown(SetDiaryTag(book.user_id, book.diary_ids[2], TagChoiceForm(tag_id=work["id"])))

    trip_diaries = shown(ListTaggedDiaries(book.user_id, [trip["id"]]))
    either = shown(ListTaggedDiaries(book.user_id, [trip["id"], work["id"]]))

    # コメントにだけタグが付いた日記も拾い、新しい順に並べる
    assert [diary["id"] for diary in trip_diaries] == [book.diary_ids[1], book.diary_ids[0]]
    assert trip_diaries[0]["comments"][0]["tag"] == trip
    # どれかのタグが付いていれば拾う(OR)
    assert [diary["id"] for diary in either] == book.diary_ids[::-1]
    assert shown(ListTaggedDiaries(book.user_id, [food["id"]])) == []


def test_list_other_users_tagged_diaries(shown, book):
    tag = shown(CommitTag(book.user_id, TagCreateForm(name="旅行")))
    other_tag = shown(CommitTag(book.other_user_id, TagCreateForm(name="旅行")))

    with pytest.raises(UnknownRecordError):
        shown(ListTaggedDiaries(book.user_id, [tag["id"], other_tag["id"]]))
