# PostgreSQL

db は PostgreSQL。本番は AWS の RDS(db `diary`、[aws-deploy.md](aws-deploy.md))、開発・テストは手元の PostgreSQL。
表の形は `db/schema.py` が唯一の正で、変更は alembic のマイグレーション(`db/alembic/`)で当てる。

## 空の db を作る

`db.postgres.init_db` が、空の db に `schema.py` から今の形をそのまま作り、alembic を head に stamp する。

```
DIARY_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/diary .venv/bin/python -m db.postgres.init_db --create-database
```

RDS に作るときは、マスターで流す(`tool.aws.rds` がマスターの `DIARY_DATABASE_URL` を渡す)。
`--create-database` は、同じサーバーの `postgres` db に繋いで `CREATE DATABASE` する。

```
.venv/bin/python -m tool.aws.rds --database diary -- .venv/bin/python -m db.postgres.init_db --create-database
```

`init_db` の代わりに、空の db へ `alembic upgrade head` を流しても同じ形になる(最初のマイグレーションが表を作る)。

## 開発用の db

`infra_local/postgres.sh` が、開発用の PostgreSQL を用意して空の db(`diary_dev`)の URL を出す。何度走らせてもよい。

| 場所 | サーバー | URL |
| --- | --- | --- |
| 手元 | Docker のコンテナ `diary-postgres`(`postgres:18`、ボリューム `diary-postgres-data`) | `postgresql+psycopg://diary:diary@127.0.0.1:55433/diary_dev` |
| web のセッション | apt で入れた PostgreSQL | `postgresql+psycopg://diary:diary@127.0.0.1:5432/diary_dev` |

テスト(`tool.test`)は、同じサーバーの `diary_test` を使う。本番の行は写さず、テストが自分の行を足す(`.claude/docs/testing.md`)。

## 時刻

日記・コメントの `time` は時差を持つ時刻(`timestamp with time zone`)。db の中では UTC の時点として持ち、読み出しは日本時間にそろえる
(`data_access_logic/material.py` の `JstTime`)。

- 時差の無い時刻(以前の db・CSV の `2021-01-02 09:00:00.000000`、`"2026-10-01 21:00"` のような入口への入力)は日本時間として読む。
  以前の画面は日本時間の時刻を時差無しで送り、以前の db は時差無しで持っていたので、その意味に合わせた
- 日付で絞る(`start_date` / `end_date`)ときは、日本時間の暦の日で切る(`common_query.in_days`)
- 同じ時刻の行を一件に限らない。以前の db には、同じ時刻で本文の違う日記・コメントが入っている(続けて書いた分を取り込んだもの。
  以前の `schema.py` には一意の制約が書いてあったが、db の表には掛かっていなかった)。取り込みは、時刻と本文がどちらも同じ行を同じものとみなして
  重ねない(`data_access_logic/query/import_query.py`)
