from pydantic import Field

from data_access_logic.material import Form, JstTime


class CommentCreateForm(Form):
    diary_id: int
    text: str = Field(min_length=1)
    # 省けば書き込んだ時刻
    time: JstTime | None = None
