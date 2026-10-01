# .docs — 設計と運用の覚え書き

人が読むための設計・運用の文書を置く。Claude 向けの作業指針は `CLAUDE.md` と `.claude/docs/` にある。

| 文書 | 中身 |
| --- | --- |
| [postgres.md](postgres.md) | PostgreSQL の db の作り方、開発・テスト用の手元の db、時刻の持ち方 |
| [aws-deploy.md](aws-deploy.md) | AWS に置く形(Amplify の画面 / Lambda Web Adapter の API / RDS / Cognito)、`infra/` の CDK、手元から db へ繋ぐ道(`tool.aws.rds`) |
| [ci-cd.md](ci-cd.md) | GitHub から Lambda・Amplify への自動デプロイ(OIDC・変数・マイグレーションの流し方) |
| [migration.md](migration.md) | 以前の二つのリポジトリ(`all_diary_front` / `all_diary_backend`)からの移し方と、変えたこと |

## 全体の形

```
ブラウザ ──(Cognito でログイン)──▶ Amplify Hosting: gui/web(Next.js)
                                      │ /api/* を route handler が流す。トークンを確かめ、その人の sub を x-diary-user に入れる。
                                      │ SigV4 の署名と x-diary-api-key を付ける
                                      ▼
                               Lambda(関数 URL、AWS_IAM)+ Lambda Web Adapter: gui/api(FastAPI, uvicorn)
                                      │ SQLAlchemy(DIARY_DATABASE_URL)。VPC の中。IAM データベース認証
                                      ▼
                               RDS for PostgreSQL(db diary。private subnet。ai-novel-core と同じインスタンスを使い回せる)
                                      ▲
手元 ──(EC2 Instance Connect Endpoint)──▶ 踏み台 ┘ tool.aws.rds(--serve: ふだんの読み書き。-- <コマンド>: マイグレーションなど)
```

AWS のリソースは `infra/` の CDK で持つ([aws-deploy.md](aws-deploy.md#infracdk))。

- db は RDS ただ一つ。手元の CLI・`gui.dev`・Claude Code も、踏み台越しの転送(`tool.aws.rds --serve`)で RDS を読み書きする(`.claude/docs/setup.md`)。
  以前の SQLite の db は使わない
- 開発・テストでは、手元に作った空の PostgreSQL を使う([postgres.md](postgres.md#開発用の-db))
