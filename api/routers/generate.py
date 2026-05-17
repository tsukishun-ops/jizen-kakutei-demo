import csv
import io
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


@router.post("/generate/csv")
async def generate_csv(data: ExtractionResult):
    """構造化データから CSV ファイルを生成（Excel Online / Google Sheets 対応）"""
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([
        "法人名", "法人番号", "納税地", "電話番号", "代表者", "所轄税務署",
        "決議日", "決議機関", "届出���限区分",
        "氏名", "役職", "支給日", "支給額", "定期同額給与月額",
    ])
    for officer in data.officers:
        for j, payment in enumerate(officer.payments):
            writer.writerow([
                data.corporation.name if j == 0 else "",
                data.corporation.corporation_number or "" if j == 0 else "",
                data.corporation.address if j == 0 else "",
                data.corporation.phone or "" if j == 0 else "",
                data.corporation.representative or "" if j == 0 else "",
                data.corporation.tax_office if j == 0 else "",
                str(data.resolution.decision_date) if j == 0 else "",
                data.resolution.decision_body if j == 0 else "",
                data.resolution.filing_deadline_basis or "イ" if j == 0 else "",
                officer.name,
                officer.position,
                str(payment.payment_date),
                payment.amount,
                officer.regular_payment or "",
            ])

    csv_content = "\ufeff" + buf.getvalue()
    filename = _make_filename(data.corporation.name, "csv")
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        },
    )
