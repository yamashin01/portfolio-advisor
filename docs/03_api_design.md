# API設計書

## 1. 概要

| 項目 | 内容 |
|------|------|
| ベースURL | `https://api.portfolio-advisor.example.com/api/v1` |
| 開発URL | `http://localhost:8000/api/v1` |
| プロトコル | HTTPS (本番) / HTTP (開発) |
| フォーマット | JSON (application/json) |
| 認証 | 不要（全エンドポイントがパブリック） |
| APIドキュメント | `/docs` (Swagger UI), `/redoc` (ReDoc) |
| バージョニング | URLパス方式 (`/api/v1/`) |

---

## 3. 共通仕様

### 3.1 エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ",
  "status_code": 400,
  "errors": [
    {
      "field": "email",
      "message": "有効なメールアドレスを入力してください"
    }
  ]
}
```

### 3.2 HTTPステータスコード

| コード | 意味 | 使用場面 |
|--------|------|---------|
| 200 | OK | 正常レスポンス |
| 400 | Bad Request | バリデーションエラー |
| 404 | Not Found | リソース不存在 |
| 422 | Unprocessable Entity | Pydanticバリデーションエラー |
| 429 | Too Many Requests | レート制限超過 |
| 500 | Internal Server Error | サーバー内部エラー |

### 3.3 ページネーション

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

クエリパラメータ: `?page=1&per_page=20`

### 3.4 コスト制御（レート制限に代替）

個人/少人数利用のため、IP単位のレート制限（slowapi）は使用しない。代わりに、Claude API呼び出しに対するトークン予算ベースの制御を行う。

| 制御対象 | 上限 | 設定方法 |
|---------|------|---------|
| Claude API 日次トークン | 100,000トークン（デフォルト） | 環境変数 `DAILY_TOKEN_BUDGET` |
| Claude API 月次トークン | 2,000,000トークン（デフォルト） | 環境変数 `MONTHLY_TOKEN_BUDGET` |

予算超過時のレスポンス:
```json
{
  "detail": "本日のAI利用上限に達しました。明日以降に再度お試しください。",
  "status_code": 429,
  "error_code": "DAILY_BUDGET_EXCEEDED",
  "usage": {
    "daily_tokens_used": 100500,
    "daily_token_budget": 100000,
    "monthly_tokens_used": 850000,
    "monthly_token_budget": 2000000
  }
}
```

---

## 4. エンドポイント一覧

### 4.0 ヘルスチェック

| メソッド | パス | 認証 | 説明 |
|---------|------|------|------|
| GET | `/api/v1/health` | 不要 | ヘルスチェック |

---

### 4.1 リスク診断 (Risk Assessment)

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/risk-assessment/questions` | 診断質問一覧取得 |
| POST | `/api/v1/risk-assessment/calculate` | リスクスコア計算（ステートレス） |

---

#### GET /api/v1/risk-assessment/questions

リスク診断ウィザードで使用する質問リストを返す。

