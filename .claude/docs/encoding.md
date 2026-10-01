# 文字コード

- リポジトリのテキスト(`.py` `.md` `.json` `.ts` など)はすべて UTF-8(BOM 無し)。
  ファイルを開くときは必ず `encoding="utf-8"` を付ける
- db(PostgreSQL)も UTF-8 で作る(`db.postgres.init_db` の `CREATE DATABASE ... ENCODING 'UTF8'`)
- 取り込む CSV は UTF-8。先頭に BOM があっても読む(`data_access_logic/csv_file/rows.py`)
- Windows の python は標準出力が cp932 になるため、日本語を出すコマンドは
  `PYTHONUTF8=1` を付けて実行する(付けないと文字化け・`UnicodeEncodeError` になる)
