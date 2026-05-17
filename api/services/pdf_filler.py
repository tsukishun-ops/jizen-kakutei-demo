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

    # 税務署名（「○○税務署長 殿」の○○部分）
    _draw_text(c, 48, 211, corp.tax_office, 9)

    # 法人番号（ページ右上の番号欄）
    if corp.corporation_number:
        for i, ch in enumerate(corp.corporation_number):
            _draw_text(c, 140 + i * 4.8, 272, ch, 8)

    # 納税地（「納税地」ラベルの右、記入欄）
    postal = f"〒{corp.postal_code}" if corp.postal_code else ""
    _draw_text(c, 100, 257, f"{postal} {corp.address}", 8)

    # 電話番号（電話欄）
    if corp.phone:
        _draw_text(c, 135, 253, corp.phone, 8)

    # 法人名（「法人名」ラベルの右）
    _draw_text(c, 100, 241, corp.name, 9)

    # 法人名フリガナ
    if corp.name:
        _draw_text(c, 105, 248, "", 7)

    # 代表者名（「代表者氏名」ラベルの右）
    if corp.representative:
        _draw_text(c, 100, 218, corp.representative, 9)

    # 代表者住所
    if corp.representative:
        _draw_text(c, 100, 207, "", 8)

    # 提出日（左上「令和＿年＿月＿日」）
    from datetime import date as _date
    today = _date.today()
    _draw_text(c, 33, 240, str(today.year - 2018), 9)
    _draw_text(c, 45, 240, str(today.month), 9)
    _draw_text(c, 55, 240, str(today.day), 9)

    # ① 決議をした日（「決議をした日」欄の年月日記入位置）
    d = res.decision_date
    _draw_text(c, 113, 183, str(d.year - 2018), 8)
    _draw_text(c, 123, 183, str(d.month), 8)
    _draw_text(c, 133, 183, str(d.day), 8)

    # ① 決議をした機関
    _draw_text(c, 95, 178, res.decision_body, 8)

    # ② 職務執行開始日
    d2 = res.execution_start_date
    _draw_text(c, 113, 168, str(d2.year - 2018), 8)
    _draw_text(c, 123, 168, str(d2.month), 8)
    _draw_text(c, 133, 168, str(d2.day), 8)

    # ③ 臨時改定事由（概要）- 通常は空
    if res.fiscal_year_basis:
        d3 = res.fiscal_year_basis
        _draw_text(c, 113, 137, str(d3.year - 2018), 8)
        _draw_text(c, 123, 137, str(d3.month), 8)
        _draw_text(c, 133, 137, str(d3.day), 8)

    # ④ 付表No
    n_officers = len(data.officers)
    _draw_text(c, 100, 132, f"1 ～ No. {n_officers}", 8)

    # ⑤ 定期同額給与としない理由
    if res.reason_for_bonus_timing:
        _draw_text(c, 25, 108, res.reason_for_bonus_timing[:40], 7)
        if len(res.reason_for_bonus_timing) > 40:
            _draw_text(c, 25, 104, res.reason_for_bonus_timing[40:80], 7)

    c.showPage()
    c.save()
    return buf.getvalue()


def _create_futahyo_overlay(data: ExtractionResult) -> bytes:
    """付表1 PDF のオーバーレイを作成（1役員1ページ）"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    for idx, officer in enumerate(data.officers):
        if idx > 0:
            c.showPage()

        # No.（右上）
        _draw_text(c, 130, 277, str(idx + 1), 9)

        # 対象者の氏名（役職）
        _draw_text(c, 60, 270, f"{officer.name}（{officer.position}）", 9)

        # 職務執行開始日
        d = data.resolution.execution_start_date
        _draw_text(c, 125, 263, str(d.year - 2018), 8)
        _draw_text(c, 140, 263, str(d.month), 8)
        _draw_text(c, 152, 263, str(d.day), 8)

        # 事業年度
        if data.corporation.fiscal_year_start:
            fy = data.corporation.fiscal_year_start
            _draw_text(c, 100, 252, str(fy.year - 2018), 8)
            _draw_text(c, 112, 252, str(fy.month), 8)
            _draw_text(c, 122, 252, str(fy.day), 8)
        if data.corporation.fiscal_year_end:
            fe = data.corporation.fiscal_year_end
            _draw_text(c, 148, 252, str(fe.year - 2018), 8)
            _draw_text(c, 160, 252, str(fe.month), 8)
            _draw_text(c, 170, 252, str(fe.day), 8)

        # 届出額の表（各支給回）
        # 表のヘッダー位置: y≈238mm, 各行は約9mm間隔
        row_y_start = 230
        for j, payment in enumerate(officer.payments):
            ry = row_y_start - j * 9.5
            # 支給時期（年月日）
            pd = payment.payment_date
            _draw_text(c, 40, ry, str(pd.year - 2018), 7)
            _draw_text(c, 50, ry, str(pd.month), 7)
            _draw_text(c, 58, ry, str(pd.day), 7)
            # 届出額
            _draw_text(c, 75, ry, _format_amount(payment.amount), 8)
            # 届出額（右側も同額）
            _draw_text(c, 155, ry, _format_amount(payment.amount), 8)

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
