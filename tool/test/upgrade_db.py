#!/usr/bin/env python3
"""テスト用の db(`diary_test`)を、行を残したままコードの版(alembic の head)まで上げる。リポジトリのルートから:

    .venv/bin/python -m tool.test.upgrade_db

マイグレーションそのものを手元で試すときに使う。ふつうは `tool.test.recreate_db` で作り直せばよい。
"""
from tool.test import TEST_DATABASE_URL  # noqa: F401  db をテスト用の db に固定する(schema より先に読む)

from data_access_logic.logs import configure_logging  # noqa: E402
from tool.local_db import upgrade_local_db  # noqa: E402


def main() -> None:
    configure_logging()
    upgrade_local_db()


if __name__ == "__main__":
    main()
