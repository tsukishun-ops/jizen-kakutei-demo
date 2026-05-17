from fastapi import APIRouter

from models.schema import ExtractRequest, ExtractResponse
from services.claude_extractor import extract_from_memo

router = APIRouter(prefix="/api", tags=["extract"])


@router.post("/extract", response_model=ExtractResponse)
async def extract_data(req: ExtractRequest):
    """決議メモと役員マスタからClaude APIで構造化データを抽出する"""
    result = extract_from_memo(req.memo, req.yakuin_master)
    return ExtractResponse(**result)