**Response 200**:
```json
{
  "questions": [
    {
      "id": 1,
      "question": "あなたの年齢を教えてください",
      "type": "single_choice",
      "options": [
        { "value": "20s", "label": "20代", "score_weight": 3 },
        { "value": "30s", "label": "30代", "score_weight": 3 },
        { "value": "40s", "label": "40代", "score_weight": 2 },
        { "value": "50s", "label": "50代", "score_weight": 1 },
        { "value": "60plus", "label": "60代以上", "score_weight": 0 }
      ]
    },
    {
      "id": 2,
      "question": "投資の目的は何ですか？",
      "type": "single_choice",
      "options": [
        { "value": "retirement", "label": "老後の資金準備", "score_weight": 2 },
        { "value": "education", "label": "教育資金", "score_weight": 1 },
        { "value": "wealth_growth", "label": "資産を増やしたい", "score_weight": 3 },
        { "value": "preservation", "label": "資産を守りたい", "score_weight": 0 }
      ]
    },
    {
      "id": 3,
      "question": "投資期間はどれくらいを予定していますか？",
      "type": "single_choice",
      "options": [
        { "value": "short", "label": "1〜3年", "score_weight": 0 },
        { "value": "medium", "label": "3〜10年", "score_weight": 2 },
        { "value": "long", "label": "10年以上", "score_weight": 3 }
      ]
    },
    {
      "id": 4,
      "question": "投資経験はありますか？",
      "type": "single_choice",
      "options": [
        { "value": "none", "label": "まったくない", "score_weight": 0 },
        { "value": "beginner", "label": "1年未満", "score_weight": 1 },
        { "value": "intermediate", "label": "1〜5年", "score_weight": 2 },
        { "value": "advanced", "label": "5年以上", "score_weight": 3 }
      ]
    },
    {
      "id": 5,
      "question": "投資した資産が1ヶ月で20%下落した場合、どうしますか？",
      "type": "single_choice",
      "options": [
        { "value": "sell_all", "label": "すべて売却する", "score_weight": 0 },
        { "value": "sell_part", "label": "一部を売却する", "score_weight": 1 },
        { "value": "hold", "label": "そのまま保持する", "score_weight": 2 },
        { "value": "buy_more", "label": "買い増しする", "score_weight": 3 }
      ]
    },
    {
      "id": 6,
      "question": "毎月の投資可能額はどれくらいですか？",
      "type": "single_choice",
      "options": [
        { "value": "under_10k", "label": "1万円未満", "score_weight": 0 },
        { "value": "10k_30k", "label": "1〜3万円", "score_weight": 1 },
        { "value": "30k_100k", "label": "3〜10万円", "score_weight": 2 },
        { "value": "over_100k", "label": "10万円以上", "score_weight": 3 }
      ]
    },
    {
      "id": 7,
      "question": "以下のうち、最も共感する投資方針はどれですか？",
      "type": "single_choice",
      "options": [
        { "value": "safety_first", "label": "元本割れはなるべく避けたい", "score_weight": 0 },
        { "value": "balanced", "label": "多少のリスクは許容し、バランスよく運用したい", "score_weight": 2 },
        { "value": "growth", "label": "リスクを取ってでも高いリターンを狙いたい", "score_weight": 3 }
      ]
    },
    {
      "id": 8,
      "question": "緊急時に使える預貯金（生活費の3〜6ヶ月分）はありますか？",
      "type": "single_choice",
      "options": [
        { "value": "no", "label": "ない", "score_weight": 0 },
        { "value": "partial", "label": "一部ある（3ヶ月未満）", "score_weight": 1 },
        { "value": "yes", "label": "十分にある（6ヶ月以上）", "score_weight": 2 }
      ]
    }
  ]
}
```

---

#### POST /api/v1/risk-assessment/calculate

リスク診断の回答を送信し、スコアを計算して返却する。**ステートレス** — 結果はDBに保存しない。

**Request Body**:
```json
{
  "answers": [
    { "question_id": 1, "value": "30s" },
    { "question_id": 2, "value": "wealth_growth" },
    { "question_id": 3, "value": "long" },
    { "question_id": 4, "value": "beginner" },
    { "question_id": 5, "value": "hold" },
    { "question_id": 6, "value": "30k_100k" },
    { "question_id": 7, "value": "balanced" },
    { "question_id": 8, "value": "yes" }
  ]
}
```

**Response 200**:
```json
{
  "risk_score": 7,
  "risk_tolerance": "moderate",
  "investment_horizon": "long",
  "investment_experience": "beginner",
  "recommended_strategy": "hrp",
  "description": "あなたのリスク許容度は「バランス型」です。長期投資を前提に、株式と債券をバランスよく組み合わせたポートフォリオをおすすめします。"
}
```

**スコア計算ロジック**:
```
raw_score = Σ(各質問のscore_weight)
max_possible = Σ(各質問の最大score_weight)
normalized_score = round(raw_score / max_possible * 9) + 1  # 1-10

risk_tolerance:
  score 1-3  → conservative
  score 4-7  → moderate
  score 8-10 → aggressive
```

---

