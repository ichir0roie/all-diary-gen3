#!/usr/bin/env python3
"""開発用の db(`diary_dev`)に、作り物の日記とコメントを入れる。リポジトリのルートから:

    .venv/bin/python -m tool.dev.mock_data                 # 今の前後 10 年に日記 3000 件
    .venv/bin/python -m tool.dev.mock_data --count 500 --seed 1

時刻は今の前後 `--years` 年から一様に選ぶ。書く人は `--user`(既定は画面がログインなしで流す `DIARY_LOCAL_USER_ID`、無ければ `local`)。
その人の行は、入れる前に消して入れ直す。
"""
from tool.dev import DEV_DATABASE_URL  # db を開発用の db に固定する(schema より先に読む)

import argparse  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402

from sqlalchemy import delete  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from data_access_logic.constants import JST  # noqa: E402
from data_access_logic.logs import configure_logging  # noqa: E402
from db.schema import Comment, Diary, get_env_session  # noqa: E402

logger = logging.getLogger("tool.dev.mock_data")

OPENINGS = ["朝は雨だった。", "よく晴れた。", "風が強かった。", "少し寝坊した。", "早起きできた。", "一日中くもり。"]
EVENTS = [
    "駅前の本屋で文庫本を二冊買った。", "昼はうどんにした。", "散歩の途中で猫を見かけた。", "部屋の片付けを少し進めた。",
    "友人と電話で一時間ほど話した。", "仕事の資料を作り直した。", "夕方に買い物へ出た。", "新しい曲を何度も聴いた。",
    "カレーを作りすぎた。", "自転車のタイヤに空気を入れた。", "図書館で調べものをした。", "映画を一本観た。",
]
THOUGHTS = [
    "明日はもう少し早く寝たい。", "なんとなく落ち着かない一日だった。", "悪くない日だったと思う。", "次の休みは遠出したい。",
    "やることを書き出したら気が楽になった。", "季節が変わってきた気がする。",
]
COMMENTS = ["読み返すと懐かしい。", "この頃は忙しかった。", "結局どうなったんだっけ。", "いい日だ。", "続きを書くこと。"]


def diary_text(rng: random.Random) -> str:
    # 画面の折り返し・改行も試せるよう、短い一文から数段落まで長さを散らす
    paragraphs = []
    for _ in range(rng.choice([1, 1, 1, 2, 3])):
        sentences = [rng.choice(OPENINGS)] if not paragraphs else []
        sentences += rng.sample(EVENTS, rng.randint(1, 4))
        if rng.random() < 0.5:
            sentences.append(rng.choice(THOUGHTS))
        paragraphs.append("".join(sentences))
    return "\n\n".join(paragraphs)


def mock_rows(user_id: str, count: int, years: int, rng: random.Random) -> list[tuple[Diary, list[Comment]]]:
    """日記と、その日記へのコメント(日記の id が決まってから `diary_id` を入れる)の組。"""
    now = datetime.now(JST)
    span = timedelta(days=365 * years)
    rows = []
    for _ in range(count):
        time = (now - span + timedelta(seconds=rng.uniform(0, 2 * span.total_seconds()))).replace(microsecond=0)
        diary = Diary(user_id=user_id, time=time, text=diary_text(rng))
        comment_count = rng.randint(1, 2) if rng.random() < 0.3 else 0
        comments = [Comment(user_id=user_id, time=time + timedelta(minutes=rng.randint(1, 60 * 24 * 400)), text=rng.choice(COMMENTS))
                    for _ in range(comment_count)]
        rows.append((diary, comments))
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--user", default=os.environ.get("DIARY_LOCAL_USER_ID", "local"))
    parser.add_argument("--count", type=int, default=3000, help="日記の件数")
    parser.add_argument("--years", type=int, default=10, help="今の前後何年に散らすか")
    parser.add_argument("--seed", type=int, help="乱数の種。同じ種なら同じ本文と時刻の並び(基準の今は変わる)")
    args = parser.parse_args(argv)
    configure_logging()

    rng = random.Random(args.seed)
    rows = mock_rows(args.user, args.count, args.years, rng)
    with get_env_session() as s, s.begin():
        s.execute(delete(Comment).where(Comment.user_id == args.user))
        s.execute(delete(Diary).where(Diary.user_id == args.user))
        s.add_all([diary for diary, _ in rows])
        s.flush()
        for diary, comments in rows:
            for comment in comments:
                comment.diary_id = diary.id
            s.add_all(comments)
    comment_count = sum(len(comments) for _, comments in rows)
    logger.info(f"{make_url(DEV_DATABASE_URL).database} の {args.user} に、日記 {len(rows)} 件とコメント {comment_count} 件を入れた")


if __name__ == "__main__":
    main()
