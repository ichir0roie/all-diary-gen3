# 作業指針

Claude はユーザへの返答を常に日本語で書く。

日記とコメントは db(AWS の RDS)にだけあり、このリポジトリには無い。日記は人の書いたものなので、
読み書きは頼まれた範囲だけにし、本文を報告やログ・コミットに写さない。

# 作業する場所

作業する場所は二つあり、環境変数 `CLAUDE_CODE_REMOTE` で見分ける。

| 場所 | `CLAUDE_CODE_REMOTE` | SessionStart フック(`.claude/hooks/session-start.sh`) | db | git |
| --- | --- | --- | --- | --- |
| 手元(CLI・VS Code) | `true` でない | `.venv` を用意し、RDS への転送を起こして `DIARY_DATABASE_URL` を渡す | 入口越しに直に読み書きする | 頼まれたときだけ |
| web のセッション(Claude Code on the web) | `true` | `.venv` を用意する | 繋がない(コードとテストだけ) | セッションの指示に従う |

# 条件付きのドキュメント

次の表の条件に当てはまる作業をするときは、始める前に対応するファイルを Read し、それに従う。
当てはまらなければ読まなくてよい。パスはリポジトリのルートから書いてある。

| 条件 | 読むファイル |
| --- | --- |
| コマンドの実行でエラーが出たとき | `.claude/docs/command-errors.md` |
| ファイルを読み書きするコードを書くとき、日本語を出すコマンドを打つとき | `.claude/docs/encoding.md` |
| リポジトリの構成・環境変数を扱うとき、python・pytest・alembic を動かすとき、`.venv` を用意するとき | `.claude/docs/setup.md` |
| git でコミット・push・merge・ブランチ操作をするとき、worktree で作業してと頼まれたとき | `.claude/docs/git.md` |
| 手元で db を読み書きするとき(入口の呼び出し・作成、マイグレーションの確認を含む) | `.claude/docs/db.md` |
| テストをしてと明確に依頼されたとき | `.claude/docs/testing.md` |
| テスト・動作確認で GUI(API・画面)を動かすとき | `.claude/docs/gui.md` |
| 列名・型を確かめるとき、`db/schema.py` やマイグレーションを変えるとき | `.claude/docs/schema.md` |
| db を読む処理(pydantic のマテリアル・入口の引数とレスポンス)を書く・直すとき、リファクタするとき | `.claude/docs/data-access.md` |
| PostgreSQL(`DIARY_DATABASE_URL`)・AWS へのデプロイ・GitHub Actions を扱うとき | `.docs/README.md` から当たる文書 |
| AWS の db・資源に触れるとき、API(Lambda)のコードを書くとき | `.claude/docs/aws.md` |

# コーディング規約

コードを読んで内容を理解すること。
コードを読んでも分からない理由のみコメントにする。
途中経過や失敗の知らせは `logging`(モジュールごとの `logger`)で出す。`print` は `show()` のように、標準出力に出すものが結果そのものの所だけに使う。
SQLAlchemy のセッションは、引数も変数も `s` と書く(`s: Session`、`with get_env_session() as s:`)。
python を直したら、ルートで `uvx ruff check .` と `npx pyright --pythonpath .venv/bin/python` を回す(設定は `ruff.toml` / `pyrightconfig.json`)。
画面(`gui/web`)を直したら、`gui/web` で `npm run typecheck` と `npm run lint` を回す。
