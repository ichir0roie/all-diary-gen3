"""テストは手元の PostgreSQL のテスト用の db(`diary_test`)だけを読み書きする。`tool.test` を最初に import して db を固定する。"""
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest

from tool.test import ensure_test_db  # schema より先に読む(db をテスト用の db に固定)
from data_access_logic.constants import JST  # noqa: E402
from data_access_logic.entrypoint import Entrypoint  # noqa: E402
from db.schema import Comment, Diary, engine, get_env_session  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def prepared_test_db() -> None:
    ensure_test_db()
    engine.dispose()  # 作る前の db を掴んでいる接続を捨てる


@pytest.fixture
def shown(capsys: pytest.CaptureFixture[str]) -> Callable[[Entrypoint], Any]:
    """claude が CLI から呼ぶのと同じく `show()` を呼び、標準出力の JSON を読んで返す。"""
    def show(entrypoint: Entrypoint) -> Any:
        capsys.readouterr()
        entrypoint.show()
        return json.loads(capsys.readouterr().out)
    return show


@dataclass
class Book:
    user_id: str
    other_user_id: str
    diary_ids: list[int]
    comment_id: int
    other_diary_id: int


@pytest.fixture
def book() -> Book:
    """テストごとに、自分だけの人(user_id)の日記三件とコメント一件、別の人の日記一件を足す。
    前のテストの行が残っていても、返した user_id と id で自分の行を指せる。"""
    user_id = f"test-{uuid.uuid4()}"
    other_user_id = f"test-{uuid.uuid4()}"
    with get_env_session() as s:
        diaries = [Diary(user_id=user_id, migration_id=100 + day, time=datetime(2024, 7, day, 21, 0, tzinfo=JST),
                         text=f"7 月 {day} 日の日記")
                   for day in (1, 2, 3)]
        other = Diary(user_id=other_user_id, time=datetime(2024, 7, 2, 21, 0, tzinfo=JST), text="別の人の日記")
        s.add_all([*diaries, other])
        s.flush()
        comment = Comment(user_id=user_id, diary_id=diaries[1].id, migration_id=200,
                          time=datetime(2024, 7, 2, 22, 0, tzinfo=JST), text="7 月 2 日へのコメント")
        s.add(comment)
        s.commit()
        return Book(user_id=user_id, other_user_id=other_user_id, diary_ids=[diary.id for diary in diaries],
                    comment_id=comment.id, other_diary_id=other.id)
