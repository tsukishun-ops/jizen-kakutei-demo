# 事前確定届出書 自動生成システム 完全指示書 v1
> AIエンジニア案件デモ（会計業務自動化／システム連携）
> Claude Code への一括指示用ドキュメント

---

## 0. このドキュメントの使い方

このファイルをプロジェクトのルートに `INSTRUCTIONS.md` として配置し、Claude Code を起動した最初のメッセージで以下を渡す：

```
INSTRUCTIONS.md を読み込んで、Phase 1 から順に実装してください。
各 Phase 完了時に動作確認結果を報告し、私の OK を待ってから次へ進んでください。
```

進行中、Claude Code が判断に迷ったら必ず停止して質問するよう、最初のメッセージで明示すること。

---

## 1. プロジェクト概要

### 目的
会計事務所向けに、株主総会の決議メモと役員マスタ CSV から、国税庁様式 C1-23「事前確定届出給与に関する届出書」を自動生成する Web アプリのデモを構築する。AI（Claude API）で自然言語の決議メモから構造化データを抽出する点が技術的コアバリュー。

### デモ価値訴求
1. **PDF しか配布されていない官公庁帳票の自動入力**（業界共通の痛み）
2. **非構造データ（議事録）からの構造化抽出**（生成 AI 活用）
3. **Excel / PDF 両対応**（会計事務所の業務フロー両方をカバー）
4. **TKC・弥生連携への拡張余地の提示**（README に拡張プランを明記）

### 想定面談トーク
「会計事務所の方々が毎期手作業で作成している事前確定届出書を、議事録メモと役員マスタから 30 秒で生成できるところまで作りました。次フェーズで TKC API 連携・弥生会計 CSV 取り込みまで広げる構想です。」

---

## 2. 技術スタック

### フロントエンド（Vercel デプロイ）
- Next.js 14 (App Router)
- TypeScript 5.x
- Tailwind CSS 3.x
- shadcn/ui（必要なコンポーネント：Button / Card / Input / Textarea / Tabs / Toast / Progress / Table / Dialog）
- React Hook Form + Zod（フォームバリデーション）
- lucide-react（アイコン）

### バックエンド（Render デプロイ）
- Python 3.11
- FastAPI + Uvicorn
- pandas（CSV 処理）
- openpyxl（Excel 生成）
- pypdf 4.x（PDF フォームフィールド書き込み）
- reportlab（PDF オーバーレイ描画、フォームフィールドが無い場合のフォールバック）
- anthropic（Claude API 公式 SDK）
- python-dotenv
- pydantic v2

### インフラ
- フロント：Vercel（無料）
- バック：Render Web Service（無料プラン、自動スリープあり）
- リポジトリ：GitHub（パブリック）

---

## 3. ディレクトリ構成

```
jizen-kakutei-demo/
├── INSTRUCTIONS.md                    # このファイル
├── README.md                          # ポートフォリオ用の説明
├── extraction_schema.json             # Claude API 抽出スキーマ
├── samples/
│   ├── yakuin_master.csv              # 役員マスタサンプル
│   ├── yayoi_journal.csv              # 弥生仕訳サンプル（参考）
│   ├── kessian_memo.txt               # 決議メモサンプル
│   ├── honpyo_template.pdf            # 国税庁本表 PDF（手動配置）
│   └── futahyo1_template.pdf          # 国税庁付表1 PDF（手動配置）
├── web/                               # Next.js
│   ├── app/
│   │   ├── page.tsx                   # トップ（3ステップウィザード）
│   │   ├── layout.tsx
│   │   └── api/                       # Next.js API routes（バックエンドへのプロキシ）
│   ├── components/
│   │   ├── ui/                        # shadcn/ui
│   │   ├── steps/
│   │   │   ├── Step1Upload.tsx
│   │   │   ├── Step2Review.tsx
│   │   │   └── Step3Download.tsx
│   │   └── ProgressIndicator.tsx
│   ├── lib/
│   │   ├── api-client.ts              # FastAPI 呼び出し
│   │   └── types.ts                   # extraction_schema.json から生成
│   ├── package.json
│   ├── tailwind.config.ts
│   └── next.config.js
├── api/                               # FastAPI
│   ├── main.py                        # エントリポイント
│   ├── routers/
│   │   ├── parse.py                   # /api/parse
│   │   ├── extract.py                 # /api/extract
│   │   └── generate.py                # /api/generate/{xlsx,pdf}
│   ├── services/
│   │   ├── csv_parser.py
│   │   ├── claude_extractor.py
│   │   ├── xlsx_builder.py
│   │   └── pdf_filler.py
│   ├── models/
│   │   └── schema.py                  # extraction_schema.json から生成された Pydantic モデル
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile                     # Render 用
└── docs/
    ├── architecture.md                # 構成図とフロー説明
    ├── demo_script.md                 # 面談での実演スクリプト
    └── future_roadmap.md              # TKC 連携等の拡張プラン
```

