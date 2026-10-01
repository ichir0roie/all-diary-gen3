"""以前の API(`all_diary_backend`)の SQLite の db ファイルを、テストのために作る。"""
import os
import sqlite3
import tempfile

# 以前の API(all_diary_backend の module/db/db.py)が SQLite に作った表の形。module/db/db.py には一意の制約が書いてあるが、
# 実際の db の表には無く、同じ時刻の行が入っている
LEGACY_SCHEMA = """
CREATE TABLE diary (user_id VARCHAR(255) NOT NULL, id INTEGER NOT NULL, migration_id BIGINT,
    time TIMESTAMP DEFAULT (CURRENT_TIMESTAMP) NOT NULL, text VARCHAR(1024) NOT NULL, PRIMARY KEY (id));
CREATE TABLE comment (user_id VARCHAR(255) NOT NULL, id INTEGER NOT NULL, migration_id BIGINT,
    time TIMESTAMP DEFAULT (CURRENT_TIMESTAMP) NOT NULL, text VARCHAR(1024) NOT NULL, diary_id BIGINT,
    PRIMARY KEY (id), FOREIGN KEY(diary_id) REFERENCES diary (id));
CREATE TABLE count (id INTEGER NOT NULL, time TIMESTAMP DEFAULT (CURRENT_TIMESTAMP) NOT NULL, PRIMARY KEY (id));
"""


def legacy_db(diaries: list[tuple], comments: list[tuple]) -> bytes:
    """`diaries` は (id, user_id, time, text)、`comments` は (id, user_id, diary_id, time, text)。"""
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "sqlite.db")
        conn = sqlite3.connect(path)
        conn.executescript(LEGACY_SCHEMA)
        conn.executemany("INSERT INTO diary (id, user_id, time, text) VALUES (?, ?, ?, ?)", diaries)
        conn.executemany("INSERT INTO comment (id, user_id, diary_id, time, text) VALUES (?, ?, ?, ?, ?)", comments)
        conn.commit()
        conn.close()
        with open(path, "rb") as f:
            return f.read()


OLD_ME = "old-sub-me"
OLD_OTHER = "old-sub-other"
# 続けて書いて同じ時刻になった日記(2 と 5)・コメント(1 と 4)を含む
LEGACY_DIARIES = [
    (1, OLD_ME, "2026-03-01 21:00:00.000000", "三月一日"), (2, OLD_ME, "2026-09-30 22:30:15.123000", "九月末"),
    (3, OLD_OTHER, "2026-03-01 21:00:00.000000", "別の人"), (5, OLD_ME, "2026-09-30 22:30:15.123000", "九月末の続き")]
LEGACY_COMMENTS = [
    (1, OLD_ME, 1, "2026-03-02 08:00:00.000000", "翌朝のコメント"), (2, OLD_OTHER, 3, "2026-03-02 09:00:00.000000", "別の人へ"),
    (4, OLD_ME, 1, "2026-03-02 08:00:00.000000", "翌朝のコメントの続き"),
    # 以前の CSV の取り込み(pandas)は diary_id を 8 バイトのバイナリで書いた。8 は無い日記を指す
    (8, OLD_ME, (2).to_bytes(8, "little"), "2026-10-01 06:00:00.000000", "バイナリの diary_id"),
    (9, OLD_ME, (8).to_bytes(8, "little"), "2026-10-01 06:30:00.000000", "結び付かないコメント")]
LEGACY = legacy_db(LEGACY_DIARIES, LEGACY_COMMENTS)
