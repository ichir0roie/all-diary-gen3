#!/usr/bin/env python3
"""開発用の db(`diary_dev`)を消して `schema.py` から作り直し、作り物の日記とコメントを入れる。リポジトリのルートから:

    .venv/bin/python -m tool.dev.reset_db                  # 今の前後 10 年に日記 3000 件
    .venv/bin/python -m tool.dev.reset_db --count 500 --seed 1

引数は `tool.dev.mock_data` と同じ。画面で試しに書いた日記・コメントも消える。
"""
from tool.dev import DEV_DATABASE_URL  # db を開発用の db に固定する(schema より先に読む)

from tool.dev import mock_data  # noqa: E402
from tool.local_db import recreate_local_db  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    recreate_local_db(DEV_DATABASE_URL)
    mock_data.main(argv)


if __name__ == "__main__":
    main()