---

## 4. 環境変数

`api/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=4000
COST_LIMIT_JPY_PER_REQUEST=100
ALLOWED_ORIGINS=http://localhost:3000,https://your-vercel-url.vercel.app
```

`web/.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 5. Phase 別実装計画

### Phase 0: 事前準備（人間がやる作業）
**Claude Code に依頼する前に Shun が手動で完了させること**

1. `samples/honpyo_template.pdf` と `samples/futahyo1_template.pdf` を国税庁サイトから取得して配置  
   URL: https://www.nta.go.jp/taxes/tetsuzuki/shinsei/annai/hojin/annai/5104.htm
2. Acrobat Reader で本表 PDF を開き、入力欄がクリックして文字を打てる「フォーム入力 PDF」か、印刷専用かを確認  
   → 結果を Phase 3 開始時に Claude Code に伝える（実装分岐に必要）
3. Anthropic API キーを取得し、Render と Vercel のアカウントを準備
4. GitHub 上に新規リポジトリ `jizen-kakutei-demo` を作成

---

### Phase 1: バックエンド基盤と CSV パーサー

**目的**：FastAPI を立ち上げ、役員マスタ CSV と仕訳 CSV を読み込み、整形して JSON で返すエンドポイントを作る。

**タスク**：
1. `api/` 配下に FastAPI プロジェクトを初期化
2. `requirements.txt` に必要パッケージを列挙
3. CORS 設定（`ALLOWED_ORIGINS` 環境変数から読み込み）
4. `services/csv_parser.py` を実装
   - 弥生会計仕訳日記帳の標準カラム構造をパース
   - 文字コードは Shift_JIS / UTF-8 両対応（自動判定）
   - 役員マスタの最小カラムをバリデーション
5. `routers/parse.py` で `POST /api/parse` を実装
   - multipart/form-data で `yakuin_master.csv` と `kessian_memo.txt`（オプションで `yayoi_journal.csv`）を受け取る
   - パース結果を JSON で返す
6. `GET /api/health` を実装（Render のヘルスチェック用）

**完了条件**：
- ローカルで `uvicorn main:app --reload` が起動する
- `samples/yakuin_master.csv` をアップロードして、役員 5 名の構造化 JSON が返る
- 不正な CSV（カラム不足）でバリデーションエラーが返る

**報告内容**：
- 起動コマンドと動作確認のスクリーンショット相当のログ
- 想定外の挙動があれば質問

---

### Phase 2: Claude API による抽出エンジン

**目的**：決議メモ（自然言語）と役員マスタ JSON を入力に、`extraction_schema.json` 準拠の構造化データを出力する。

**タスク**：
1. `extraction_schema.json` を読み込み、`models/schema.py` に Pydantic モデルとして再現
2. `services/claude_extractor.py` を実装
   - Anthropic SDK を使用
   - システムプロンプトで JSON Schema を提示し、JSON のみ返すよう厳密に指示
   - `response_format` の代替として、プロンプトで「コードブロックや前置きなしで JSON のみ返す」と明示
   - パース失敗時は最大 2 回までリトライ（自己修正プロンプト）
   - コスト概算：入力 + 出力トークン数からドル換算→円換算してログ出力
   - `COST_LIMIT_JPY_PER_REQUEST` を超える見込みなら事前に拒否
3. `routers/extract.py` で `POST /api/extract` を実装
   - 入力：`memo` (string) と `yakuin_master` (役員マスタ JSON 配列)
   - 出力：Pydantic バリデーション済みの構造化データ
4. ユニットテスト：`samples/kessian_memo.txt` を入力して、田中太郎/鈴木花子/佐藤次郎の 3 名分の支給情報が正しく抽出されるか確認

**完了条件**：
- サンプル決議メモから 3 名分の `officers` 配列が抽出され、各人に 12 月 10 日の支給予定が含まれる
- 法人名・納税地・決議日が正しく抽出される
- コスト計算ログがリクエストごとに出る

**プロンプト設計の指針**：
- システムプロンプトに JSON Schema を埋め込む
- 「日付は YYYY-MM-DD 形式で出力」「金額は円単位の整数」「不明な項目は null」を明記
- few-shot で 1 例だけ提示すると精度が安定する

---

### Phase 3: 帳票生成（Excel + PDF）

**目的**：構造化データから本表 + 付表1 の Excel と PDF を生成する。

**タスク**：
1. `services/xlsx_builder.py` を実装
   - openpyxl で国税庁様式を再現したテンプレートを生成
   - シート1：本表、シート2：付表1
   - セル結合、罫線、フォントサイズで実物に近づける
   - 役員数が多い場合は付表1 のシートを動的に複数生成
2. `services/pdf_filler.py` を実装  
   **Phase 0 の確認結果に応じて分岐**
   - **フォーム入力 PDF の場合**：`pypdf` の `update_page_form_field_values()` でフィールド名を辞書で渡す。最初にフィールド名一覧を抽出して `docs/pdf_fields.md` に記録
   - **印刷専用 PDF の場合**：`reportlab` で透明オーバーレイ PDF を作成し、`pypdf` で元 PDF に重ね焼き。座標は `docs/pdf_coordinates.md` にハードコード
3. `routers/generate.py` で `POST /api/generate/xlsx` と `POST /api/generate/pdf` を実装
   - 入力：構造化データ
   - 出力：バイナリレスポンス（Content-Disposition で適切なファイル名）

**完了条件**：
- 抽出済みデータから Excel が生成され、Excel で開いて様式が崩れていない
- 同データから PDF が生成され、Acrobat Reader で開いて文字が正しい位置に表示される
- ダウンロードファイル名が `事前確定届出書_株式会社サンプルコーポレーション_20250520.xlsx` 等になる

---

### Phase 4: フロントエンドUI（3ステップウィザード）

**目的**：会計事務所職員が直感的に使える Web UI。

**タスク**：
1. `web/` 配下に Next.js プロジェクトを初期化（TypeScript、Tailwind、App Router）
2. shadcn/ui をセットアップし必要コンポーネントをインストール
3. `extraction_schema.json` から TypeScript 型定義を生成（`json-schema-to-typescript`）
4. トップページで 3 ステップウィザード
   - **Step 1: アップロード**
     - 役員マスタ CSV のドラッグ&ドロップ
     - 決議メモのテキストエリア（サンプルを「サンプルを読み込む」ボタンで挿入可能）
     - 「AI で抽出」ボタン
   - **Step 2: レビュー**
     - 抽出結果を編集可能なフォームで表示
     - 法人情報セクション、決議情報セクション、役員ごとの支給予定テーブル
     - React Hook Form + Zod でバリデーション
     - 「修正して帳票生成」ボタン
   - **Step 3: ダウンロード**
     - 本表 PDF プレビュー（embed タグまたは pdf.js）
     - Excel ダウンロードボタンと PDF ダウンロードボタン
     - 「最初に戻る」ボタン
5. プログレスインジケータをヘッダーに常時表示
6. Toast 通知（成功・エラー）
7. ローディング中はステップ全体に loading オーバーレイ
8. レスポンシブ対応（タブレットまで）

**デザイン指針**：
- 配色：会計事務所向けの清潔感ある白基調 + アクセントに濃紺
- フォント：日本語は Noto Sans JP、英数字は Inter
- 装飾を最小限にして、業務ツールらしい誠実なトーン

**完了条件**：
- ローカルで `npm run dev` 起動、`localhost:3000` で全ステップが動く
- サンプルデータでエンドツーエンドの流れが完走し、Excel と PDF がダウンロードできる
- エラー時に Toast が表示される

---

### Phase 5: デプロイとドキュメント整備

**目的**：面談で URL を共有できる状態にする。

**タスク**：
1. **Render に FastAPI をデプロイ**
   - Dockerfile を作成
   - 環境変数を Render ダッシュボードに設定
   - 自動スリープ前提なので、ヘルスチェック用の cron-job.org 設定（5 分おきに `/api/health` を叩いてスリープ防止）も README に記載
2. **Vercel に Next.js をデプロイ**
   - `NEXT_PUBLIC_API_BASE_URL` を Render の URL に設定
3. **README.md** を仕上げる（次セクションのテンプレ参照）
4. **`docs/architecture.md`**：構成図（mermaid 記法）、データフロー、技術選定理由
5. **`docs/demo_script.md`**：面談での 5 分プレゼン台本（こちらで作成済み、`samples/` から移植）
6. **`docs/future_roadmap.md`**：TKC API 連携、弥生会計 API 連携、e-Tax XML 出力、複数法人対応、議事録 OCR、Slack/Chatwork 通知連携

**完了条件**：
- Vercel の公開 URL でサンプルデータでのデモが完走
- ポートフォリオサイト（shuntsukimura-tech.vercel.app）の Works に追加
- GitHub README に Vercel デプロイバッジ、技術スタックバッジ、デモ GIF

---

## 6. README.md テンプレート（Phase 5 で完成させる）

```markdown
# 事前確定届出書 自動生成システム

