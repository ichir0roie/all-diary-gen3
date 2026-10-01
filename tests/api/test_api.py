"""API(`gui/api/app.py`)。エンドポイントごとに、なるべく多くの値を渡す一件を通す。"""
from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from data_access_logic.constants import JST
from gui.api.app import app
from tests.legacy_files import LEGACY, OLD_ME, OLD_OTHER


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def as_user(user_id: str) -> dict[str, str]:
    """画面の route handler が、確かめた Cognito のユーザーの sub を入れて流す見出し。"""
    return {"x-diary-user": user_id}


def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"dialect": "postgresql"}


def test_user_required(client):
    response = client.get("/api/diaries")

    assert response.status_code == 401


def test_list_diaries(client, book):
    response = client.get("/api/diaries", params={"start_date": "2024-07-01", "end_date": "2024-07-02"},
                          headers=as_user(book.user_id))

    assert response.status_code == 200
    assert [diary["id"] for diary in response.json()] == book.diary_ids[:2]


def test_read_diary(client, book):
    response = client.get(f"/api/diaries/{book.diary_ids[1]}", headers=as_user(book.user_id))

    assert response.status_code == 200
    assert [comment["id"] for comment in response.json()["comments"]] == [book.comment_id]


def test_read_other_users_diary(client, book):
    response = client.get(f"/api/diaries/{book.other_diary_id}", headers=as_user(book.user_id))

    assert response.status_code == 404


def test_commit_diary(client, book):
    response = client.post("/api/diaries", json={"text": "API から書く", "time": "2024-07-06T07:00:00+09:00"},
                           headers=as_user(book.user_id))

    assert response.status_code == 201
    assert (response.json()["text"], response.json()["time"]) == ("API から書く", "2024-07-06T07:00:00+09:00")


def test_commit_diary_unknown_field(client, book):
    response = client.post("/api/diaries", json={"text": "欄が多い", "user_id": book.other_user_id},
                           headers=as_user(book.user_id))

    assert response.status_code == 422


def test_comments(client, book):
    created = client.post("/api/comments", json={"diary_id": book.diary_ids[2], "text": "API からのコメント"},
                          headers=as_user(book.user_id))
    listed = client.get(f"/api/diaries/{book.diary_ids[2]}/comments", headers=as_user(book.user_id))
    read = client.get(f"/api/comments/{created.json()['id']}", headers=as_user(book.user_id))

    assert created.status_code == 201
    assert [comment["text"] for comment in listed.json()] == ["API からのコメント"]
    assert read.json() == created.json()


def test_comment_to_other_users_diary(client, book):
    response = client.post("/api/comments", json={"diary_id": book.other_diary_id, "text": "書けない"},
                           headers=as_user(book.user_id))

    assert response.status_code == 404


def test_update_and_delete_diary(client, book):
    updated = client.patch(f"/api/diaries/{book.diary_ids[1]}", json={"text": "書き直した"}, headers=as_user(book.user_id))
    deleted = client.delete(f"/api/diaries/{book.diary_ids[1]}", headers=as_user(book.user_id))
    read = client.get(f"/api/diaries/{book.diary_ids[1]}", headers=as_user(book.user_id))

    assert (updated.status_code, updated.json()["text"]) == (200, "書き直した")
    assert deleted.json() == {"id": book.diary_ids[1], "comments": 1}
    assert read.status_code == 404


def test_delete_other_users_diary(client, book):
    response = client.delete(f"/api/diaries/{book.other_diary_id}", headers=as_user(book.user_id))

    assert response.status_code == 404


def test_update_and_delete_comment(client, book):
    updated = client.patch(f"/api/comments/{book.comment_id}", json={"text": "書き直した"}, headers=as_user(book.user_id))
    deleted = client.delete(f"/api/comments/{book.comment_id}", headers=as_user(book.user_id))

    assert (updated.status_code, updated.json()["text"]) == (200, "書き直した")
    assert deleted.json() == {"id": book.comment_id, "diary_id": book.diary_ids[1]}
    assert client.get(f"/api/comments/{book.comment_id}", headers=as_user(book.user_id)).status_code == 404