### 4.2 ポートフォリオ (Portfolios)

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/v1/portfolios/generate` | ポートフォリオ生成（ステートレス） |
| POST | `/api/v1/portfolios/backtest` | バックテスト実行（ステートレス） |
| POST | `/api/v1/portfolios/explain` | AI説明生成（ステートレス） |

※ すべてステートレス。結果はレスポンスで返却し、DBに保存しない。

---

#### POST /api/v1/portfolios/generate

リスクスコアに基づいてポートフォリオを最適化・生成する。**ステートレス** — 結果はDBに保存しない。

**Request Body**:
```json
{
  "risk_score": 7,
  "risk_tolerance": "moderate",
  "investment_horizon": "long",
  "strategy": "auto",
  "investment_amount": 1000000,
  "currency": "JPY",
  "constraints": {
    "max_single_asset_weight": 0.3,
    "include_markets": ["jp", "us"],
    "include_asset_types": ["etf", "bond", "reit"]
  }
}
```

**パラメータ説明**:
| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| risk_score | integer | YES | リスクスコア (1-10) |
| risk_tolerance | string | YES | リスク許容度 (conservative/moderate/aggressive) |
| investment_horizon | string | YES | 投資期間 (short/medium/long) |
| strategy | string | NO | 戦略指定。"auto"で自動選択 |
| investment_amount | integer | NO | 投資金額（円）。配分金額の計算に使用 |
| currency | string | NO | 表示通貨。デフォルト "JPY" |
| constraints | object | NO | 制約条件 |

**戦略自動選択ロジック**:
```
risk_tolerance → strategy:
  conservative → min_volatility
  moderate     → hrp
  aggressive   → max_sharpe
```

**Response 200**:
```json
{
  "name": "バランス型ポートフォリオ",
  "strategy": "hrp",
  "risk_profile": {
    "risk_score": 7,
    "risk_tolerance": "moderate"
  },
  "metrics": {
    "expected_return": 0.0682,
    "volatility": 0.1124,
    "sharpe_ratio": 0.5072
  },
  "allocations": [
    {
      "asset": {
        "symbol": "VTI",
        "name_ja": "バンガード・トータル・ストック・マーケットETF",
        "asset_type": "etf",
        "market": "us"
      },
      "weight": 0.2500,
      "amount": 250000
    },
    {
      "asset": {
        "symbol": "1306.T",
        "name_ja": "TOPIX連動型上場投資信託",
        "asset_type": "etf",
        "market": "jp"
      },
      "weight": 0.2000,
      "amount": 200000
    },
    {
      "asset": {
        "symbol": "BND",
        "name_ja": "バンガード・米国トータル債券市場ETF",
        "asset_type": "bond",
        "market": "us"
      },
      "weight": 0.2000,
      "amount": 200000
    },
    {
      "asset": {
        "symbol": "2511.T",
        "name_ja": "NEXT FUNDS 外国債券インデックス",
        "asset_type": "bond",
        "market": "jp"
      },
      "weight": 0.1500,
      "amount": 150000
    },
    {
      "asset": {
        "symbol": "VNQ",
        "name_ja": "バンガード・リアルエステートETF",
        "asset_type": "reit",
        "market": "us"
      },
      "weight": 0.1000,
      "amount": 100000
    },
    {
      "asset": {
        "symbol": "GLD",
        "name_ja": "SPDRゴールド・シェア",
        "asset_type": "etf",
        "market": "us"
      },
      "weight": 0.1000,
      "amount": 100000
    }
  ],
  "currency": "JPY"
}
```

---

#### POST /api/v1/portfolios/backtest

ポートフォリオ配分のバックテストを実行する。**ステートレス** — 配分データはリクエストボディで受信。

**Request Body**:
```json
{
  "allocations": [
    { "symbol": "VTI", "weight": 0.25 },
    { "symbol": "1306.T", "weight": 0.20 },
    { "symbol": "BND", "weight": 0.20 },
    { "symbol": "2511.T", "weight": 0.15 },
    { "symbol": "VNQ", "weight": 0.10 },
    { "symbol": "GLD", "weight": 0.10 }
  ],
  "period_years": 5,
  "initial_investment": 1000000,
  "rebalance_frequency": "quarterly"
}
```

**Response 200**:
```json
{
  "period": {
    "start": "2021-02-20",
    "end": "2026-02-20",
    "years": 5
  },
  "initial_investment": 1000000,
  "metrics": {
    "final_value": 1412000,
    "total_return": 0.412,
    "cagr": 0.0714,
    "volatility": 0.1089,
    "sharpe_ratio": 0.5231,
    "max_drawdown": -0.1823,
    "max_drawdown_period": {
      "start": "2022-01-03",
      "end": "2022-10-12"
    },
    "sortino_ratio": 0.7124,
    "calmar_ratio": 0.3917
  },
  "benchmark_comparison": {
    "nikkei225": {
      "total_return": 0.352,
      "cagr": 0.0623
    },
    "sp500": {
      "total_return": 0.521,
      "cagr": 0.0872
    }
  },
  "time_series": [
    { "date": "2021-02-22", "value": 1000000, "return_pct": 0.0 },
    { "date": "2021-02-23", "value": 1002300, "return_pct": 0.0023 },
    "..."
  ],
  "annual_returns": [
    { "year": 2021, "return": 0.1234 },
    { "year": 2022, "return": -0.0856 },
    { "year": 2023, "return": 0.1567 },
    { "year": 2024, "return": 0.0923 },
    { "year": 2025, "return": 0.1102 }
  ],
  "disclaimer": "※ 過去のパフォーマンスは将来の結果を保証するものではありません。バックテストは仮想的なシミュレーションであり、実際の取引コスト・税金は考慮されていません。"
}
```

---

#### POST /api/v1/portfolios/explain

AIによるポートフォリオ説明を生成する。**ステートレス** — ポートフォリオデータはリクエストボディで受信。

**Request Body**:
```json
{
  "strategy": "hrp",
  "risk_tolerance": "moderate",
  "allocations": [
    { "symbol": "VTI", "name_ja": "バンガード・トータル・ストック・マーケットETF", "weight": 0.25 },
    { "symbol": "1306.T", "name_ja": "TOPIX連動型上場投資信託", "weight": 0.20 },
    { "symbol": "BND", "name_ja": "バンガード・米国トータル債券市場ETF", "weight": 0.20 },
    { "symbol": "2511.T", "name_ja": "NEXT FUNDS 外国債券インデックス", "weight": 0.15 },
    { "symbol": "VNQ", "name_ja": "バンガード・リアルエステートETF", "weight": 0.10 },
    { "symbol": "GLD", "name_ja": "SPDRゴールド・シェア", "weight": 0.10 }
  ],
  "metrics": {
    "expected_return": 0.0682,
    "volatility": 0.1124,
    "sharpe_ratio": 0.5072
  }
}
```

**Response 200**:
```json
{
  "explanation": "このポートフォリオは「バランス型」の運用方針に基づいて構成されています。\n\n**配分の考え方**\n米国株式ETF（VTI: 25%）と日本株式ETF（TOPIX: 20%）を中心に、債券（BND: 20%、外国債券: 15%）で安定性を確保しています。また、REIT（VNQ: 10%）と金（GLD: 10%）を組み入れることで、インフレへの備えと分散効果を高めています。\n\n**リスクについて**\n年率ボラティリティは約11.2%で、最大下落幅は約18%程度が想定されます。100万円投資した場合、一時的に82万円程度まで下落する可能性があります。\n\n**重要な注意点**\n- これは教育目的の情報提供であり、投資助言ではありません\n- 投資にはリスクが伴い、元本を割り込む可能性があります\n- 実際の投資判断はご自身の責任で行ってください"
}
```

---

### 4.3 資産 (Assets)

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/assets/` | 資産一覧取得 |
| GET | `/api/v1/assets/{symbol}` | 資産詳細取得 |
| GET | `/api/v1/assets/{symbol}/prices` | 価格履歴取得 |

