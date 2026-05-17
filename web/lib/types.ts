export interface Corporation {
  name: string;
  corporation_number?: string | null;
  postal_code?: string | null;
  address: string;
  phone?: string | null;
  representative?: string | null;
  fiscal_year_start?: string | null;
  fiscal_year_end?: string | null;
  capital?: number | null;
  tax_office: string;
}

export interface Resolution {
  decision_date: string;
  decision_body: string;
  execution_start_date: string;
  fiscal_year_basis?: string | null;
  filing_deadline_basis?: string | null;
  reason_for_bonus_timing?: string | null;
  remarks?: string | null;
}

export interface Payment {
  payment_date: string;
  amount: number;
  memo?: string | null;
}

export interface Officer {
  name: string;
  name_kana?: string | null;
  position: string;
  appointment_date?: string | null;
  category?: string | null;
  payments: Payment[];
  regular_payment?: number | null;
}

export interface ExtractionResult {
  corporation: Corporation;
  resolution: Resolution;
  officers: Officer[];
}

export interface ExtractResponse {
  data: ExtractionResult;
  cost_jpy?: number | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
}

export interface YakuinRecord {
  役員ID: string;
  氏名フリガナ: string;
  氏名: string;
  役職: string;
  就任年月日: string;
  生年月日: string;
  住所: string;
  所属部門: string;
}

export interface ParseResponse {
  yakuin_master: YakuinRecord[];
  memo?: string | null;
}