def test_future_diaries(client, book):
    deliver_on = (datetime.now(JST) + timedelta(days=3)).date().isoformat()

    sent = client.post("/api/future-diaries", json={"text": "三日後へ", "deliver_on": deliver_on}, headers=as_user(book.user_id))
    listed = client.get("/api/future-diaries", headers=as_user(book.user_id))
    read = client.get(f"/api/diaries/{sent.json()['id']}", headers=as_user(book.user_id))

    assert sent.status_code == 201
    assert listed.json() == [sent.json()]
    assert read.status_code == 404


def test_future_diary_to_past(client, book):
    response = client.post("/api/future-diaries", json={"text": "過去へは送れない", "deliver_on": "2020-01-01"},
                           headers=as_user(book.user_id))

    assert response.status_code == 400


def test_on_this_day(client, book):
    response = client.get("/api/on-this-day", params={"day": "2025-07-02", "around_days": 1}, headers=as_user(book.user_id))

    assert response.status_code == 200
    assert [(year["year"], len(year["diaries"])) for year in response.json()] == [(2025, 0), (2024, 3)]


def test_on_this_day_too_wide(client, book):
    response = client.get("/api/on-this-day", params={"day": "2025-07-02", "around_days": 100}, headers=as_user(book.user_id))

    assert response.status_code == 400


def test_diary_counts(client, book):
    response = client.get("/api/diary-counts", params={"end_date": "2024-07-02"}, headers=as_user(book.user_id))

    assert [(day["day"], day["diaries"]) for day in response.json()] == [("2024-07-01", 1), ("2024-07-02", 1)]


def test_similar_diaries(client, book):
    created = client.post("/api/diaries", json={"text": "駅前の本屋に寄った"}, headers=as_user(book.user_id))
    response = client.post("/api/diaries/similar", json={"text": "駅前の本屋"}, headers=as_user(book.user_id))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["diaries"][0]["diary"]["id"] == created.json()["id"]


def test_similar_to_diary(client, book):
    source = client.post("/api/diaries", json={"text": "駅前の本屋で文庫本を買った"}, headers=as_user(book.user_id))
    near = client.post("/api/diaries", json={"text": "駅前の本屋に寄った"}, headers=as_user(book.user_id))

    response = client.get(f"/api/diaries/{source.json()['id']}/similar", headers=as_user(book.user_id))
    other = client.get(f"/api/diaries/{book.other_diary_id}/similar", headers=as_user(book.user_id))

    assert [diary["diary"]["id"] for diary in response.json()["diaries"]] == [near.json()["id"]]
    assert other.status_code == 404


def test_csv(client, book):
    exported = client.get("/api/csv/diary", headers=as_user(book.user_id))
    imported = client.post("/api/csv/diary", json={"text": exported.text}, headers=as_user(book.other_user_id))

    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert exported.headers["content-disposition"] == 'attachment; filename="diary.csv"'
    # 別の人にも 7 月 2 日 21 時の日記があるが、本文が違うので足す
    assert imported.json() == {"added": 3, "skipped": 0}


def test_csv_unknown_kind(client, book):
    response = client.get("/api/csv/episode", headers=as_user(book.user_id))

    assert response.status_code == 422


def test_legacy_db(client, book):
    file_headers = {**as_user(book.user_id), "content-type": "application/octet-stream"}
    summary = client.post("/api/legacy-db/summary", content=LEGACY, headers=file_headers)
    imported = client.post("/api/legacy-db/import", params={"source_user_id": OLD_ME}, content=LEGACY, headers=file_headers)

    assert summary.status_code == 200
    assert [user["user_id"] for user in summary.json()["users"]] == [OLD_ME, OLD_OTHER]
    assert imported.json() == {"diaries": {"added": 3, "skipped": 0}, "comments": {"added": 3, "skipped": 0}}


def test_legacy_db_not_sqlite(client, book):
    response = client.post("/api/legacy-db/summary", content=b"not a db",
                           headers={**as_user(book.user_id), "content-type": "application/octet-stream"})

    assert response.status_code == 400
