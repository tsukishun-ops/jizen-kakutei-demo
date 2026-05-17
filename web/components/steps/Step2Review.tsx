"use client";

import { useState } from "react";
import { ArrowLeft, FileOutput } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ExtractionResult } from "@/lib/types";

interface Props {
  data: ExtractionResult;
  onSubmit: (data: ExtractionResult) => void;
  onBack: () => void;
  loading: boolean;
}

export default function Step2Review({ data, onSubmit, onBack, loading }: Props) {
  const [formData, setFormData] = useState<ExtractionResult>(
    JSON.parse(JSON.stringify(data))
  );

  const updateCorp = (field: string, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      corporation: { ...prev.corporation, [field]: value },
    }));
  };

  const updateResolution = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      resolution: { ...prev.resolution, [field]: value },
    }));
  };

  const updateOfficerPayment = (
    officerIdx: number,
    paymentIdx: number,
    field: string,
    value: string | number
  ) => {
    setFormData((prev) => {
      const officers = [...prev.officers];
      const payments = [...officers[officerIdx].payments];
      payments[paymentIdx] = { ...payments[paymentIdx], [field]: value };
      officers[officerIdx] = { ...officers[officerIdx], payments };
      return { ...prev, officers };
    });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">法人情報</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">法人名</label>
            <Input
              value={formData.corporation.name}
              onChange={(e) => updateCorp("name", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">法人番号</label>
            <Input
              value={formData.corporation.corporation_number || ""}
              onChange={(e) => updateCorp("corporation_number", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">納税地</label>
            <Input
              value={formData.corporation.address}
              onChange={(e) => updateCorp("address", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">所轄税務署</label>
            <Input
              value={formData.corporation.tax_office}
              onChange={(e) => updateCorp("tax_office", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">代表者</label>
            <Input
              value={formData.corporation.representative || ""}
              onChange={(e) => updateCorp("representative", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">電話番号</label>
            <Input
              value={formData.corporation.phone || ""}
              onChange={(e) => updateCorp("phone", e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">決議情報</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">決議日</label>
            <Input
              type="date"
              value={formData.resolution.decision_date}
              onChange={(e) => updateResolution("decision_date", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">決議機関</label>
            <Input
              value={formData.resolution.decision_body}
              onChange={(e) => updateResolution("decision_body", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">職務執行開始日</label>
            <Input
              type="date"
              value={formData.resolution.execution_start_date}
              onChange={(e) => updateResolution("execution_start_date", e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">届出期限区分</label>
            <Input
              value={formData.resolution.filing_deadline_basis || "イ"}
              onChange={(e) => updateResolution("filing_deadline_basis", e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">役員別 支給予定</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>氏名</TableHead>
                <TableHead>役職</TableHead>
                <TableHead>支給日</TableHead>
                <TableHead>支給額（円）</TableHead>
                <TableHead>月額報酬</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {formData.officers.map((officer, oi) =>
                officer.payments.map((payment, pi) => (
                  <TableRow key={`${oi}-${pi}`}>
                    <TableCell>{pi === 0 ? officer.name : ""}</TableCell>
                    <TableCell>{pi === 0 ? officer.position : ""}</TableCell>
                    <TableCell>
                      <Input
                        type="date"
                        value={payment.payment_date}
                        onChange={(e) =>
                          updateOfficerPayment(oi, pi, "payment_date", e.target.value)
                        }
                        className="w-40"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={payment.amount}
                        onChange={(e) =>
                          updateOfficerPayment(oi, pi, "amount", Number(e.target.value))
                        }
                        className="w-36"
                      />
                    </TableCell>
                    <TableCell>
                      {pi === 0 && officer.regular_payment
                        ? `${officer.regular_payment.toLocaleString()}円`
                        : ""}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          戻る
        </Button>
        <Button
          onClick={() => onSubmit(formData)}
          disabled={loading}
          className="bg-blue-900 px-8 hover:bg-blue-800"
        >
          <FileOutput className="mr-2 h-4 w-4" />
          {loading ? "生成中..." : "帳票を生成"}
        </Button>
      </div>
    </div>
  );
}