---

#### GET /api/v1/assets/

資産一覧を取得する。フィルタリング・ソート対応。

**Query Parameters**:
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| market | string | - | 市場フィルタ (jp/us) |
| asset_type | string | - | 資産タイプフィルタ (etf/bond/reit/stock) |
| search | string | - | 名称/シンボル検索 |
| page | integer | 1 | ページ番号 |
| per_page | integer | 20 | 1ページあたり件数 |

**Response 200**:
```json
{
  "items": [
    {
      "symbol": "VTI",
      "name": "Vanguard Total Stock Market ETF",
      "name_ja": "バンガード・トータル・ストック・マーケットETF",
      "asset_type": "etf",
      "market": "us",
      "currency": "USD",
      "sector": null,
      "latest_price": {
        "close": 285.42,
        "date": "2026-02-19",
        "change_pct": 0.0034
      }
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 20,
  "pages": 2
}
```

---

#### GET /api/v1/assets/{symbol}/prices

指定資産の価格履歴を取得する。

**Query Parameters**:
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| period | string | "1y" | 期間 (1m/3m/6m/1y/3y/5y/max) |
| interval | string | "daily" | 間隔 (daily/weekly/monthly) |

**Response 200**:
```json
{
  "symbol": "VTI",
  "period": "1y",
  "interval": "daily",
  "prices": [
    {
      "date": "2025-02-20",
      "open": 270.15,
      "high": 271.30,
      "low": 269.80,
      "close": 270.95,
      "adj_close": 270.95,
      "volume": 3245000
    }
  ],
  "data_source_note": "データは教育・情報提供目的です。投資判断の根拠として使用しないでください。"
}
```

