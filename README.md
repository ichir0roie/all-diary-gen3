# all-diary-gen3

日記を書き、同じ時期の一週間を今年・去年・一昨年と並べて読み返すための道具。日記にはあとからコメントを足せる。
書いた日記とコメントは、自分の AWS に建てた db(RDS for PostgreSQL)に置き、このリポジトリには入れない。
建て方は `.docs/aws-deploy.md`、手元の用意は `.claude/docs/setup.md`。

以前の `all_diary_front`(画面)と `all_diary_backend`(API)をこのリポジトリにまとめ、ai-novel-core と同じ形に組み直した
(何を変えたか・以前の日記の移し方は `.docs/migration.md`)。

## 特徴

- **三年を並べて読む。** 同じ時期の一週間を、年ごとに横に並べる(狭い画面では今年だけ)
- **db に触れる処理を一本化。** db を読み書きする処理と入口は `data_access_logic/` にまとめ、Claude(CLI)も API も同じ入口を呼ぶ
- **人ごとの日記。** どの入口も書いた人(Cognito のユーザーの sub)で行を絞る。誰の日記かは、画面のサーバーがログインを確かめてから API に渡す
- **CSV で出し入れ。** 書き出した CSV はそのまま取り込み直せる。以前の db の CSV も取り込める
- **テストは本番に触れない。** 手元の PostgreSQL に作った空の db に、テストが自分の行を足す

## ディレクトリ

| ディレクトリ | 役割 |
| --- | --- |
| `db/` `data_access_logic/` | 仕組み。db の形・入口・問い合わせ |
| db(RDS) | **日記とコメントそのもの**(PostgreSQL。AWS 側) |
| `gui/` | 画面と API。使い方は `gui/readme.md` |
| `.docs/` | 設計・運用の文書(PostgreSQL・AWS へのデプロイ・以前のリポジトリからの移し方) |
| `CLAUDE.md` | **Claude 向けの作業指針** |

```
db/                 **記録の形(SQLAlchemy)。列はここ一か所で決まる**
                    alembic/ にマイグレーション、postgres/ に空の db の作り方
data_access_logic/  **db を読み書きする処理と入口。db に触れるのはここ越しだけ**(一覧は data_access_logic/readme.md)
                    diary/ comment/ csv_file/ query/
gui/                api/(FastAPI)と web/(Next.js)
tool/               AWS の RDS へ踏み台越しに繋ぐ aws/rds(--serve でふだんの転送、-- <コマンド> でマスターで流す)、
                    テスト用の db を作る test/(必ず手元の PostgreSQL のテスト用の db を使う)
tests/              pytest。claude_interface/(入口)と api/(API)
infra/              AWS のリソース(CDK、TypeScript。npx cdk deploy)。既存の db・踏み台は作り直さず参照できる
  lambda/           API を Lambda(Lambda Web Adapter)で動かすコンテナ。amplify.yml(ルート)は画面を Amplify で建てる設定
infra_local/        手元・クラウドのセッションで使う開発用のリソース(空の PostgreSQL を用意する postgres.sh)
```
