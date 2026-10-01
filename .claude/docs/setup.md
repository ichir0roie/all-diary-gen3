# 環境構築

このリポジトリ(`all-diary-gen3`)だけで動く。日記とコメントは db(AWS の RDS)にだけ置き、リポジトリには入れない。
以前の二つのリポジトリ(`all_diary_front` と `all_diary_backend`)と、その SQLite の db は使わない(移し方は `.docs/migration.md`)。

## 構成

```
db/                 記録の形(SQLAlchemy)。列はここ一か所で決まる。alembic/ にマイグレーション、postgres/ に空の db の作り方
data_access_logic/  db を読み書きする処理と入口。db に触れるのはここ越しだけ(一覧は data_access_logic/readme.md)
                    diary/ comment/ csv_file/(CSV の出し入れ) query/(入口が共に使う問い合わせ)
gui/                api/(FastAPI)と web/(Next.js)。使い方は gui/readme.md
tool/               AWS の RDS へ踏み台越しに繋ぐ aws/rds、テスト用の db を作る test/、開発用の db にモックの行を入れる dev/
tests/              pytest(入口と API)
infra/              AWS のリソース(CDK、TypeScript)。lambda/ に API のコンテナ
infra_local/        開発・テスト用の空の PostgreSQL を用意する postgres.sh
```

## python

python・pytest・alembic はリポジトリのルートを cwd にし、ルートの `.venv/bin/python`(Windows は `.venv\Scripts\python.exe`)で呼ぶ。
`PYTHONPATH` はリポジトリのルート(SessionStart フックと `.vscode` が渡す)。
python の版は `.python-version`(3.14)に書く。Claude Code のセッションでは SessionStart フック(`.claude/hooks/session-start.sh`)が
`.venv` を用意する。手で用意するときは(python 本体は uv が取ってくる。uv が古いと新しい版を知らないので、uvx で新しめの uv を使う):

```
uvx --from 'uv>=0.9' uv venv --python 3.14 .venv
uvx --from 'uv>=0.9' uv pip install --python .venv/bin/python -r requirements.txt
```

`.venv` に pip は入らない。

`requirements.txt` は、依存の依存まで版とハッシュを固定したもので、手では書かない。直接使うパッケージは `requirements.in` に書き、
そこから作る(Windows でも同じファイルで入るよう `--universal` で作る)。パッケージを足す・版を上げるときは、`requirements.in` を直してから:

```
uvx --from 'uv>=0.9' uv pip compile requirements.in --universal --python-version 3.14 --generate-hashes -o requirements.txt
uvx --from 'uv>=0.9' uv pip install --python .venv/bin/python -r requirements.txt
```

固定した版の中で上げるだけなら、1 行目に `--upgrade-package <名前>`(全部なら `--upgrade`)を足す。

## db と環境変数

| 環境変数 | 中身 | 渡す所 |
| --- | --- | --- |
| `DIARY_DATABASE_URL` | 読み書きする db。手元は踏み台越しの RDS(`postgresql+psycopg://diary_app@127.0.0.1:25432/diary?sslmode=require`) | SessionStart フック・`.vscode`(ターミナル・タスク・デバッグ) |
| `DIARY_DATABASE_IAM_AUTH` | `1` なら IAM データベース認証のトークンで繋ぐ | 同上 |
| `DIARY_DEV_DATABASE_URL` | 開発用の空の PostgreSQL(`infra_local/postgres.sh`)。テストの db もこのサーバーに作る | `.vscode` は固定の値。Claude Code では渡さず、テスト(`tool.test`)が要ったときに用意する |
| `PYTHONUTF8` | `1`(Windows の文字化け除け。`.claude/docs/encoding.md`) | 同上 |

- 手元から RDS へは、踏み台越しの転送(`.venv/bin/python -m tool.aws.rds --serve`)を張って繋ぐ。SessionStart フックが裏で起こし、
  VS Code ではタスク「db tunnel」で起こす。繋ぎ方の決まりは `.claude/docs/db.md`、AWS の側は `.claude/docs/aws.md`
- 転送のポートは 25432。同じ RDS を使い回す ai-novel-core の転送(15432)と同時に張れるよう分けてある
- `DIARY_DATABASE_URL` が無くても import はできる。繋いだ時点で止まる
- テストは `DIARY_DATABASE_URL` を手元の PostgreSQL のテスト用の db に差し替える(`.claude/docs/testing.md`)

## git

git のコマンドはリポジトリのルートで打つ。決まりは `.claude/docs/git.md`。
