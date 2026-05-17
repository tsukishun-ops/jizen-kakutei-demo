"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileText, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

const SAMPLE_MEMO = `【定時株主総会決議メモ】

開催日：令和7年5月20日（火）
開催場所：当社本社会議室
出席状況：株主3名（全員出席）、議決権の100%

決議事項：

第1号議案 取締役の役員報酬および事前確定届出給与の件

当期の役員報酬および事前確定届出給与について、下記のとおり決議した。

定期同額給与（月額）
・代表取締役 田中太郎：80万円
・取締役 鈴木花子：60万円
・取締役 佐藤次郎：50万円

事前確定届出給与（賞与）
代表取締役 田中太郎に対し、令和7年12月10日に金300万円を支給する。
取締役 鈴木花子に対し、令和7年12月10日に金200万円を支給する。
取締役 佐藤次郎に対し、令和7年12月10日に金150万円を支給する。

なお、上記事前確定届出給与の支給時期を賞与時期とした理由は、業績連動性を反映させつつ役員のモチベーション維持を図るためである。

職務執行期間：令和7年5月20日から令和8年5月の定時株主総会終結の時まで

以上をもって本日の議事を終了し、午前11時に閉会した。

---

【法人基本情報】
法人名：株式会社サンプルコーポレーション
法人番号：1234567890123
納税地：〒106-0032 東京都港区六本木1-2-3
電話：03-1234-5678
代表者：代表取締役 田中太郎
事業年度：令和7年4月1日 〜 令和8年3月31日
資本金：1,000万円
所轄税務署：麻布税務署`;

interface Props {
  onSubmit: (csvFile: File, memo: string) => void;
  loading: boolean;
}

export default function Step1Upload({ onSubmit, loading }: Props) {
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [memo, setMemo] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".csv")) {
      setCsvFile(file);
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setCsvFile(file);
  };

  const handleSubmit = () => {
    if (csvFile && memo.trim()) {
      onSubmit(csvFile, memo);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Upload className="h-5 w-5" />
            役員マスタ CSV
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            {csvFile ? (
              <div className="flex items-center justify-center gap-2 text-blue-900">
                <FileText className="h-5 w-5" />
                <span className="font-medium">{csvFile.name}</span>
              </div>
            ) : (
              <div className="text-gray-500">
                <Upload className="mx-auto mb-2 h-8 w-8" />
                <p>CSV ファイルをドラッグ＆ドロップ、またはクリックして選択</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-lg">
            <span className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              決議メモ
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMemo(SAMPLE_MEMO)}
              type="button"
            >
              サンプルを読み込む
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            placeholder="株主総会の決議メモをここに入力してください..."
            rows={12}
            className="resize-y font-mono text-sm"
          />
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          onClick={handleSubmit}
          disabled={!csvFile || !memo.trim() || loading}
          size="lg"
          className="bg-blue-900 px-8 hover:bg-blue-800"
        >
          <Sparkles className="mr-2 h-5 w-5" />
          {loading ? "AI で抽出中..." : "AI で抽出"}
        </Button>
      </div>
    </div>
  );
}
