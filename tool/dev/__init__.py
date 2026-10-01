"""手元で画面・API を試すための道具。この下のモジュールは必ず、手元の PostgreSQL の開発用の db(`diary_dev`)を読み書きする。

`db.schema` は import 時に `DIARY_DATABASE_URL` で engine を固定するので、この package の読み込みで環境変数を差し替える。
日記は人の書いたものなので、本番の行は写さず、作り物の行(`tool.dev.mock_data`)を入れて試す。
"""
from tool.local_db import local_database_url, pin_database_url

DEV_DATABASE_NAME = "diary_dev"
DEV_DATABASE_URL = local_database_url(DEV_DATABASE_NAME)
pin_database_url(DEV_DATABASE_URL, "tool.dev")
