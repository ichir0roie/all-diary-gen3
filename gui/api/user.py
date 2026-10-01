#!/usr/bin/env python3
"""要求を出した人。API は Cognito のトークンを自分では確かめない。

画面の Next.js のサーバー(`gui/web/app/api/[...path]/route.ts`)が、クッキーのトークンを Cognito の公開鍵で確かめてから
その人の sub を `x-diary-user` に入れて流す。API には合言葉(`DIARY_API_KEYS`)と関数 URL の IAM の署名が要り、
それを持つのはその route handler だけなので、この見出しはその route handler が付けたものとして信じる。
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

USER_HEADER = "x-diary-user"


def user_id_dep(x_diary_user: Annotated[str | None, Header()] = None) -> str:
    if not x_diary_user:
        raise HTTPException(status_code=401, detail=f"{USER_HEADER} が無い")
    return x_diary_user
