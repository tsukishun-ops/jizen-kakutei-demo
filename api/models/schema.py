from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class YakuinRecord(BaseModel):
    """役員マスタCSVの1行を表すモデル"""

    yakuin_id: str = Field(..., alias="役員ID")
    name_kana: str = Field(..., alias="氏名フリガナ")
    name: str = Field(..., alias="氏名")
    position: str = Field(..., alias="役職")
    appointment_date: date = Field(..., alias="就任年月日")
    birth_date: date = Field(..., alias="生年月日")
    address: str = Field(..., alias="住所")
    department: str = Field(..., alias="所属部門")

    model_config = {"populate_by_name": True}


class YayoiJournalRecord(BaseModel):
    """弥生仕訳日記帳CSVの1行を表すモデル"""

    identifier: str = Field(..., alias="識別フラグ")
    slip_no: str = Field(..., alias="伝票No")
    settlement: Optional[str] = Field(None, alias="決算")
    transaction_date: date = Field(..., alias="取引日付")
    debit_account: str = Field(..., alias="借方勘定科目")
    debit_sub_account: Optional[str] = Field(None, alias="借方補助科目")
    debit_department: Optional[str] = Field(None, alias="借方部門")
    debit_tax_category: Optional[str] = Field(None, alias="借方税区分")
    debit_amount: int = Field(..., alias="借方金額")
    debit_tax_amount: int = Field(0, alias="借方税金額")
    credit_account: str = Field(..., alias="貸方勘定科目")
    credit_sub_account: Optional[str] = Field(None, alias="貸方補助科目")
    credit_department: Optional[str] = Field(None, alias="貸方部門")
    credit_tax_category: Optional[str] = Field(None, alias="貸方税区分")
    credit_amount: int = Field(..., alias="貸方金額")
    credit_tax_amount: int = Field(0, alias="貸方税金額")
    summary: Optional[str] = Field(None, alias="摘要")

    model_config = {"populate_by_name": True}


class ParseResponse(BaseModel):
    """POST /api/parse のレスポンス"""

    yakuin_master: list[YakuinRecord]
    memo: Optional[str] = None
    yayoi_journal: Optional[list[YayoiJournalRecord]] = None


# --- extraction_schema.json 準拠モデル ---


class Corporation(BaseModel):
    """法人基本情報（本表の上部）"""

    name: str
    corporation_number: Optional[str] = None
    postal_code: Optional[str] = None
    address: str
    phone: Optional[str] = None
    representative: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    capital: Optional[int] = None
    tax_office: str


class Resolution(BaseModel):
    """株主総会等の決議情報（本表 1〜3）"""

    decision_date: date
    decision_body: Literal[
        "定時株主総会", "臨時株主総会", "取締役会", "報酬委員会", "社員総会", "その他"
    ]
    execution_start_date: date
    fiscal_year_basis: Optional[date] = None
    filing_deadline_basis: Optional[Literal["イ", "ロ", "ハ"]] = None
    reason_for_bonus_timing: Optional[str] = None
    remarks: Optional[str] = None


class Payment(BaseModel):
    """支給予定の1回分"""

    payment_date: date
    amount: int
    memo: Optional[str] = None


class Officer(BaseModel):
    """事前確定届出給与の対象役員"""

    name: str
    name_kana: Optional[str] = None
    position: str
    appointment_date: Optional[date] = None
    category: Optional[Literal[
        "事前確定届出給与", "事前確定届出給与以外の給与", "業績連動給与"
    ]] = None
    payments: list[Payment]
    regular_payment: Optional[int] = None


class ExtractionResult(BaseModel):
    """Claude API が返す構造化データ全体"""

    corporation: Corporation
    resolution: Resolution
    officers: list[Officer]


class ExtractRequest(BaseModel):
    """POST /api/extract のリクエスト"""

    memo: str
    yakuin_master: list[dict]


class ExtractResponse(BaseModel):
    """POST /api/extract のレスポンス"""

    data: ExtractionResult
    cost_jpy: Optional[float] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
