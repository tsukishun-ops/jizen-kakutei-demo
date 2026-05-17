import { ExtractResponse, ExtractionResult, ParseResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function parseFiles(
  yakuinFile: File,
  memoText?: string
): Promise<ParseResponse> {
  const formData = new FormData();
  formData.append("yakuin_master", yakuinFile);
  if (memoText) {
    const memoBlob = new Blob([memoText], { type: "text/plain" });
    formData.append("kessian_memo", memoBlob, "kessian_memo.txt");
  }

  const res = await fetch(`${API_BASE}/api/parse`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "パースに失敗しました" }));
    throw new Error(err.detail || "パースに失敗しました");
  }
  return res.json();
}

export async function extractData(
  memo: string,
  yakuinMaster: Record<string, string>[]
): Promise<ExtractResponse> {
  const res = await fetch(`${API_BASE}/api/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ memo, yakuin_master: yakuinMaster }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "AI抽出に失敗しました" }));
    throw new Error(err.detail || "AI抽出に失敗しました");
  }
  return res.json();
}

export async function downloadFile(
  type: "xlsx" | "pdf" | "csv",
  data: ExtractionResult
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/generate/${type}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const text = await res.text();
    let detail = "帳票生成に失敗しました";
    try { detail = JSON.parse(text).detail || detail; } catch {}
    throw new Error(detail);
  }
  const arrayBuffer = await res.arrayBuffer();
  return new Blob([arrayBuffer]);
}
