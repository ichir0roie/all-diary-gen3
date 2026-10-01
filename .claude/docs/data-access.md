# db の読み取り(pydantic)

`data_access_logic/diary/` がこの形の見本。既存の処理を直すときも、この形へ寄せる。

- 既存の処理をなぞらず、その処理に要るものからゼロベースで組む。引数名は何の値・何の範囲かが分かる具体的な名前にする
  (`start` ではなく `start_date`)。理由の言えない構文(キーワード専用の `*` など)は付けない
- 入口は、誰の行かを `user_id: str` で最初の引数に受ける。行の中身(フォーム)には `user_id` を入れない(API では、画面の route handler が
  確かめた人を `x-diary-user` で渡し、本文の JSON には入れさせない)
- select の結果は pydantic のモデル(マテリアル。基底は `data_access_logic/material.py` の `Material`)に、ORM のままを渡して詰める。
  型チェッカーの `reportArgumentType` はプロジェクト設定(`pyrightconfig.json`)で切ってあるので、`Model(diary=diary_row)` のように渡してよい
- マテリアルは ORM の列とリレーションに忠実に写す。リレーションは同じ名前のフィールドに、関係先のモデルを入れ子にして持つ
  (`AliasPath` などで平らにしない)
- リレーションは `lazy="raise"` で定義し、要るものだけを `selectinload` で読み、`execution_options(populate_existing=True)` を付ける
  (同じセッションに行が残っていると eager load が効かない)。読むものはマテリアルの `LOAD_OPTIONS` に書き、`entrypoint.loading` /
  `entrypoint.record_of` で読む。`execute` はなるべく使わず `scalars` / `scalar` で ORM を取る
- 時刻の欄は `JstTime`(日本時間にそろえ、JSON では `+09:00` 付きの ISO 8601)
- dict の `.get` や文字列キーでの取り出しは極力使わない。境目(CSV の行など)でモデルに読み込んでから属性で扱う
- dict への変換と二重の変換は残さない。関数は最初からモデルを返し(呼ぶ側で `model_validate` し直さない)、フォームは ORM の行へ属性で書く
  (`Form.write_to`。`Model(**form.model_dump())` にしない)。dict にするのは API・CLI へ返す最後の `model_dump(mode="json")` だけ
- 入口(`data_access_logic/<領域>/<動詞_対象>.py`。claude は `show()`、API は `execute(s)` を呼ぶ)の引数は、`str | dict` にせず pydantic のモデル
  (`data_access_logic/<領域>/form.py`)で受ける。レスポンスもモデル(`data_access_logic/<領域>/record.py`)で組み、
  `run()` が `model_dump(mode="json")` した結果を返す。すべての引数に型を書く
- 確定(commit)の境目: db に書く入口は `CommitEntrypoint` を継ぎ、入口のトランザクション(`s.begin()`)に任せて中で commit しない。
  API も `with s.begin():` の中で `execute(s)` を呼ぶ
