from typing import Optional

from fastapi import APIRouter, File, UploadFile

from services.csv_parser import parse_yakuin_master, parse_yayoi_journal, read_memo
from models.schema import ParseResponse, YakuinRecord, YayoiJournalRecord

router = APIRouter(prefix="/api", tags=["parse"])


@router.post("/parse", response_model=ParseResponse)
async def parse_files(
    yakuin_master: UploadFile = File(..., description="役員マスタCSV"),
    kessian_memo: Optional[UploadFile] = File(None, description="決議メモテキスト"),
    yayoi_journal: Optional[UploadFile] = File(None, description="弥生仕訳日記帳CSV"),
):
    """役員マスタCSV・決議メモ・弥生仕訳CSVをパースして構造化JSONで返す"""
    yakuin_bytes = await yakuin_master.read()
    yakuin_dicts = parse_yakuin_master(yakuin_bytes)
    yakuin_records = [YakuinRecord(**row) for row in yakuin_dicts]

    memo_text = None
    if kessian_memo is not None:
        memo_bytes = await kessian_memo.read()
        memo_text = read_memo(memo_bytes)

    yayoi_records = None
    if yayoi_journal is not None:
        yayoi_bytes = await yayoi_journal.read()
        yayoi_dicts = parse_yayoi_journal(yayoi_bytes)
        yayoi_records = [YayoiJournalRecord(**row) for row in yayoi_dicts]

    return ParseResponse(
        yakuin_master=yakuin_records,
        memo=memo_text,
        yayoi_journal=yayoi_records,
    )
