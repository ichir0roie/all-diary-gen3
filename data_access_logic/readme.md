db を読み書きする処理と、それを呼ぶ入口を置く場所。claude と API は、どちらもここの処理を使う。
**claude が db を触る操作の前にこの readme を引く。**

入口は `<領域>/<動詞_対象>.py` に一つずつ置いたクラス。同じ入口を、呼ぶ側が次のように使い分ける。

- claude が CLI から: インスタンス化して `show()` を呼ぶ。結果を JSON で print する
  (CLI 引数のパースはしない。`if __name__ == "__main__"` も置かない)
- 結果を同じ python の中で続けて使う: print せずに返す `run()` を呼ぶ
- API: 自分の開いたセッションで `execute(s)` を呼び、レスポンスのモデルをそのまま使う

    from data_access_logic.diary.list_diaries import ListDiaries
    ListDiaries("<ユーザーの sub>", start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)).show()

db の触り方(入口越し・読み取り)は `.claude/docs/db.md` を見る。ユーザが書いて読む窓口は `gui/`。

## 誰の行か

日記・コメントは人ごとの行。どの入口も最初の引数に `user_id`(Cognito のユーザーの sub)を取り、その人の行だけを読み書きする。
他の人の行は、無い行と同じに扱う(`UnknownRecordError`。API では 404)。API では、画面の route handler が確かめた人を
`x-diary-user` で渡す(`gui/api/user.py`)。

## 引数とレスポンス

行の中身を渡す引数は、dict や JSON の文字列ではなく pydantic のモデルで渡す。モデルは領域ごとの
`data_access_logic/<領域>/form.py` にあり、スキーマに無い欄が混ざっていたらそこで止まる(`extra="forbid"`)。

    from data_access_logic.diary.commit_diary import CommitDiary
    from data_access_logic.diary.form import DiaryCreateForm
    CommitDiary("<ユーザーの sub>", DiaryCreateForm(text="今日は…", time="2026-10-01 21:00")).show()

| 入口 | 引数のモデル |
| --- | --- |
| `CommitDiary` | `diary.form.DiaryCreateForm` |
| `UpdateDiary` | `diary.form.DiaryUpdateForm` |
| `SendFutureDiary` | `diary.form.FutureDiaryCreateForm` |
| `CommitComment` | `comment.form.CommentCreateForm` |
| `UpdateComment` | `comment.form.CommentUpdateForm` |

(モジュールはどれも `data_access_logic.` を頭に付ける)

`run()` は、入口が組んだレスポンスのモデルを `model_dump(mode="json")` した dict(一覧はそのリスト)を返す。
時刻は日本時間の `"2026-10-01T21:00:00+09:00"` の文字列になる。入口に渡す時刻は、時差の無いもの(`"2026-10-01 21:00"`)なら日本時間として読む。
レスポンスのモデルは、行を写したものが `data_access_logic/<領域>/record.py`(`*Record` など)にある。

## 依頼内容 → 呼ぶコード

`data_access_logic.` を頭に付けて import する。

