from typing import Annotated

from pydantic import StringConstraints

from data_access_logic.material import Form

# 前後の空白を落としてから比べる(「 旅行」と「旅行」を別のタグにしない)
TagName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TagCreateForm(Form):
    name: TagName


class TagUpdateForm(Form):
    name: TagName


class TagChoiceForm(Form):
    """日記・コメントに付けるタグ。"""

    # None ならタグを外す
    tag_id: int | None
