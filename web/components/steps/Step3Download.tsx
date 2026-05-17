"use client";

import { Download, FileSpreadsheet, FileText, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExtractionResult } from "@/lib/types";

interface Props {
  data: ExtractionResult;
  onDownload: (type: "xlsx" | "pdf") => void;
  onReset: () => void;
  loading: boolean;
}

export default function Step3Download({ data, onDownload, onReset, loading }: Props) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">生成完了</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-gray-600">
            「{data.corporation.name}」の事前確定届出給与に関する届出書が生成されました。
            以下からダウンロードしてください。
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card className="border-2 hover:border-blue-300 transition-colors">
              <CardContent className="flex flex-col items-center gap-3 p-6">
                <FileSpreadsheet className="h-12 w-12 text-green-600" />
                <h3 className="font-bold">Excel ファイル</h3>
                <p className="text-center text-sm text-gray-500">
                  本表・付表1 を含む Excel ブック
                </p>
                <Button
                  onClick={() => onDownload("xlsx")}
                  disabled={loading}
                  className="mt-2 w-full bg-green-600 hover:bg-green-700"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Excel をダウンロード
                </Button>
              </CardContent>
            </Card>
            <Card className="border-2 hover:border-blue-300 transition-colors">
              <CardContent className="flex flex-col items-center gap-3 p-6">
                <FileText className="h-12 w-12 text-red-600" />
                <h3 className="font-bold">PDF ファイル</h3>
                <p className="text-center text-sm text-gray-500">
                  国税庁様式テンプレートに記入済み
                </p>
                <Button
                  onClick={() => onDownload("pdf")}
                  disabled={loading}
                  variant="outline"
                  className="mt-2 w-full border-red-300 text-red-600 hover:bg-red-50"
                >
                  <Download className="mr-2 h-4 w-4" />
                  PDF をダウンロード
                </Button>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button variant="outline" onClick={onReset}>
          <RotateCcw className="mr-2 h-4 w-4" />
          最初に戻る
        </Button>
      </div>
    </div>
  );
}
