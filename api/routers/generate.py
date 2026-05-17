from datetime import date
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import Response

from models.schema import ExtractionResult
from services.xlsx_builder import build_xlsx
from services.pdf_filler import build_pdf

router = APIRouter(prefix="/api", tags=["generate"])


def _make_filename(corp_name: str, ext: str) -> str:
    today = date.today().strftime("%Y%m%d")
    return f"事前確定届出書_{corp_name}_{today}.{ext}"


@router.post("/generate/xlsx")
async def generate_xlsx(data: ExtractionResult):
    """構造化データから Excel ファイルを生成"""
    xlsx_bytes = build_xlsx(data)
    filename = _make_filename(data.corporation.name, "xlsx")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        },
    )


@router.post("/generate/pdf")
async def generate_pdf(data: ExtractionResult):
    """構造化データから PDF ファイルを生成（テンプレート重ね合わせ）"""
    pdf_bytes = build_pdf(data)
    filename = _make_filename(data.corporation.name, "pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        },
    )