| 依頼内容(言い回しの例) | 呼ぶコード |
| --- | --- |
| 「この期間の日記」「先週の日記を見せて」 | `diary.list_diaries.ListDiaries(user_id, start_date=None, end_date=None)`。日本時間の日付で、両端を含む。コメント付きで時刻の順に返す。省いた端は限らない |
| 「この日記を見せて」 | `diary.read_diary.ReadDiary(user_id, diary_id)`。コメント付き |
| 「日記を書いて」「日記を足して」 | `diary.commit_diary.CommitDiary(user_id, DiaryCreateForm(text=…, time=None))`。`time` を省けば今の時刻 |
| 「この日記を書き直して」 | `diary.update_diary.UpdateDiary(user_id, diary_id, DiaryUpdateForm(text=…))`。本文だけを変え、時刻は変えない |
| 「この日記を消して」 | `diary.delete_diary.DeleteDiary(user_id, diary_id)`。付いたコメントごと消す。`{"id", "comments": 消したコメントの数}` を返す |
| 「未来の自分へ日記を送って」 | `diary.send_future_diary.SendFutureDiary(user_id, FutureDiaryCreateForm(text=…, deliver_on=date(…)))`。`deliver_on`(明日より後)の日本時間 0 時を `time` に、今を `written_at` に入れる。届くまでは封をし、どの入口も読まない・書き直さない・コメントを足さない(`common_query.delivered` / `own_diary`) |
| 「まだ届いていない日記は?」 | `diary.list_future_diaries.ListFutureDiaries(user_id)`。届く時刻と書いた時刻だけ(本文は返さない) |
| 「◯年前の今日の日記」「毎年のこの日」 | `diary.list_on_this_day.ListOnThisDay(user_id, day, around_days=0)`。`day` と同じ月日の前後 `around_days` 日(30 まで)の日記を、書き始めた年から `day` の年まで、新しい年から年ごとに返す。日記の無い年も空で返す。2 月 29 日はうるう年でない年では 2 月 28 日 |
| 「日ごとに何件書いた?」 | `diary.count_diaries_by_day.CountDiariesByDay(user_id, start_date=None, end_date=None)`。日本時間の暦の日ごとの件数と文字数。書いた日だけ。本文は返さない |
| 「この日記に似た日記」 | `diary.list_similar_diaries.ListSimilarDiaries(user_id, diary_id, limit=50)`。その日記の本文で `SearchSimilarDiaries` を回し、元の日記は除く。他の人の日記・まだ届いていない日記は `UnknownRecordError` |
| 「この文章に似た日記」 | `diary.search_similar_diaries.SearchSimilarDiaries(user_id, text, limit=50, exclude_diary_id=None)`。文章を二文字の組に切り(ひらがなだけの組・句読点をまたぐ組は捨てる)、その人の日記にどれだけ出るかで重みを付けて、重みの 3 割以上が出てくる日記を似ているとする。`{"total", "diaries": [{"score", "diary"}]}` を似ている順に返す |
| 「この日記のコメント」 | `comment.list_comments.ListComments(user_id, diary_id)` |
| 「このコメントを見せて」 | `comment.read_comment.ReadComment(user_id, comment_id)` |
| 「このコメントを書き直して」 | `comment.update_comment.UpdateComment(user_id, comment_id, CommentUpdateForm(text=…))`。時刻は変えない |
| 「このコメントを消して」 | `comment.delete_comment.DeleteComment(user_id, comment_id)` |
| 「この日記にコメントして」 | `comment.commit_comment.CommitComment(user_id, CommentCreateForm(diary_id=…, text=…, time=None))`。自分の日記にだけ足せる |
| 「日記の CSV を取り込んで」「前の db から移して」 | `csv_file.import_diary_csv.ImportDiaryCsv(user_id, csv_text)`。列は `id,text,time`、未来へ送った日記は `written_at` も(以前の CSV の `user_id` の列は読まない)。時刻は `2021-01-02 09:00:00.000000` のような日本時間か、時差付きの ISO 8601。CSV の `id` は `migration_id` に残す。時刻と本文が同じ日記は、CSV の中では先の行を取り、db に既にあれば足さない(取り込み直しても重ならない)。`{"added", "skipped"}` を返す |
| 「コメントの CSV を取り込んで」 | `csv_file.import_comment_csv.ImportCommentCsv(user_id, csv_text)`。列は `id,diary_id,text,time`。`diary_id` は日記の CSV の `id` で、先に取り込んだ日記(`migration_id`)を指す。指す日記が無ければ一件も足さずに止まる |
| 「以前の db ファイルに誰の日記が入っている?」 | `legacy_db.summarize_legacy_db.SummarizeLegacyDb(sqlite_bytes)`。以前の API の SQLite の db ファイル(`open(path, "rb").read()`)の、人(以前の Cognito のユーザーの sub)ごとの日記・コメントの件数と期間。db(RDS)には触れない |
| 「以前の db ファイルから取り込んで」「旧環境の最新を移して」 | `legacy_db.import_legacy_db.ImportLegacyDb(user_id, sqlite_bytes, source_user_id)`。`source_user_id` の日記と、その日記へのコメントを `user_id` の人の行として足す。以前の id は `migration_id` に残す。時刻と本文が同じ日記・コメントが既にあれば足さないので、新しい db ファイルで取り込み直せば増えた分だけが入る。`{"diaries": {"added", "skipped"}, "comments": {…}}` を返す |
| 「日記を CSV に書き出して」 | `csv_file.export_diary_csv.ExportDiaryCsv(user_id)`。`ImportDiaryCsv` で取り込み直せる形(`id,text,time,written_at`。まだ届いていない日記も、封をしたまま書き出す)。`{"text", "rows"}` を返す |
| 「コメントを CSV に書き出して」 | `csv_file.export_comment_csv.ExportCommentCsv(user_id)`。`diary_id` は日記の id(`ExportDiaryCsv` の `id`) |

## 入口の作り方

- 置き場所は `data_access_logic/<領域>/<動詞_対象>.py`。クラス名は動詞と対象(`CommitDiary`)
- 読むだけなら `entrypoint.SessionEntrypoint`、書くなら `entrypoint.CommitEntrypoint` を継ぎ、`execute(s)` を書く。
  `CommitEntrypoint` の `execute` は入口のトランザクションの中で走るので、中で commit しない
- 引数の型・レスポンスのモデル・リレーションの読み方は `.claude/docs/data-access.md`
- API から呼ぶなら `gui/api/app.py` にエンドポイントを足し、`.venv/bin/python -m gui.api.dump_openapi` と
  `(cd gui/web && npm run types)` で画面の型を作り直す
- 足したら、上の対応表に行を足し、`tests/claude_interface/` にテストを足す
