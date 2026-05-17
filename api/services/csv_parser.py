import io
from typing import Optional

import pandas as pd
from fastapi import HTTPException

YAKUIN_REQUIRED_COLUMNS = {"役員ID", "氏名フリガナ", "氏名", "役職", "就任年月日", "生年月日", "住所", "所属部門"}

YAYOI_REQUIRED_COLUMNS = {
    "識別フラグ", "伝票No", "取引日付", "借方勘定科目", "借方金額",
    "貸方勘定科目", "貸方金額",
}


def _detect_encoding_and_read(raw_bytes: bytes) -> str:
    """Shift_JIS / UTF-8 を自動判定してテキストに変換"""
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    raise HTTPException(status_code=400, detail="CSVの文字コードを判定できません（UTF-8 または Shift_JIS に対応）")


def _validate_columns(df: pd.DataFrame, required: set[str], file_label: str) -> None:
    """必須カラムの存在を検証"""
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"{file_label}に必須カラムが不足しています: {', '.join(sorted(missing))}",
        )


def parse_yakuin_master(raw_bytes: bytes) -> list[dict]:
    """役員マスタCSVをパースして辞書リストを返す"""
    text = _detect_encoding_and_read(raw_bytes)
    df = pd.read_csv(io.StringIO(text), dtype=str)
    df.columns = df.columns.str.strip()
    _validate_columns(df, YAKUIN_REQUIRED_COLUMNS, "役員マスタCSV")
    df = df.fillna("")
    return df.to_dict(orient="records")


def parse_yayoi_journal(raw_bytes: bytes) -> list[dict]:
    """弥生仕訳日記帳CSVをパースして辞書リストを返す"""
    text = _detect_encoding_and_read(raw_bytes)
    df = pd.read_csv(io.StringIO(text), dtype=str)
    df.columns = df.columns.str.strip()
    _validate_columns(df, YAYOI_REQUIRED_COLUMNS, "弥生仕訳日記帳CSV")
    df = df.fillna("")
    int_cols = ["借方金額", "借方税金額", "貸方金額", "貸方税金額"]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df.to_dict(orient="records")


def read_memo(raw_bytes: bytes) -> Optional[str]:
    """決議メモテキストを読み込む"""
    text = _detect_encoding_and_read(raw_bytes)
    stripped = text.strip()
    if not stripped:
        return None
    return stripped
