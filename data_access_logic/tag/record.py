from data_access_logic.material import Material


class TagRecord(Material):
    id: int
    name: str


class TagUsage(Material):
    """タグと、それを付けた日記・コメントの数。"""

    tag: TagRecord
    diaries: int
    comments: int


class DeletedTag(Material):
    id: int
    # タグを外した日記・コメントの数
    diaries: int
    comments: int
