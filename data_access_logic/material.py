from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer

from data_access_logic.constants import JST
from db.schema import Base


class Material(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # このモデルに詰めるのに要る、リレーション(`lazy="raise"`)の読み方(`entrypoint.record_of` / `entrypoint.loading` が使う)
    LOAD_OPTIONS: ClassVar[tuple] = ()


class Form(BaseModel):
    """入口の引数。スキーマに無い欄が混ざっていたら止める。"""

    model_config = ConfigDict(extra="forbid")

    def write_to(self, record: Base) -> None:
        """欄のうち `record` のテーブルの列に当たるものを書く。列でない欄は、呼ぶ側が別に書く。"""
        columns = type(record).__table__.columns
        for name, value in self:
            if name != "id" and name in columns:
                setattr(record, name, value)


def _in_jst(value: datetime) -> datetime:
    return value.replace(tzinfo=JST) if value.tzinfo is None else value.astimezone(JST)


# 時差の無い時刻は日本時間として読み、どの時刻も日本時間にそろえる。レスポンスでは `+09:00` 付きの ISO 8601 にする
JstTime = Annotated[datetime, AfterValidator(_in_jst), PlainSerializer(datetime.isoformat, return_type=str, when_used="json")]