---

### 4.4 マーケット情報 (Market)

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/market/summary` | マーケットサマリー |
| GET | `/api/v1/market/indicators` | 経済指標 |

---

#### GET /api/v1/market/summary

主要指標のサマリーを返す。ISRキャッシュ対象（1時間）。

**Response 200**:
```json
{
  "updated_at": "2026-02-20T07:00:00+09:00",
  "indices": {
    "nikkei225": {
      "value": 39245.50,
      "change_pct": 0.0082,
      "as_of": "2026-02-19"
    },
    "sp500": {
      "value": 6123.45,
      "change_pct": -0.0012,
      "as_of": "2026-02-19"
    }
  },
  "bonds": {
    "us_treasury_10y": {
      "value": 4.25,
      "unit": "%",
      "as_of": "2026-02-19"
    },
    "jp_govt_bond_10y": {
      "value": 1.05,
      "unit": "%",
      "as_of": "2026-02-19"
    }
  },
  "forex": {
    "usd_jpy": {
      "value": 150.23,
      "change_pct": -0.0015,
      "as_of": "2026-02-20"
    }
  },
  "disclaimer": "※ データは情報提供目的であり、リアルタイムではありません。"
}
```

---

### 4.5 チャット (Chat)

ステートレスなストリーミングチャット。FastAPIバックエンドでClaude APIを呼び出し、SSEで返却する。チャット履歴はページ内のみ（DB保存なし）。コスト制御のため、Claude API呼び出しはすべてバックエンドに集約する。

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/v1/chat` (FastAPI) | ストリーミングチャット (SSE) |

---

#### POST /api/v1/chat (FastAPI SSE)

anthropic Python SDK によるストリーミングチャット。予算チェック付き。

**Request Body**:
```json
{
  "messages": [
    { "role": "user", "content": "このポートフォリオのリスクを教えてください" }
  ],
  "portfolio_context": {
    "strategy": "hrp",
    "risk_tolerance": "moderate",
    "allocations": [
      { "symbol": "VTI", "name_ja": "バンガード・トータル・ストック・マーケットETF", "weight": 0.25 },
      { "symbol": "BND", "name_ja": "バンガード・米国トータル債券市場ETF", "weight": 0.20 }
    ],
    "metrics": { "expected_return": 0.0682, "volatility": 0.1124, "sharpe_ratio": 0.5072 }
  }
}
```

**Response**: Server-Sent Events (text/event-stream)
```
data: {"type":"text-delta","text":"この"}
data: {"type":"text-delta","text":"ポートフォリオ"}
data: {"type":"text-delta","text":"の"}
data: {"type":"text-delta","text":"リスク"}
...
data: {"type":"finish","usage":{"input_tokens":1250,"output_tokens":580}}
```

**処理フロー**:
```
1. リクエスト受信
2. UsageTracker: 日次/月次予算チェック → 超過時は429返却
3. システムプロンプト + portfolio_context からClaude APIリクエスト構築
4. anthropic SDK の client.messages.stream() でストリーミング呼び出し
5. StreamingResponse (text/event-stream) でクライアントにリレー
6. 完了後、UsageTracker: トークン数・推定コストをapi_usage_logsに記録
```

**予算超過時 (429)**:
```json
{
  "detail": "本日のAI利用上限に達しました。明日以降に再度お試しください。",
  "status_code": 429,
  "error_code": "DAILY_BUDGET_EXCEEDED"
}
```

**システムプロンプト概要**:
```
あなたは個人投資家向けの教育的なAIアドバイザーです。

ルール:
- 日本語で回答する
- 初心者にわかりやすい平易な表現を使う
- 具体的な売買タイミングの指示は絶対にしない
- リスクについて必ず言及する
- 「教育目的であり投資助言ではない」旨を適宜伝える
- ポートフォリオの配分理由を論理的に説明する
- 専門用語には簡単な説明を添える

コンテキスト:
- ユーザーのリスクプロファイル: {risk_profile}
- 現在のポートフォリオ: {portfolio_allocations}
- バックテスト結果: {backtest_summary}
```

