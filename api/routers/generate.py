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

    writer.writerow(["事前確定届出給与に関する届出書"])
    writer.writerow([])
    writer.writerow(["法人名", data.corporation.name])
    writer.writerow(["法人番号", data.corporation.corporation_number or ""])
    writer.writerow(["納税地", data.corporation.address])
    writer.writerow(["電話番号", data.corporation.phone or ""])
    writer.writerow(["代表者", data.corporation.representative or ""])
    writer.writerow(["所轄税務署", data.corporation.tax_office])
    writer.writerow(["事業年度開始", str(data.corporation.fiscal_year_start or "")])
    writer.writerow(["事業年度終了", str(data.corporation.fiscal_year_end or "")])
    writer.writerow(["資本金", data.corporation.capital or ""])
    writer.writerow([])
    writer.writerow(["決議日", str(data.resolution.decision_date)])
    writer.writerow(["決議機関", data.resolution.decision_body])
    writer.writerow(["職務執行開始日", str(data.resolution.execution_start_date)])
    writer.writerow(["届出期限区分", data.resolution.filing_deadline_basis or "イ"])
    writer.writerow(["理由", data.resolution.reason_for_bonus_timing or ""])
    writer.writerow([])
    writer.writerow(["氏名", "役職", "支給日", "支給額（円）", "定期同額給与月額（円）"])
    for officer in data.officers:
        for j, payment in enumerate(officer.payments):
            writer.writerow([
                officer.name if j == 0 else "",
                officer.position if j == 0 else "",
                str(payment.payment_date),
                payment.amount,
                officer.regular_payment if j == 0 else "",
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
