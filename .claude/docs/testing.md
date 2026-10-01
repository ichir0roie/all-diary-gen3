# テスト

テストをしてと明確に依頼されたら、そのとき要るテストを `tests/` に書いて実行する(`.venv/bin/python -m pytest tests`)。

- テストは手元の PostgreSQL のテスト用の db(`diary_test`。開発用の db と同じサーバー)だけを読み書きする。
  `tests/conftest.py` で `tool.test` を先に読んで固定する。本番の RDS には書き込まない(`tool.test` は、テスト用の db が
  手元のサーバーを指していなければ止まる)。`DIARY_DEV_DATABASE_URL` が無ければ、`tool.test` がその場で `infra_local/postgres.sh` を回して用意する
  (手元は Docker のコンテナ `diary-postgres`、web のセッションは apt で入れた PostgreSQL)
- テスト用の db は本番を写さず、`schema.py` から空の db を作る(日記は人の書いたものなので、手元にも写さない)。
  行はテストごとに `conftest.py` の `book` が、毎回新しい `user_id` で足す。前のテストの行が残っていても混ざらない
- `conftest.py` はテストの始めに `tool.test.ensure_test_db` を回す。テスト用の db が無いときだけ作る。
  マイグレーションを足したあと、版の食い違いの警告が出たら `.venv/bin/python -m tool.test.recreate_db` で作り直す
  (VS Code はタスク「test db recreate」)
- 入口のテストは `tests/claude_interface/`(claude と同じく `show()` を呼ぶ)、API のテストは `tests/api/`(TestClient。
  画面の route handler の代わりに `x-diary-user` を付ける)
- alembic のテスト、ダウングレードのテストはやらない
