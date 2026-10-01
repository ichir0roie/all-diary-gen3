"""テスト用の道具。この下のモジュールは必ず、手元の PostgreSQL のテスト用の db(`diary_test`)を読み書きする。

`db.schema` は import 時に `DIARY_DATABASE_URL` で engine を固定するので、この package の読み込み(= 配下のモジュールより先に走る)で
環境変数を差し替える。日記は人の書いたものなので、本番の行はテスト用の db に写さず、空の db にテストが自分の行を足す。
"""
import logging
import os

from sqlalchemy.engine import make_url

from tool.local_db import ROOT, local_database_url, pin_database_url

TEST_DATABASE_NAME = "diary_test"
TEST_DATABASE_URL = local_database_url(TEST_DATABASE_NAME)
pin_database_url(TEST_DATABASE_URL, "tool.test")

logger = logging.getLogger(__name__)


def ensure_test_db() -> None:
    """テスト用の db が無ければ `schema.py` から作る。あればそのまま使う(作り直すのは `tool.test.recreate_db`)。"""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import text

    from db.postgres import init_db
    from db.schema import engine

    if not _test_db_exists():
        init_db.main(["--url", TEST_DATABASE_URL, "--create-database"])
        return
    with engine.connect() as conn:
        current = conn.scalar(text("SELECT version_num FROM alembic_version"))
    head = ScriptDirectory.from_config(Config(os.path.join(ROOT, "db", "alembic", "alembic.ini"))).get_current_head()
    if current != head:
        logger.warning(f"テスト用の db の版({current})がコードの版({head})と違う。"
                       "`.venv/bin/python -m tool.test.recreate_db` で作り直す")


def _test_db_exists() -> bool:
    from sqlalchemy import text

    from db.schema import make_url_engine

    admin = make_url_engine(make_url(TEST_DATABASE_URL).set(database="postgres").render_as_string(hide_password=False))
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DATABASE_NAME})
    admin.dispose()
    return bool(exists)


def recreate_test_db() -> None:
    """テスト用の db を消し、`schema.py` から空の db を作り直す。"""
    from sqlalchemy import text

    from db.postgres import init_db
    from db.schema import engine, make_url_engine

    engine.dispose()
    admin = make_url_engine(make_url(TEST_DATABASE_URL).set(database="postgres").render_as_string(hide_password=False))
    with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}" WITH (FORCE)'))
    admin.dispose()
    init_db.main(["--url", TEST_DATABASE_URL, "--create-database"])
