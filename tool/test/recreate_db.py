#!/usr/bin/env python3
"""テスト用の db(`diary_test`)を消し、`schema.py` から空の db を作り直す。リポジトリのルートから:

    .venv/bin/python -m tool.test.recreate_db

pytest は、テスト用の db があればそのまま使うので、マイグレーションを足したあとに回す。
"""
from tool.test import recreate_test_db  # db をテスト用の db に固定する(schema より先に読む)

from data_access_logic.logs import configure_logging


def main() -> None:
    configure_logging()
    recreate_test_db()


if __name__ == "__main__":
    main()
