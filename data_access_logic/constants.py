#!/usr/bin/env python3
from __future__ import annotations

from datetime import timedelta, timezone

# 時差の無い時刻(以前の db・CSV・画面の入力)を読むときの時差。日本に夏時間は無いので、固定の +9 時間でよい
JST = timezone(timedelta(hours=9), "JST")

# data_access_logic/csv_file
# 以前の db から書き出した CSV の時刻の書式(日本時間、時差無し)。書き出しも同じ書式にして、取り込み直せるようにする
CSV_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
