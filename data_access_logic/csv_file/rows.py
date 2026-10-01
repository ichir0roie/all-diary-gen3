#!/usr/bin/env python3
"""日記・コメントの CSV の行。以前の db から書き出した CSV(日記は `user_id,text,id,time`、コメントは `diary_id,text,id,time`)を
そのまま読み、書き出しも同じ列と時刻の書式にする。"""
from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from data_access_logic.constants import CSV_TIME_FORMAT, JST
from data_access_logic.material import JstTime


class CsvRow(BaseModel):
    # 以前の CSV にある user_id の列は読まない(取り込む人の行にする)
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: int | None = None
    text: str
    time: JstTime

    @field_validator("id", mode="before")
    @classmethod
    def _blank_id(cls, value: object) -> object:
        return None if value == "" else value


class DiaryCsvRow(CsvRow):
    # 未来へ送った日記の、書いた時刻(`time` は届く時刻)。以前の CSV には無い列で、ふだんの日記は空
    written_at: JstTime | None = None

    @field_validator("written_at", mode="before")
    @classmethod
    def _blank_written_at(cls, value: object) -> object:
        return None if value == "" else value


class CommentCsvRow(CsvRow):
    # 取り込むときは、日記の CSV の id(取り込んだ日記の migration_id)を指す
    diary_id: int


def read_rows[R: CsvRow](csv_text: str, row_model: type[R]) -> list[R]:
    rows = []
    # 1 行目は見出しなので、データの行は 2 行目から数える
    for line, row in enumerate(csv.DictReader(io.StringIO(csv_text.lstrip("﻿"))), start=2):
        try:
            rows.append(row_model.model_validate(row))
        except ValueError as e:
            raise ValueError(f"CSV の {line} 行目が読めない: {e}") from e
    return rows


def write_rows(rows: Iterable[CsvRow], columns: list[str]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        values = row.model_dump(include=set(columns))
        for name in ("time", "written_at"):
            if isinstance(values.get(name), datetime):
                values[name] = values[name].astimezone(JST).strftime(CSV_TIME_FORMAT)
        writer.writerow(values)
    return out.getvalue()
