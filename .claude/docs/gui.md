# GUI

`gui/` の GUI(API :8766 / 画面 :3001)は、ユーザが日記を書いて読む窓口。起動・停止はユーザが任意で行う
(`gui/readme.md` の「起動」)。Claude は、テスト・動作確認で GUI が要るときだけ起こす。
作業の区切りに GUI が動いているかを確かめたり、落ちているのを立て直したりはしない。

- テストで起こすサーバーは、ユーザの使うポート(8766 / 3001)と別のポートにする。`gui.dev` は指定したポートを
  使っている処理を止めてから起こすので、同じポートだとユーザの GUI を落とす。ai-novel-core の GUI(8765 / 3000)のポートも使わない
- 画面を起こすときは、ビルド先も `.next-test` に分ける(`DIARY_WEB_DIST_DIR`)。`next dev` はビルド先ごとに 1 つしか
  動かせず、同じビルド先だとユーザの `gui.dev` と片方が起動に失敗する
  - API と画面: `DIARY_WEB_DIST_DIR=.next-test .venv/bin/python -m gui.dev --no-browser --api-port 18766 --web-port 13001`
  - API だけで足りるとき: `.venv/bin/python -m uvicorn gui.api.app:app --port 18766`
- 画面は `http://localhost:13001` で開く。`127.0.0.1` で開くと、`next dev` が別のオリジンからの開発用の読み込み(`/_next/*`)を
  弾き、画面が動かない(読み込み中のまま)
- 裏で起こし(`run_in_background`)、使い終わったら `kill -TERM` で止め、18766 / 13001 が閉じたことを `ss -ltn` で確かめる
- 起こした API は、渡した `DIARY_DATABASE_URL` の db を読み書きする(ふだんは本番の RDS)。テスト・動作確認は本番の日記を使わず、
  手元の開発用の db に向けて起こす。行が要るなら、先に `.venv/bin/python -m tool.dev.mock_data` で作り物の日記とコメントを入れる。
  ログインを掛けない手元では、画面の route handler が `DIARY_LOCAL_USER_ID`(既定 `local`)の人として流す:
  `DIARY_DATABASE_URL=${DIARY_DEV_DATABASE_URL:-$(infra_local/postgres.sh .venv/bin/python)} DIARY_DATABASE_IAM_AUTH=0 DIARY_WEB_DIST_DIR=.next-test .venv/bin/python -m gui.dev --no-browser --api-port 18766 --web-port 13001`
