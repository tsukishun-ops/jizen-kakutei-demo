"use client";

import { CheckCircle2 } from "lucide-react";

const STEPS = [
  { label: "アップロード", description: "CSV・メモ入力" },
  { label: "レビュー", description: "抽出結果の確認・編集" },
  { label: "ダウンロード", description: "Excel・PDF出力" },
];

interface Props {
  currentStep: number;
}

export default function ProgressIndicator({ currentStep }: Props) {
  return (
    <div className="flex items-center justify-center gap-0 py-6">
      {STEPS.map((step, i) => {
        const isCompleted = i < currentStep;
        const isCurrent = i === currentStep;
        return (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-bold transition-colors ${
                  isCompleted
                    ? "border-blue-900 bg-blue-900 text-white"
                    : isCurrent
                    ? "border-blue-900 bg-white text-blue-900"
                    : "border-gray-300 bg-white text-gray-400"
                }`}
              >
                {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : i + 1}
              </div>
              <span
                className={`mt-1 text-xs ${
                  isCurrent ? "font-bold text-blue-900" : "text-gray-500"
                }`}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`mx-2 h-0.5 w-16 ${
                  isCompleted ? "bg-blue-900" : "bg-gray-300"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
