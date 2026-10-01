from pydantic import BaseModel


class Imported(BaseModel):
    added: int
    # 同じ時刻の行が取り込むものの中か db に既にあって、足さなかった行の数(同じものを取り込み直しても重ならない)
    skipped: int


class CsvDump(BaseModel):
    text: str
    rows: int
