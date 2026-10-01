from datetime import date

from pydantic import Field

from data_access_logic.material import Form, JstTime


class DiaryCreateForm(Form):
    text: str = Field(min_length=1)
    # 省けば書き込んだ時刻
    time: JstTime | None = None


class DiaryUpdateForm(Form):
    text: str = Field(min_length=1)


class FutureDiaryCreateForm(Form):
    text: str = Field(min_length=1)
    # 届ける日(日本時間)。その日の 0 時に届く。明日より前は選べない
    deliver_on: date
