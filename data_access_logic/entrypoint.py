#!/usr/bin/env python3
"""入口の基底。同じ入口を、呼ぶ側が使い分ける。

- claude が CLI から: `show()`(結果を JSON で print する)
- python から続けて使う: `run()`(`model_dump(mode="json")` した dict を返す)
- GUI の API: 自分のセッションで `execute(s)`(レスポンスのモデルを返す)
"""
from __future__ import annotations

import json
from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import ORMOption

from data_access_logic.logs import configure_logging
from data_access_logic.material import Material
from db.schema import Base, get_env_session


class UnknownRecordError(ValueError):
    pass


def dumped(result: BaseModel | Sequence[BaseModel]) -> dict | list[dict]:
    """一覧を返す入口は、モデルのリストを返す。"""
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    return [item.model_dump(mode="json") for item in result]


def loading(query: Select, record_model: type[Material]) -> Select:
    """`record_model` に詰めるのに要るリレーション(日記のコメント)を読む。
    同じセッションに行が残っていると eager load が効かないので `populate_existing` を付ける。"""
    return query.options(*record_model.LOAD_OPTIONS).execution_options(populate_existing=True)


def reloaded[R: Base](s: Session, row: R, *options: ORMOption) -> R:
    model = type(row)
    return s.scalars(select(model).where(model.id == row.id).options(*options)
                     .execution_options(populate_existing=True)).one()


def record_of[M: Material](s: Session, record_model: type[M], row: Base) -> M:
    if record_model.LOAD_OPTIONS:
        row = reloaded(s, row, *record_model.LOAD_OPTIONS)
    return record_model.model_validate(row)


class Entrypoint:
    def run(self) -> dict | list[dict]:
        return dumped(self.result())

    def show(self) -> None:
        configure_logging()
        print(json.dumps(self.run(), ensure_ascii=False, indent=2))

    def result(self) -> BaseModel | Sequence[BaseModel]:
        raise NotImplementedError


class SessionEntrypoint(Entrypoint):
    def result(self) -> BaseModel | Sequence[BaseModel]:
        with get_env_session() as s:
            return self.execute(s)

    def execute(self, s: Session) -> BaseModel | Sequence[BaseModel]:
        raise NotImplementedError


# `execute()` は `s.begin()` に包むので、その中で `s.commit()` は呼ばない
# (成功時は抜けるときにまとめて commit、例外時は rollback される)
class CommitEntrypoint(SessionEntrypoint):
    def result(self) -> BaseModel | Sequence[BaseModel]:
        with get_env_session() as s, s.begin():
            return self.execute(s)

    @staticmethod
    def finalize(s: Session, record: Base) -> None:
        """db が決める値(id)と、db が読み替えた値(時刻の時差)を、レスポンスのモデルに詰める前に読み直す。"""
        s.flush()
        s.refresh(record)
