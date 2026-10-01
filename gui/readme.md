# gui — 日記の画面と API

日記を書いて読むための道具。API(`gui/api`、FastAPI)と画面(`gui/web`、Next.js)の二つ。

- 日記の画面(`/`): 同じ時期の一週間を、今年・去年・一昨年と横に並べる(狭い画面では今年の一列だけ)。
  Year / Week のボタンで年と週をずらす。下の欄で日記を書き、日記を押すとコメントを書くモーダルが開く
- データの画面(`/data`): 取り込みと書き出し。以前の API の SQLite の db ファイルを選ぶと、中の人ごとの件数を出し、選んだ人の日記と
  コメントを自分の行として取り込む。日記・コメントの CSV の取り込みと、取り込み直せる形の CSV の書き出しもここ。
  どの取り込みも、時刻と本文が同じ行が既にあれば足さないので、同じファイルや新しいファイルを取り込み直してよい

## 構成の決め方

列の定義(`db/schema.py`)、値の型(時刻の時差)、確定のときの検証(自分の日記か)はすべて python 側にある。
Next.js から db を直接開くと、その全部を TypeScript にもう一度書くことになり、正が二つになる。そのため API は FastAPI で python 側に置き、
読み書きは `data_access_logic/` の入口(`execute(s)`)を通す。
型は FastAPI の OpenAPI(`gui/api/openapi.json`)から `gui/web/lib/openapi.d.ts` を生成して合わせる。
画面に出す文言(ボタン・見出し・状態表示など、英語)は `gui/web/lib/text.ts` の `T` に集め、ページ・コンポーネントには直書きしない。

誰の日記かは、画面の Next.js のサーバー(`gui/web/app/api/[...path]/route.ts`)が決める。Cognito のトークン(クッキー)を
公開鍵で確かめ、その人の sub を `x-diary-user` に入れて API へ流す。ブラウザから来た同じ名前の見出しは流さない。
ログインを掛けない手元では、`DIARY_LOCAL_USER_ID`(既定 `local`)の人として流す。

## 起動

リポジトリのルートで(環境変数は他の python と同じ。db は `DIARY_DATABASE_URL` の RDS で、踏み台越しの転送を先に張っておく。
`.claude/docs/setup.md`)。API と画面を一緒に起こしてブラウザで開くのは `gui.dev`。
`gui/web/node_modules` が無ければ先に `npm install` を回す。VS Code なら タスク `db tunnel` のあとに `app`(`.vscode/tasks.json`)。

```
.venv/bin/python -m gui.dev              # API :8766 + 画面 :3001 を起こし、http://localhost:3001 を開く。Ctrl+C で両方止める
                                          # 片方が落ちてももう片方は止めず、落ちた方だけ自動で再起動する
.venv/bin/python -m gui.dev --no-browser # 開かない。--api-port / --web-port でポートを変える
.venv/bin/python -m gui.dev --browser-only # API・画面はすでに起きている前提で、ブラウザだけ開く
```

ポートは ai-novel-core の GUI(8765 / 3000)と同時に動かせるよう分けてある。ポートが既に使われていれば(前回の起動の残りなど)、
それを聞いている処理を止めてから起こす。`next dev` はビルド先(`gui/web/.next`)ごとに 1 つしか動かせないので、
2 つ目を起こすときは環境変数 `DIARY_WEB_DIST_DIR` でビルド先を分ける(テスト用は `.next-test`)。
画面は `localhost` で開く(`127.0.0.1` だと `next dev` が開発用の読み込みを弾く)。

手元で日記を書く人を Cognito の自分と同じにしたいときは、`DIARY_LOCAL_USER_ID` に自分の sub を渡して起こす。

別々に起こすなら次の二つ。

```
.venv/bin/python -m uvicorn gui.api.app:app --port 8766 --reload --reload-dir data_access_logic --reload-dir db --reload-dir gui/api
(cd gui/web && npm install && DIARY_API_URL=http://127.0.0.1:8766 npm run dev -- --port 3001)
```

`/api/*` は Next.js の route handler が `DIARY_API_URL`(既定 `http://127.0.0.1:8766`)へ流すので、ブラウザから見ると同じオリジンになる。
`DIARY_API_KEY` があれば、流すときに `x-diary-api-key` を付ける(API 側は `DIARY_API_KEYS` に呼ぶ側ごとの鍵を `gui=…` の形で持ち、
合わない要求を 401 にする。公開の URL に置くとき用。`.docs/aws-deploy.md`)。

## API

| メソッド | パス | 中身 |
| --- | --- | --- |
| GET | `/api/diaries?start_date=&end_date=` | 日本時間の日付(両端を含む)の日記を、コメント付きで時刻の順に(`ListDiaries`) |
| GET | `/api/diaries/{id}` | 日記一件(`ReadDiary`) |
| POST | `/api/diaries` | 日記を足す。`{"text", "time"?}`(`CommitDiary`) |
| GET | `/api/diaries/{id}/comments` | 日記一件のコメント(`ListComments`) |
| GET | `/api/comments/{id}` | コメント一件(`ReadComment`) |
| POST | `/api/comments` | コメントを足す。`{"diary_id", "text", "time"?}`(`CommitComment`) |
| POST | `/api/csv/{diary\|comment}` | CSV を取り込む。`{"text": CSV の中身}`。`{"added", "skipped"}` を返す |
| GET | `/api/csv/{diary\|comment}` | 取り込み直せる形の CSV(`text/csv`、ダウンロード) |
| POST | `/api/legacy-db/summary` | 以前の SQLite の db ファイル(本文にそのまま。`application/octet-stream`)の、人ごとの件数(`SummarizeLegacyDb`) |
| POST | `/api/legacy-db/import?source_user_id=` | 同じファイルから、`source_user_id` の日記とコメントを取り込む(`ImportLegacyDb`) |
| GET | `/api/health` | db の種類(`{"dialect": "postgresql"}`) |
| GET | `/api/ping` | 起きているかだけ(`DIARY_API_KEYS` があっても合言葉なしで通す) |

`/api/ping` と `/api/health` 以外は `x-diary-user` が要る(無ければ 401)。他の人の日記・コメントは 404。

型を変えたら OpenAPI と TS の型を作り直す。

```
.venv/bin/python -m gui.api.dump_openapi
(cd gui/web && npm run types)
```

## 型と lint

```
(cd gui/web && npm run typecheck && npm run lint)
```
