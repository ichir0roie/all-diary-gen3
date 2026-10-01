from data_access_logic.material import JstTime, Material


class CommentRecord(Material):
    id: int
    diary_id: int
    time: JstTime
    text: str


class DeletedComment(Material):
    id: int
    diary_id: int