> 会計事務所向け、議事録メモから国税庁様式 C1-23 を自動生成する Web アプリケーション

[![Deployed on Vercel](https://img.shields.io/badge/Vercel-deployed-black)](https://...)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)]()
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)]()

## デモ
👉 https://jizen-kakutei-demo.vercel.app

## 解決する課題
- 国税庁様式は PDF のみ配布で、Excel 版が存在しない
- 議事録から手作業で転記する作業に時間がかかる
- TKC・弥生など会計ソフトとの連携が個別開発になっている

## 技術スタック
| 領域 | 技術 |
|---|---|
| フロント | Next.js 14 / TypeScript / Tailwind / shadcn/ui |
| バック | Python 3.11 / FastAPI / pandas / openpyxl / pypdf |
| AI | Claude API (Sonnet 4) による構造化抽出 |
| インフラ | Vercel + Render |

## アーキテクチャ
（mermaid 図）

## ローカル起動
（手順）

## 拡張プラン
- TKC API / 弥生 API 直接連携
- e-Tax XML 形式での書き出し
- 議事録 PDF/画像からの OCR 入力
- 複数法人対応（会計事務所が顧問先 100 社を管理できる UI）

## 作者
月村駿 / Shun Tsukimura  
https://shuntsukimura-tech.vercel.app
```

---

## 7. コスト見積もり

| 項目 | 月額 |
|---|---|
| Anthropic API（デモ運用 1日5回程度） | 0〜300円 |
| Vercel Hobby | 0円 |
| Render Free Tier | 0円 |
| 合計 | ほぼ0円 |

実案件想定（顧問先 100 社、年 2 回作成）の API コストは年 1〜2 万円程度と試算し、README に明記する。

---

## 8. 想定面談 Q&A

| 想定質問 | 回答方針 |
|---|---|
| 精度はどれくらい？ | サンプルデータでは構造化抽出精度 100%。実データでは初回 80% 程度を想定し、Step 2 の編集 UI で人間確認を必須化している。 |
| 弥生・TKC との連携は？ | 現状は CSV 取り込み。TKC は公式 API 公開が限定的なので、Phase 2 として TKC FX クラウドの CSV エクスポート対応、Phase 3 で弥生会計 API 連携を想定。 |
| セキュリティは？ | デモ版はパブリックだが、本番想定では顧客データの保存をしない設計（揮発処理）。Anthropic は学習データに利用しない API プランを採用。 |
| 開発期間は？ | デモ部分はゼロベースで 3 日。実案件規模であれば要件定義 1 週 + 開発 4 週で MVP 想定。 |
| 月20〜30時間で対応可能か？ | このデモ規模のシステムは初期構築後、保守・拡張で十分その範囲内。並行で複数案件もカバー可能。 |

---

## 9. Claude Code 実行時の注意

- **必ず Phase 1 から順番に実装する**。並行作業や先回りはしない
- 各 Phase 完了時、動作確認結果をログ付きで報告
- 不明点は推測せず必ず質問
- ファイル削除や大規模リファクタは事前承認を取る
- コミット粒度は Phase 単位（`feat: phase1 csv parser implementation` のような形）
- 日本語コメントを推奨（会計用語が多いため）

---

## 10. Phase 0 確認事項チェックリスト

開発開始前に Shun が完了させること：

- [ ] 国税庁から PDF テンプレ 2 種を `samples/` に配置
- [ ] PDF がフォーム入力可能か確認した
- [ ] Anthropic API キーを取得した
- [ ] Render アカウントを作成した
- [ ] Vercel アカウントを確認した
- [ ] GitHub に新規リポジトリを作成した
- [ ] 初期ディレクトリ構造を作成して INSTRUCTIONS.md を配置した

---

以上
