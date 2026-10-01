# 以前のリポジトリからの移し方

以前は画面(`all_diary_front`、Next.js + Amplify Gen2 の Auth)と API(`all_diary_backend`、FastAPI + SQLite)を別々のリポジトリで持っていた。
このリポジトリに二つをまとめ、ai-novel-core と同じ形(`db/` `data_access_logic/` `gui/api` `gui/web` `infra/` `tool/` `tests/`)に組み直した。

## 何がどこへ移ったか

| 以前 | 今 |
| --- | --- |
| backend `module/db/db.py`(SQLAlchemy の表と SQLite の engine) | `db/schema.py`(PostgreSQL。engine は `DIARY_DATABASE_URL`)、`db/alembic/`(マイグレーション) |
| backend `module/api/query/*`・`module/api/schema/*` | `data_access_logic/diary/`・`comment/` の入口(`ListDiaries` など)、フォーム(`form.py`)とレスポンス(`record.py`) |
| backend `module/db/csv_insert.py`・`csv_dump.py`(pandas) | `data_access_logic/csv_file/`(標準の `csv` と pydantic) |
| backend `module/api/endpoint/*`・`app/fastapi_app.py` | `gui/api/app.py` |
| backend `module/api/auth/auth.py`(API が Cognito の JWT を確かめる) | `gui/web/app/api/[...path]/route.ts`(Next.js のサーバーが確かめ、`x-diary-user` で渡す)と `gui/api/user.py` |
| backend `dockerfiles/rest_api.dockerfile` | `infra/lambda/Dockerfile` |
| front `api/*`(ブラウザから API を直に呼ぶ) | `gui/web/lib/api.ts`(同じオリジンの `/api/*`。型は OpenAPI から生成) |
| front `components/*`(react-bootstrap) | `gui/web/components/*`(素の CSS。`app/globals.css`) |
| front `app/manage/upload` | `gui/web/app/manage`(取り込みと書き出し) |
| front `amplify/`(Amplify Gen2 の Auth) | `infra/lib/auth-stack.ts`(CDK の Cognito)、`amplify.yml`(画面だけを Amplify Hosting で建てる) |

## 変えたこと

- db を SQLite(Lambda の中のファイルを S3 に置き直す形)から RDS for PostgreSQL にした。ai-novel-core と同じインスタンスを使い回せる
  (db は `diary` に分ける)。そのため、S3 との db のファイルの出し入れと、それを回していたバッチの Lambda(`app/admin_function.py`。
  insert / dump / dump_month / reset / replace / save)はやめた。戻せる備えは RDS の自動バックアップ(7 日)と、画面の CSV の書き出しが受け持つ
- 時刻を時差付き(timestamptz)にした。時差の無い時刻は日本時間として読む([postgres.md](postgres.md#時刻))
- 日記・コメントの読み書きを、どれも書いた人(`user_id`)で絞るようにした。以前は、コメントの一覧・一件と CSV の書き出しが
  他の人の行も返し、他の人の日記にもコメントを足せた
- 以前の db ファイル(SQLite)をそのまま取り込めるようにした。取り込みは、時刻と本文が同じ行が db に既にあれば足さない(取り込み直しても重ならない)。
  同じ時刻の行を一件に限る制約は置かない(以前の db に、同じ時刻で本文の違う行がある)。書き出しにコメントの `id` を足し、
  取り込み直せる形にした(以前の書き出しは `id` が無く、以前の取り込みで読めなかった)
- 日記・コメントの時刻は API が決める(以前は画面が自分の時計で送っていた)
- 画面からのユーザー登録を閉じた(使う人は `aws cognito-idp admin-create-user` で作る)
- 使っていなかったもの(テスト用のエンドポイント `/test/*` と表 `count`、SQS の処理、画像のアップロードの欄)は移さなかった

## データを移す

以前の db の行は、以前の API の SQLite の db ファイルをデータの画面(`/data`)から取り込んで移す。新しい Cognito のユーザープールでは
ユーザーの sub が変わるので、取り込んだ行は取り込んだ人の行になる(ファイルの中のどの人の行を取り込むかは画面で選ぶ)。

1. 最新の db ファイルを取り出す(下の「最新の db ファイルの在りか」)
2. 新しい画面に、移す先の人でログインし、データの画面で db ファイルを選ぶ。中の人ごとの件数と期間が出るので、自分を選んで取り込む
3. 取り込みは時刻と本文が同じ行を足さないので、移行のあいだ以前の画面で書き足した分は、もう一度新しい db ファイルを取り出して取り込めば入る

CSV(以前の API の `/manage/export_csv/*`、バッチの `dump`、以前の `data/csv/input/`)も同じ画面から取り込める。
列は 日記 `user_id,text,id,time`、コメント `diary_id,text,id,time`。コメントの `diary_id` は日記の CSV の `id` を指すので、日記が先。

手元から入口で取り込むこともできる(`data_access_logic/readme.md` の `ImportLegacyDb` / `ImportDiaryCsv` / `ImportCommentCsv`)。

## 最新の db ファイルの在りか

以前の API とバッチの Lambda は、EFS のアクセスポイントを `/mnt/db` にマウントし、
`/mnt/db/sqlite.db` を読み書きしている。最新はここにだけある。

- S3 の `dump/db/<年月>.db` は、バッチの `save` が月に一度ほど写したもの。最後に写したのは 2026-03 で、それ以降に書いた分は入っていない
- 以前の API・バッチの実行ロールには S3 に書く権限が無く、バッチの環境変数にも書き出し先(`S3_BUCKET`)と `OPERATION` が無い。
  2026-10-01 に、次の手順で EFS の db ファイルを S3 の `dump/db/202610.db` に写した。もう一度取り出すときも同じ手順でよい
  1. バッチ・API の共通の実行ロールに、S3 の `dump/db/*` への `s3:PutObject` だけを許すインラインポリシーを一時的に足す
  2. バッチの環境変数に `S3_BUCKET` と `OPERATION=1` を足し、`{"event": "save"}` で呼ぶ(`dump/db/<年月>.db` に写る)
  3. 環境変数を `DB_PATH` だけに戻し、インラインポリシーを消す
- バッチの関数は、参照していたイメージ(digest)が ECR から消えて Inactive になっていたので、同じリポジトリの `latest`(2026-03-31 に push したもの)に
  向け直した。消えたイメージには戻せない

## 以前の db ファイルの癖

- 以前の CSV の取り込み(pandas)が書いたコメントの `diary_id` は、整数でなく 8 バイトのバイナリで入っている。SQL の結合ではどの日記にも
  結び付かないので、以前の画面ではこれらのコメントが出ていなかった。取り込み(`data_access_logic/legacy_db/reading.py`)は整数に読み替えて日記を引く
- 2026-10 の db ファイルには、日記の持ち主(Cognito のユーザーの sub)が二人いる。片方は 2026-03-31 に同じ CSV をもう一度取り込んだ写しで、
  もう片方にしか無い日記は 1 件だけ。ふつうは件数の多い方(今も書いている方。画面が初めから選ぶ)を取り込む
- 同じ時刻で本文の違う日記・コメントがある([postgres.md](postgres.md#時刻))
