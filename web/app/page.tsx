"use client";

import { useState } from "react";
import { toast } from "sonner";
import { parseFiles, extractData, downloadFile } from "@/lib/api-client";
import { ExtractionResult } from "@/lib/types";
import ProgressIndicator from "@/components/ProgressIndicator";
import Step1Upload from "@/components/steps/Step1Upload";
import Step2Review from "@/components/steps/Step2Review";
import Step3Download from "@/components/steps/Step3Download";

export default function Home() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [extractionData, setExtractionData] = useState<ExtractionResult | null>(null);

  const handleStep1Submit = async (csvFile: File, memo: string) => {
    setLoading(true);
    try {
      const parseResult = await parseFiles(csvFile, memo);
      const extractResult = await extractData(memo, parseResult.yakuin_master as unknown as Record<string, string>[]);
      setExtractionData(extractResult.data);
      toast.success("AI による抽出が完了しました", {
        description: `APIコスト: ${extractResult.cost_jpy?.toFixed(2) || "N/A"}円`,
      });
      setStep(1);
    } catch (e) {
      toast.error("エラーが発生しました", {
        description: e instanceof Error ? e.message : "不明なエラー",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStep2Submit = async (data: ExtractionResult) => {
    setExtractionData(data);
    setStep(2);
    toast.success("帳票の生成準備が完了しました");
  };

  const handleDownload = async (type: "xlsx" | "pdf" | "csv") => {
    if (!extractionData) return;
    setLoading(true);
    try {
      const mimeTypes: Record<string, string> = {
        xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        pdf: "application/pdf",
        csv: "text/csv",
      };
      const blob = await downloadFile(type, extractionData);
      const typedBlob = new Blob([blob], { type: mimeTypes[type] });
      const url = URL.createObjectURL(typedBlob);
      const a = document.createElement("a");
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      a.href = url;
      a.download = `事前確定届出書_${extractionData.corporation.name}_${today}.${type}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`${type.toUpperCase()} をダウンロードしました`);
    } catch (e) {
      toast.error("ダウンロードに失敗しました", {
        description: e instanceof Error ? e.message : "不明なエラー",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(0);
    setExtractionData(null);
  };

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <h1 className="text-xl font-bold text-blue-900">
            事前確定届出書 自動生成システム
          </h1>
          <p className="text-sm text-gray-500">
            議事録メモから国税庁様式 C1-23 を自動生成
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-6">
        <ProgressIndicator currentStep={step} />

        {loading && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
            <div className="rounded-lg bg-white p-8 shadow-xl">
              <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-900" />
              <p className="mt-4 text-center text-sm text-gray-600">処理中...</p>
            </div>
          </div>
        )}

        {step === 0 && (
          <Step1Upload onSubmit={handleStep1Submit} loading={loading} />
        )}

        {step === 1 && extractionData && (
          <Step2Review
            data={extractionData}
            onSubmit={handleStep2Submit}
            onBack={() => setStep(0)}
            loading={loading}
          />
        )}

        {step === 2 && extractionData && (
          <Step3Download
            data={extractionData}
            onDownload={handleDownload}
            onReset={handleReset}
            loading={loading}
          />
        )}
      </main>

      <footer className="border-t bg-white py-4 text-center text-xs text-gray-400">
        事前確定届出書 自動生成システム &copy; 2025 Shun Tsukimura
      </footer>
    </div>
  );
}
