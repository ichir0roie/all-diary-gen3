#!/usr/bin/env python3
"""API の入出力の形のうち、入口(`data_access_logic`)のモデルで足りないもの。OpenAPI に出て、
フロント(`gui/web`)の型(`lib/openapi.d.ts`)の元になる。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

# CSV で出し入れする表
CsvKind = Literal["diary", "comment"]


class Health(BaseModel):
    dialect: str


class CsvImportRequest(BaseModel):
    # CSV の中身。ファイルはブラウザで読んで文字列で渡す(multipart にしない)
    text: str


class SimilarSearchRequest(BaseModel):
    # 探す文章(書いている途中の日記)。長くなるので、クエリではなく本文で渡す
    text: str


# ファイルを本文にそのまま載せる要求(以前の SQLite の db ファイル)。読むのは `Request.body()` なので、OpenAPI にだけ形を書く
FILE_BODY: dict[str, Any] = {
    "requestBody": {"required": True, "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}},
}