### 4.6 利用状況 (Usage)

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/usage` | API利用状況・コスト確認 |

---

#### GET /api/v1/usage

Claude API利用量の日次/月次サマリーを返す。

**Response 200**:
```json
{
  "daily": {
    "date": "2026-02-20",
    "input_tokens": 45200,
    "output_tokens": 12800,
    "total_tokens": 58000,
    "estimated_cost_usd": 0.328,
    "budget_tokens": 100000,
    "remaining_tokens": 42000
  },
  "monthly": {
    "month": "2026-02",
    "input_tokens": 680000,
    "output_tokens": 195000,
    "total_tokens": 875000,
    "estimated_cost_usd": 4.97,
    "budget_tokens": 2000000,
    "remaining_tokens": 1125000
  }
}
```

---

## 5. Pydanticスキーマ一覧

### 5.1 リクエストスキーマ

```python
# Risk Assessment
class RiskAssessmentAnswer(BaseModel):
    question_id: int
    value: str

class RiskAssessmentCalculateRequest(BaseModel):
    answers: list[RiskAssessmentAnswer]  # min_length=8

# Portfolio
class PortfolioConstraints(BaseModel):
    max_single_asset_weight: float = 0.3
    include_markets: list[str] = ["jp", "us"]
    include_asset_types: list[str] = ["etf", "bond", "reit"]

class PortfolioGenerateRequest(BaseModel):
    risk_score: int                             # 1-10
    risk_tolerance: str                         # conservative/moderate/aggressive
    investment_horizon: str                     # short/medium/long
    strategy: str = "auto"
    investment_amount: int | None = None
    currency: str = "JPY"
    constraints: PortfolioConstraints | None = None

class AllocationInput(BaseModel):
    symbol: str
    weight: float

class BacktestRequest(BaseModel):
    allocations: list[AllocationInput]
    period_years: int = 5
    initial_investment: int = 1000000
    rebalance_frequency: str = "quarterly"

class ExplainAllocationInput(BaseModel):
    symbol: str
    name_ja: str | None = None
    weight: float

class ExplainRequest(BaseModel):
    strategy: str
    risk_tolerance: str
    allocations: list[ExplainAllocationInput]
    metrics: dict | None = None
```

### 5.2 レスポンススキーマ

```python
# Risk Assessment
class RiskAssessmentResponse(BaseModel):
    risk_score: int
    risk_tolerance: str
    investment_horizon: str
    investment_experience: str
    recommended_strategy: str | None
    description: str | None

# Portfolio
class AssetSummary(BaseModel):
    symbol: str
    name_ja: str | None
    asset_type: str
    market: str

class AllocationResponse(BaseModel):
    asset: AssetSummary
    weight: float
    amount: float | None

class PortfolioMetrics(BaseModel):
    expected_return: float | None
    volatility: float | None
    sharpe_ratio: float | None

class RiskProfileSummary(BaseModel):
    risk_score: int
    risk_tolerance: str

class PortfolioResponse(BaseModel):
    name: str | None
    strategy: str
    risk_profile: RiskProfileSummary
    metrics: PortfolioMetrics
    allocations: list[AllocationResponse]
    currency: str

# Backtest
class BacktestMetrics(BaseModel):
    final_value: float
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    sortino_ratio: float | None
    calmar_ratio: float | None

class BacktestResponse(BaseModel):
    period: dict
    initial_investment: float
    metrics: BacktestMetrics
    benchmark_comparison: dict | None
    time_series: list[dict]
    annual_returns: list[dict]
    disclaimer: str

# Explain
class ExplainResponse(BaseModel):
    explanation: str

# Pagination
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
```

---

## 6. エラーハンドリング方針

### 6.1 バリデーションエラー (422)

FastAPIのデフォルトPydanticエラーをカスタマイズ。

```json
{
  "detail": "入力値にエラーがあります",
  "status_code": 422,
  "errors": [
    {
      "field": "email",
      "message": "有効なメールアドレスを入力してください",
      "type": "value_error"
    }
  ]
}
```

### 6.2 ビジネスロジックエラー (400)

```json
{
  "detail": "ポートフォリオの生成に必要な価格データが不足しています。対象資産: VTI, BND",
  "status_code": 400,
  "error_code": "INSUFFICIENT_PRICE_DATA"
}
```

### 6.3 外部API障害 (503)

```json
{
  "detail": "市場データの取得に一時的に失敗しました。しばらく経ってからお試しください。",
  "status_code": 503,
  "retry_after": 60
}
```
