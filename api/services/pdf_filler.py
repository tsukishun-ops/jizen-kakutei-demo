import io
import os
from datetime import date

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

from models.schema import ExtractionResult

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

FONT_NAME = "HeiseiKakuGo-W5"
PAGE_W, PAGE_H = A4

_LOCAL_SAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "samples")
_DOCKER_SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")
SAMPLES_DIR = _LOCAL_SAMPLES if os.path.isdir(_LOCAL_SAMPLES) else _DOCKER_SAMPLES


def _format_date_wareki(d: date | None) -> str:
    if d is None:
        return ""
    return f"令和{d.year - 2018}年{d.month}月{d.day}日"


def _format_amount(amount: int | None) -> str:
    if amount is None:
        return ""
    return f"{amount:,}"


def _draw_text(c: canvas.Canvas, x_mm: float, y_mm: float, text: str, size: float = 8):
    """左下原点(mm)でテキストを描画"""
    c.setFont(FONT_NAME, size)
    c.drawString(x_mm * mm, y_mm * mm, text)


def _create_honpyo_overlay(data: ExtractionResult) -> bytes:
    """本表PDF（1ページ目）のオーバーレイを作成"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    corp = data.corporation
    res = data.resolution

    # 税務署名
    _draw_text(c, 30, 262, corp.tax_office, 10)

    # 法人番号
    if corp.corporation_number:
        for i, ch in enumerate(corp.corporation_number):
            _draw_text(c, 125 + i * 5.5, 248, ch, 9)

    # 法人名
    _draw_text(c, 55, 237, corp.name, 10)

    # 納税地
    postal = f"〒{corp.postal_code}" if corp.postal_code else ""
    _draw_text(c, 55, 228, f"{postal} {corp.address}", 8)

    # 電話番号
    if corp.phone:
        _draw_text(c, 150, 228, corp.phone, 8)

    # 代表者氏名
    if corp.representative:
        _draw_text(c, 55, 218, corp.representative, 9)

    # 事業年度
    if corp.fiscal_year_start:
        _draw_text(c, 55, 207, f"{_format_date_wareki(corp.fiscal_year_start)} ～ {_format_date_wareki(corp.fiscal_year_end)}", 8)

    # 資本金
    if corp.capital:
        _draw_text(c, 150, 207, f"{_format_amount(corp.capital)}円", 8)

    # ① 決議をした日
    _draw_text(c, 55, 185, _format_date_wareki(res.decision_date), 8)

    # ① 決議をした機関
    _draw_text(c, 130, 185, res.decision_body, 8)

    # ② 職務執行開始日
    _draw_text(c, 55, 175, _format_date_wareki(res.execution_start_date), 8)

    # ③ 当該事業年度開始の日
    if res.fiscal_year_basis:
        _draw_text(c, 55, 165, _format_date_wareki(res.fiscal_year_basis), 8)

    # 届出期限区分
    basis = res.filing_deadline_basis or "イ"
    _draw_text(c, 150, 165, basis, 9)

    # ④ 役員概要
    y_start = 140
    for i, officer in enumerate(data.officers):
        y = y_start - i * 8
        _draw_text(c, 20, y, officer.name, 7)
        _draw_text(c, 55, y, officer.position, 7)
        for j, payment in enumerate(officer.payments):
            _draw_text(c, 90, y - j * 5, _format_date_wareki(payment.payment_date), 7)
            _draw_text(c, 140, y - j * 5, f"{_format_amount(payment.amount)}円", 7)
        if officer.regular_payment:
            _draw_text(c, 170, y, f"月額{_format_amount(officer.regular_payment)}円", 7)

    # ⑤ 定期同額給与としない理由
    if res.reason_for_bonus_timing:
        _draw_text(c, 20, 95, res.reason_for_bonus_timing, 7)

    c.showPage()
    c.save()
    return buf.getvalue()


def _create_futahyo_overlay(data: ExtractionResult) -> bytes:
    """付表1 PDF のオーバーレイを作成"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # 法人名
    _draw_text(c, 55, 262, data.corporation.name, 9)

    y_start = 235
    for idx, officer in enumerate(data.officers):
        y = y_start - idx * 60

        if y < 40:
            c.showPage()
            _draw_text(c, 55, 275, data.corporation.name, 9)
            y = 250

        # 氏名
        _draw_text(c, 20, y, officer.name, 8)
        # 役職
        _draw_text(c, 65, y, officer.position, 8)
        # フリガナ
        if officer.name_kana:
            _draw_text(c, 20, y + 5, officer.name_kana, 6)
        # 就任年月日
        if officer.appointment_date:
            _draw_text(c, 110, y, _format_date_wareki(officer.appointment_date), 7)
        # 区分
        _draw_text(c, 160, y, officer.category or "事前確定届出給与", 6)

        # 支給明細
        for j, payment in enumerate(officer.payments):
            py = y - 12 - j * 8
            _draw_text(c, 30, py, _format_date_wareki(payment.payment_date), 7)
            _draw_text(c, 85, py, f"{_format_amount(payment.amount)}円", 7)
            if payment.memo:
                _draw_text(c, 130, py, payment.memo, 6)

        # 定期同額給与
        if officer.regular_payment:
            ry = y - 12 - len(officer.payments) * 8 - 5
            _draw_text(c, 30, ry, f"定期同額給与（月額）: {_format_amount(officer.regular_payment)}円", 7)

    c.showPage()
    c.save()
    return buf.getvalue()


def _merge_overlay(template_path: str, overlay_bytes: bytes) -> PdfWriter:
    """テンプレートPDFにオーバーレイを重ね合わせる"""
    template_reader = PdfReader(template_path)
    overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
    writer = PdfWriter()

    for i, page in enumerate(template_reader.pages):
        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])
        writer.add_page(page)

    return writer


def build_pdf(data: ExtractionResult) -> bytes:
    """ExtractionResult から PDF バイナリを生成（テンプレート重ね合わせ方式）"""
    honpyo_path = os.path.join(SAMPLES_DIR, "honpyo_template.pdf")
    futahyo_path = os.path.join(SAMPLES_DIR, "futahyo1_template.pdf")

    writer = PdfWriter()

    # 本表
    if os.path.exists(honpyo_path):
        honpyo_overlay = _create_honpyo_overlay(data)
        honpyo_writer = _merge_overlay(honpyo_path, honpyo_overlay)
        for page in honpyo_writer.pages:
            writer.add_page(page)

    # 付表1
    if os.path.exists(futahyo_path):
        futahyo_overlay = _create_futahyo_overlay(data)
        futahyo_writer = _merge_overlay(futahyo_path, futahyo_overlay)
        for page in futahyo_writer.pages:
            writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
