import json
import logging
import os

import anthropic
from fastapi import HTTPException

from models.schema import ExtractionResult

logger = logging.getLogger(__name__)

EXTRACTION_SCHEMA = """{
  "type": "object",
  "required": ["corporation", "resolution", "officers"],
  "properties": {
    "corporation": {
      "type": "object",
      "required": ["name", "address", "tax_office"],
      "properties": {
        "name": { "type": "string" },
        "corporation_number": { "type": "string" },
        "postal_code": { "type": "string" },
        "address": { "type": "string" },
        "phone": { "type": "string" },
        "representative": { "type": "string" },
        "fiscal_year_start": { "type": "string", "format": "date" },
        "fiscal_year_end": { "type": "string", "format": "date" },
        "capital": { "type": "integer" },
        "tax_office": { "type": "string" }
      }
    },
    "resolution": {
      "type": "object",
      "required": ["decision_date", "decision_body", "execution_start_date"],
      "properties": {
        "decision_date": { "type": "string", "format": "date" },
        "decision_body": { "type": "string", "enum": ["定時株主総会", "臨時株主総会", "取締役会", "報酬委員会", "社員総会", "その他"] },
        "execution_start_date": { "type": "string", "format": "date" },
        "fiscal_year_basis": { "type": "string", "format": "date" },
        "filing_deadline_basis": { "type": "string", "enum": ["イ", "ロ", "ハ"] },
        "reason_for_bonus_timing": { "type": "string" },
        "remarks": { "type": "string" }
      }
    },
    "officers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "position", "payments"],
        "properties": {
          "name": { "type": "string" },
          "name_kana": { "type": "string" },
          "position": { "type": "string" },
          "appointment_date": { "type": "string", "format": "date" },
          "category": { "type": "string", "enum": ["事前確定届出給与", "事前確定届出給与以外の給与", "業績連動給与"] },
          "payments": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["payment_date", "amount"],
              "properties": {
                "payment_date": { "type": "string", "format": "date" },
                "amount": { "type": "integer" },
                "memo": { "type": "string" }
              }
            }
          },
          "regular_payment": { "type": "integer" }
        }
      }
    }
  }
}"""

SYSTEM_PROMPT = f"""あなたは会計業務の専門家です。
株主総会の決議メモと役員マスタ情報から、「事前確定届出給与に関する届出書」に必要な構造化データを抽出してください。

出力は以下の JSON Schema に厳密に従った JSON のみを返してください。
前置き、説明、コードブロック記号(```)は一切不要です。純粋な JSON だけを返してください。

JSON Schema:
{EXTRACTION_SCHEMA}

ルール:
- 日付は必ず YYYY-MM-DD 形式で出力する
- 和暦（令和N年）は西暦に変換する（令和7年 = 2025年）
- 金額は円単位の整数で出力する（「300万円」→ 3000000）
- 不明な項目は null とする
- 役員マスタに存在する役員のフリガナ・就任年月日を name_kana, appointment_date に反映する
- 事前確定届出給与の対象者のみ officers 配列に含める（定期同額給与のみの役員は含めない）
- 定期同額給与の月額が判明している場合は regular_payment に設定する
- category は原則「事前確定届出給与」とする
- decision_body は決議メモの記載から判定する（「定時株主総会決議メモ」→「定時株主総会」）
- execution_start_date は「職務の執行を開始する日」、不明なら decision_date と同日にする
- fiscal_year_basis は事業年度開始日
- filing_deadline_basis は通常の届出なら「イ」
- reason_for_bonus_timing には賞与時期とした理由を記載する"""

FEW_SHOT_EXAMPLE = """
例:
入力メモ: "令和7年5月15日の定時株主総会で、代表取締役 山田太郎に令和7年12月10日に200万円を支給する決議をした。法人名: テスト株式会社、納税地: 東京都千代田区、所轄: 神田税務署、事業年度: 令和7年4月1日〜令和8年3月31日"
役員マスタ: [{"氏名": "山田 太郎", "氏名フリガナ": "ヤマダ タロウ", "役職": "代表取締役", "就任年月日": "2020-04-01"}]

出力:
{"corporation":{"name":"テスト株式会社","corporation_number":null,"postal_code":null,"address":"東京都千代田区","phone":null,"representative":"山田太郎","fiscal_year_start":"2025-04-01","fiscal_year_end":"2026-03-31","capital":null,"tax_office":"神田税務署"},"resolution":{"decision_date":"2025-05-15","decision_body":"定時株主総会","execution_start_date":"2025-05-15","fiscal_year_basis":"2025-04-01","filing_deadline_basis":"イ","reason_for_bonus_timing":null,"remarks":null},"officers":[{"name":"山田 太郎","name_kana":"ヤマダ タロウ","position":"代表取締役","appointment_date":"2020-04-01","category":"事前確定届出給与","payments":[{"payment_date":"2025-12-10","amount":2000000,"memo":null}],"regular_payment":null}]}"""

SONNET_INPUT_COST_PER_TOKEN = 3.0 / 1_000_000
SONNET_OUTPUT_COST_PER_TOKEN = 15.0 / 1_000_000
USD_TO_JPY = 150.0


def _estimate_cost_jpy(tokens_in: int, tokens_out: int) -> float:
    usd = tokens_in * SONNET_INPUT_COST_PER_TOKEN + tokens_out * SONNET_OUTPUT_COST_PER_TOKEN
    return round(usd * USD_TO_JPY, 2)


def extract_from_memo(memo: str, yakuin_master: list[dict]) -> dict:
    """決議メモと役員マスタから構造化データを抽出する"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY が設定されていません")

    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
    cost_limit = float(os.getenv("COST_LIMIT_JPY_PER_REQUEST", "100"))

    yakuin_str = json.dumps(yakuin_master, ensure_ascii=False, indent=2)
    user_message = f"""以下の決議メモと役員マスタ情報から、事前確定届出給与の届出書に必要なデータを JSON で抽出してください。

【決議メモ】
{memo}

【役員マスタ】
{yakuin_str}"""

    client = anthropic.Anthropic(api_key=api_key)

    last_error = None
    for attempt in range(3):
        messages = [{"role": "user", "content": user_message}]

        if attempt > 0 and last_error:
            messages.append({"role": "assistant", "content": "申し訳ありません。前回の出力にエラーがありました。"})
            messages.append({"role": "user", "content": f"前回のJSONパースエラー: {last_error}\n正しい JSON のみを返してください。前置きやコードブロック記号は不要です。"})

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT + "\n" + FEW_SHOT_EXAMPLE,
            messages=messages,
        )

        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        cost_jpy = _estimate_cost_jpy(tokens_in, tokens_out)

        logger.info(
            "Claude API call: attempt=%d, tokens_in=%d, tokens_out=%d, cost=%.2f JPY",
            attempt + 1, tokens_in, tokens_out, cost_jpy,
        )

        if cost_jpy > cost_limit:
            raise HTTPException(
                status_code=429,
                detail=f"コスト上限超過: {cost_jpy:.2f}円 > {cost_limit:.2f}円",
            )

        raw_text = response.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

        try:
            parsed = json.loads(raw_text)
            result = ExtractionResult.model_validate(parsed)
            return {
                "data": result,
                "cost_jpy": cost_jpy,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            }
        except (json.JSONDecodeError, Exception) as e:
            last_error = str(e)
            logger.warning("Attempt %d failed: %s", attempt + 1, last_error)

    raise HTTPException(
        status_code=502,
        detail=f"Claude API から有効な JSON を取得できませんでした（3回試行）: {last_error}",
    )
