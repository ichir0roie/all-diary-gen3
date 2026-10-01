#!/usr/bin/env python3
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):

    # sort_order は列の並び順を明示するための番号。同じクラス内では 10 刻みで振る(あとで列を挟みやすい)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, sort_order=0)


class Post(Base):
    """日記とコメント。どちらも、ある人がある時刻に書いた文章を一件ずつ持つ。

    同じ時刻の行を一件に限らない。以前の db には、同じ時刻で中身の違う日記・コメントが入っている(続けて書いた分を取り込んだもの)。
    取り込みは、時刻と本文がどちらも同じ行を同じものとみなす(`data_access_logic/query/import_query.py`)。
    """

    __abstract__ = True

    user_id: Mapped[str] = mapped_column(String, nullable=False, comment="書いた人。Cognito のユーザーの sub", sort_order=10)
    # 時差を持つ時刻(timestamptz)で持つ。時差の無い時刻を受けたら日本時間として読む(`data_access_logic/material.py` の `JstTime`)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="書いた時刻", sort_order=20)
    migration_id: Mapped[int | None] = mapped_column(
        BigInteger, comment="CSV から取り込んだ行の、取り込む前の id。コメントの CSV の diary_id はこれで日記を引く", sort_order=900)
    text: Mapped[str] = mapped_column(String, nullable=False, sort_order=1000)


class Diary(Post):

    __tablename__ = "diary"

    # リレーションは読むときに `selectinload` などで明示して読む。読まずに触ったら、黙って空にせず止める
    comments: Mapped[list[Comment]] = relationship(
        back_populates="diary", lazy="raise", viewonly=True, order_by="(Comment.time, Comment.id)")

    __table_args__ = (Index("ix_diary_user_id_time", "user_id", "time"),)


class Comment(Post):

    __tablename__ = "comment"

    diary_id: Mapped[int] = mapped_column(Integer, ForeignKey("diary.id"), nullable=False, sort_order=30)

    diary: Mapped[Diary] = relationship(back_populates="comments", lazy="raise")

    __table_args__ = (Index("ix_comment_diary_id", "diary_id"),)


# 読み書きする db の SQLAlchemy の URL。手元は踏み台越しの RDS(`tool.aws.rds --serve`)、Lambda は VPC の中の RDS、
# テストは手元の PostgreSQL(`tool.test`)を指す。無くても import はできる(繋いだ時点で止まる)
DATABASE_URL = os.environ.get("DIARY_DATABASE_URL") or None
# RDS の IAM データベース認証で繋ぐか(パスワードの代わりに、接続のたびにトークンを作る)
DATABASE_IAM_AUTH = os.environ.get("DIARY_DATABASE_IAM_AUTH") == "1"
# 手元の転送(127.0.0.1)越しに IAM 認証で繋ぐとき、トークンは RDS の本来のエンドポイントに宛てて作る。その在りかの SSM パラメータ
_RDS_ENDPOINT_PARAMETERS = ("/diary/db/endpoint", "/diary/db/port")
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DIARY_DATABASE_URL が無い。手元は `tool.aws.rds --serve` の転送と、"
                           "SessionStart フックか .vscode が渡す DIARY_DATABASE_URL で RDS に繋ぐ(.claude/docs/setup.md)")
    return DATABASE_URL


def make_url_engine(url: str, iam_auth: bool = False):
    if make_url(url).get_backend_name() == "sqlite":
        return create_engine(url)
    # Lambda は凍結をはさんで接続を使い回し、手元の転送は 1 時間で張り直すので、切れた接続を使う前に確かめる
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=300)
    if iam_auth:
        _use_iam_auth_token(engine)
    return engine


def _use_iam_auth_token(engine) -> None:
    # RDS の IAM データベース認証のトークンは 15 分で切れるので、接続を張るたびに作る。
    # 署名は手元で作るので、NAT の無い VPC の中の Lambda からでも外へ出ずに済む
    import boto3
    from sqlalchemy import event

    rds = boto3.client("rds")
    signed_for: dict[tuple[str, int], tuple[str, int]] = {}

    def rds_endpoint(host: str, port: int) -> tuple[str, int]:
        if host not in _LOOPBACK_HOSTS:
            return host, port
        if (host, port) not in signed_for:
            values = boto3.client("ssm").get_parameters(Names=list(_RDS_ENDPOINT_PARAMETERS))["Parameters"]
            found = {value["Name"]: value["Value"] for value in values}
            endpoint, rds_port = (found[name] for name in _RDS_ENDPOINT_PARAMETERS)
            signed_for[(host, port)] = (endpoint, int(rds_port))
        return signed_for[(host, port)]

    @event.listens_for(engine, "do_connect")
    def _set_token(dialect, conn_rec, cargs, cparams):
        host, port = rds_endpoint(cparams["host"], int(cparams.get("port", 5432)))
        cparams["password"] = rds.generate_db_auth_token(
            DBHostname=host, Port=port, DBUsername=cparams["user"], Region=rds.meta.region_name)


def _no_database(*args, **kwargs):
    database_url()


# URL が無ければ、繋いだ時点で database_url() の理由で止まる engine にする
engine = (make_url_engine(DATABASE_URL, iam_auth=DATABASE_IAM_AUTH) if DATABASE_URL
          else create_engine("postgresql+psycopg://", creator=_no_database))


def get_env_session():
    return Session(engine)
