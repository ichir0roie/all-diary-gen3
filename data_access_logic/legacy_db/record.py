from pydantic import BaseModel

from data_access_logic.csv_file.record import Imported
from data_access_logic.material import JstTime


class LegacyUser(BaseModel):
    """以前の db に日記を持つ人一人ぶん。`user_id` は以前の Cognito のユーザーの sub。"""

    user_id: str
    diaries: int
    comments: int
    first_time: JstTime
    last_time: JstTime


class LegacyDbSummary(BaseModel):
    users: list[LegacyUser]
    # どの日記にも結び付かず、取り込めないコメントの数
    unlinked_comments: int


class LegacyImported(BaseModel):
    diaries: Imported
    comments: Imported
