"""手元の PostgreSQL(`infra_local/postgres.sh`)の db の URL と、作り直し・版の上げ。テスト(`tool.test`)とモックの db(`tool.dev`)が使う。"""
import logging
import os
import subprocess
import sys

from sqlalchemy.engine import make_url

logger = logging.getLogger(__name__)

PRODUCTION_DATABASE_URL = os.environ.get("DIARY_DATABASE_URL") or None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _dev_database_url() -> str:
    """開発用の PostgreSQL の URL。渡されていなければ、要ったこの時に `infra_local/postgres.sh` で用意する。"""
    dev = os.environ.get("DIARY_DEV_DATABASE_URL")
    if dev:
        return dev
    logger.info("開発用の PostgreSQL を用意する(infra_local/postgres.sh)")
    result = subprocess.run(["bash", os.path.join("infra_local", "postgres.sh"), sys.executable], cwd=ROOT,
                            stdout=subprocess.PIPE, text=True, encoding="utf-8", check=True)
    dev = result.stdout.strip().splitlines()[-1]
    os.environ["DIARY_DEV_DATABASE_URL"] = dev
    return dev


def local_database_url(database: str) -> str:
    """開発用の PostgreSQL のサーバーにある db `database` の URL。手元のサーバーを指していなければ止まる。"""
    url = make_url(_dev_database_url()).set(database=database)
    # 取り違えて本番(転送越しの RDS も 127.0.0.1)に書かないよう、開発用の db と同じサーバーの db だけを許す
    if url.host not in ("127.0.0.1", "localhost") or PRODUCTION_DATABASE_URL and \
            (make_url(PRODUCTION_DATABASE_URL).host, make_url(PRODUCTION_DATABASE_URL).port) == (url.host, url.port):
        raise RuntimeError(f"db が手元の PostgreSQL を指していない: {url.render_as_string(hide_password=True)}")
    return url.render_as_string(hide_password=False)


def pin_database_url(url: str, package: str) -> None:
    """`db.schema` が読み込む前に、`DIARY_DATABASE_URL` を `url` に差し替える。`package` は止まったときの案内に使う。"""
    if "db.schema" in sys.modules and sys.modules["db.schema"].DATABASE_URL != url:
        raise RuntimeError(f"db.schema が {make_url(url).database} 以外で先に読み込まれている。{package} 配下は "
                           f"{make_url(url).database} しか使わないので、こちらを先に import する")
    os.environ["DIARY_DATABASE_URL"] = url
    os.environ.pop("DIARY_DATABASE_IAM_AUTH", None)


def recreate_local_db(url: str) -> None:
    """手元の db `url`(`local_database_url` で作り、`pin_database_url` で固定したもの)を消し、`schema.py` から空の db を作り直す。"""
    from sqlalchemy import text

    from db.postgres import init_db
    from db.schema import engine, make_url_engine

    engine.dispose()
    target = make_url(url)
    admin = make_url_engine(target.set(database="postgres").render_as_string(hide_password=False))
    with admin.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{target.database}" WITH (FORCE)'))
    admin.dispose()
    init_db.main(["--url", url, "--create-database"])


def upgrade_local_db() -> None:
    """`pin_database_url` で固定した db を、コードの版(alembic の head)まで上げる。前に作った db には、そのあと足したマイグレーションが当たっていない。"""
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(os.path.join(ROOT, "db", "alembic", "alembic.ini")), "head")
