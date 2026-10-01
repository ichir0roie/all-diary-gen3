# 手元からの db(`CLAUDE_CODE_REMOTE` が `true` でない)

db は AWS の RDS(PostgreSQL、db `diary`)ただ一つ。手元の作業も、画面(Amplify)と同じ db を読み書きする。
web のセッションは db に繋がない。

## 手元からの道

SessionStart フックが、踏み台越しの転送(`tool.aws.rds --serve`、127.0.0.1:25432)を裏で起こし、次の環境変数を渡す。
python はリポジトリのルートの `.venv/bin/python` で呼べば、そのまま RDS を読み書きする。

| 環境変数 | 値 |
| --- | --- |
| `DIARY_DATABASE_URL` | `postgresql+psycopg://diary_app@127.0.0.1:25432/diary?sslmode=require` |
| `DIARY_DATABASE_IAM_AUTH` | `1`(パスワードの代わりに IAM データベース認証のトークンで繋ぐ。パスワードはどこにも置かない) |

- `diary_app` は行の読み書き(DML)だけができる。表を作る・変える(DDL)ことはできない
- `connection refused` で落ちたら、転送がまだ張れていない(踏み台が止まっていれば起こすのに 1 分ほどかかる)か、落ちている。
  `.cache/rds-tunnel.log` を見て、無ければ `.venv/bin/python -m tool.aws.rds --serve` を `run_in_background` で起こす
- 転送は EC2 Instance Connect Endpoint の都合で 1 時間ごとに切れ、`--serve` が張り直す。その間に落ちた処理はやり直す
- 止めるのは `pkill -f 'tool.aws.rds --serve'`(自分で起こした踏み台も止まる)。ユーザに頼まれたときだけ止める。
  踏み台を ai-novel-core と使い回しているときは、こちらが起こした踏み台を止めると向こうの転送も切れる

## 読み書きの決まり

- コードから触るときは `from db.schema import get_env_session` で `Session` を開く。`engine` も同じモジュールにある
- 作業として db を読み書きするときは `data_access_logic/` の入口越しに、既存の python コードを呼んで行う
- `data_access_logic/readme.md` を操作前のマニュアルとする。操作の前にその「依頼内容 → 呼ぶコード」の
  対応表を引き、依頼に当たる入口を呼ぶ
- 対応する入口が無ければ、readme の形に沿って入口を新しく作ってから行う。
  足したら同じ作業のうちに readme の対応表へ行を足す(表に無い入口は次から見えない)
- 入口は `user_id`(Cognito のユーザーの sub)を取る。ユーザの sub が分からなければ尋ねる。推し量って他の人の行に書かない
- 読み取り(`select`)だけなら入口を通さなくてよい。件数・日付の範囲などを覗くのは好きにしてよいが、日記の本文は頼まれた分だけ読む。
  書き込み(`insert` `update` `delete`)は必ず入口越しに行う
- 調査用の読み取り例:

```
.venv/bin/python -c "
from sqlalchemy import text
from db.schema import engine
with engine.connect() as c:
    print(c.execute(text('select user_id, count(*), min(time), max(time) from diary group by user_id')).all())
"
```

## マイグレーションの確認

db の版は、コードの版(`alembic heads`)と揃っていなければならない。列が増えていると、db を読む入口が
`column ... does not exist` で止まる。db を触る作業の前に食い違いを見つけたら、ユーザに伝える
(RDS へ当てるのはユーザに言われてから。`.claude/docs/aws.md` の決まり 1)。

```
.venv/bin/python -m alembic -c db/alembic/alembic.ini current   # diary_app でも版は読める
.venv/bin/python -m alembic -c db/alembic/alembic.ini heads
```

当てるときは表を変えるのでマスターで流す:
`.venv/bin/python -m tool.aws.rds -- .venv/bin/python -m alembic -c db/alembic/alembic.ini upgrade head`
