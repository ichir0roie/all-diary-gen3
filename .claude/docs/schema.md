# schema の確認方法

- 列の定義は `db/schema.py` が唯一の正。列名・型を確かめたいときは、db へクエリを打たず、この `db/schema.py` を Read する。
- マイグレーションは `db/alembic/`。コマンド例は `db/alembic/README` にある。
- `schema.py` を変えたら alembic の `revision --autogenerate` → 内容確認 → `upgrade head` の順。
  autogenerate は手元の開発用の db(`DIARY_DEV_DATABASE_URL`)に向けて回す。RDS に当てるのはユーザに言われてから(`.claude/docs/aws.md` の決まり 1)
- 日記・コメントは人(`user_id`。Cognito のユーザーの sub)ごとの行。読む処理は必ず `user_id` で絞り、他の人の行は無い行と同じに扱う
  (`data_access_logic/query/common_query.py` の `own_row`)
- 時刻(`time`)は時差を持つ時刻(timestamptz)。時差の無い時刻は日本時間として読む(`data_access_logic/material.py` の `JstTime`)。
  日付で絞るときは日本時間の暦の日で切る(`common_query.in_days`)
- NULL を持てる列で並べるときは NULL の向き(降順は `.nulls_last()`)を明示する
