# システムアーキテクチャ設計書

## 1. ドキュメント情報

| 項目 | 内容 |
|------|------|
| プロジェクト名 | AI ポートフォリオ提案サービス (Portfolio Advisor) |
| バージョン | 1.0.0 (MVP) |
| 作成日 | 2026-02-20 |
| 最終更新 | 2026-02-20 (パターンB: ステートレス・オンデマンド生成型に変更) |
| 対象ユーザー | 個人投資家（初心者） ※ 個人/少人数利用前提 |

---

## 2. システム概要

### 2.1 サービス概要

日米の金融資産（株・ETF・債券・REIT）の市場データを収集し、ユーザーのリスク許容度に基づいてAIが最適なポートフォリオを提案するWebサービス。ユーザーはチャットインターフェースを通じてAIアドバイザーと対話し、ポートフォリオの詳細確認・調整を行える。

**利用規模: 個人/少人数（身内数人）利用前提**。一般公開は想定しない。コスト最小化を優先し、無料枠・スリープ機能を最大限活用する設計とする。

**設計思想: ステートレス・オンデマンド生成型（パターンB）**
- **ログイン不要**: 全ページ・全APIがパブリック。認証・ユーザー管理なし
- **リスク診断**: APIで計算し結果をレスポンスで返却。DBに保存しない。ブラウザ内でZustandにより一時保持
- **ポートフォリオ**: APIで都度生成し結果をレスポンスで返却。DBに保存しない。ブラウザ内で一時保持
- **チャット**: ステートレス。履歴はページ内のみ（ブラウザメモリ）
- **PostgreSQL**: マーケットデータキャッシュ専用（assets, asset_prices, economic_indicators の3テーブルのみ）

### 2.2 主要機能

| # | 機能 | 概要 |
|---|------|------|
| F1 | リスク診断 | 8問のアンケートでリスク許容度を数値化（ステートレス計算） |
| F2 | ポートフォリオ生成 | リスクスコアに基づく最適配分のオンデマンド算出 |
| F3 | バックテスト | 過去データによるパフォーマンスシミュレーション |
| F4 | AI説明・チャット | ポートフォリオの日本語説明生成とストリーミングチャット |
| F5 | マーケットデータ | 日米市場データの自動取得・表示 |

---

## 3. アーキテクチャ全体図

```
┌─────────────────────────────────────────────────────────┐
│                      クライアント                        │
│                  (ブラウザ / PWA)                        │
│              Zustand: 診断結果・ポートフォリオ一時保持      │
└──────────────┬──────────────────────────────────────────┘
               │
               │ HTTPS (REST + SSE)
               ▼
┌──────────────────────┐
│   Next.js Frontend   │
│   (Vercel Hobby/無料)│
│                      │
│ - App Router (SSR)   │
│ - shadcn/ui          │
│ - Recharts v3        │
│ - TanStack Query v5  │
│ - Zustand v5         │
│ ※ API Routeなし      │
│ ※ サーバーレス関数なし│
└──────────┬───────────┘
           │
           │ REST API (JSON)
           │ + SSE (チャット)
           │ (認証不要)
           ▼
┌──────────────────────────────────────────────┐
│      FastAPI Backend (Railway / スリープ対応)  │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │Asset API │ │ Risk API │ │ Portfolio API│ │
│  │/assets/* │ │ /risk/*  │ │ /portfolios/*│ │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
│       │             │              │         │
│  ┌────┴─────┐ ┌─────┴──────┐ ┌────┴───────┐ │
│  │Chat API  │ │ Usage API  │ │ Market API │ │
│  │/chat     │ │ /usage     │ │ /market/*  │ │
│  │(SSE)     │ │(コスト追跡) │ │            │ │
│  └────┬─────┘ └─────┬──────┘ └────────────┘ │
│       │             │                        │
│  ┌────▼─────────────▼──────────────────────┐ │
│  │            サービス層                     │ │
│  │                                         │ │
│  │  ┌─────────────┐  ┌──────────────────┐  │ │
│  │  │ RiskProfiler│  │PortfolioOptimizer│  │ │
│  │  │ (スコア計算) │  │ (PyPortfolioOpt) │  │ │
│  │  └─────────────┘  └──────────────────┘  │ │
│  │  ┌─────────────┐  ┌──────────────────┐  │ │
│  │  │ Backtester  │  │   AI Advisor     │  │ │
│  │  │ (シミュレーション)│ │ (Claude API)  │  │ │
│  │  └─────────────┘  └──────────────────┘  │ │
│  │  ┌─────────────────┐ ┌───────────────┐  │ │
│  │  │  UsageTracker   │ │ Data Pipeline │  │ │
│  │  │  (コスト制御)    │ │ (手動/CLI)    │  │ │
│  │  └─────────────────┘ └───────────────┘  │ │
│  └─────────────────────────────────────────┘ │
│                      │                       │
│              ┌───────▼──────┐                │
│              │  PostgreSQL  │                │
│              │  (Railway)   │                │
│              │  ※市場データ  │                │
│              │  キャッシュ    │                │
│              │  + API利用ログ │                │
│              └──────────────┘                │
└──────────────────────────────────────────────┘

           外部データソース
┌──────────┬──────────┬──────────┬──────────────┐
│ yfinance │ J-Quants │ FRED API │ExchangeRate  │
│ (米国)   │ (日本)   │ (債券)   │.host (為替)  │
└──────────┴──────────┴──────────┴──────────────┘

           定期データ更新（サーバー常時起動不要）
┌──────────────────────────────────────────────┐
│  GitHub Actions cron（オプション）             │
│  または手動CLI: make update-market-data       │
└──────────────────────────────────────────────┘
```

---

## 4. コンポーネント詳細

### 4.1 Frontend (Next.js 16)

| 項目 | 詳細 |
|------|------|
| フレームワーク | Next.js 16 (App Router) |
| 言語 | TypeScript 5.x |
| UIライブラリ | shadcn/ui + Tailwind CSS v4 |
| チャート | Recharts v3 |
| 状態管理 | Zustand v5 (クライアント状態 + 計算結果の一時保持) + TanStack Query v5 (サーバー状態) |
| ホスティング | Vercel (Hobbyプラン/無料) |

**責務**:
- SSR/SSGによるSEO最適化されたページレンダリング
- ユーザーインターフェース（リスク診断ウィザード、ポートフォリオ表示、チャート）
- リスク診断結果・ポートフォリオ生成結果のブラウザ内一時保持（Zustand）
- チャットのストリーミング表示（FastAPIバックエンドのSSEエンドポイントを`fetch + ReadableStream`で消費）
- PWA対応（オフライン時の基本表示）

**※ Next.js API Routeは使用しない**（サーバーレス関数を排除し、Vercel Hobbyプラン無料枠で運用するため）

### 4.2 Backend (FastAPI)

| 項目 | 詳細 |
|------|------|
| フレームワーク | FastAPI 0.129+ |
| 言語 | Python 3.13 |
| ORM | SQLAlchemy 2.0 (async) |
| マイグレーション | Alembic |
| 最適化 | PyPortfolioOpt |
| パッケージ管理 | uv |
| ホスティング | Railway (Docker, スリープ対応) |

**責務**:
- REST APIの提供（資産、リスク計算、ポートフォリオ生成、マーケット）
- **ストリーミングチャットAPI**（SSEエンドポイント、Claude API呼び出しを一元管理）
- ビジネスロジック（リスクスコアリング、ポートフォリオ最適化、バックテスト）
- 外部データソースからのデータ取得・保存（市場データキャッシュ）
- AI Advisorによるポートフォリオ説明生成
- **API利用量追跡・コスト制御**（日次/月次予算上限）
- 市場データ更新（手動CLIコマンド or GitHub Actions cron）

### 4.3 Database (PostgreSQL)

| 項目 | 詳細 |
|------|------|
| DBMS | PostgreSQL 16 |
| 接続 | asyncpg (非同期ドライバ) |
| ホスティング | Railway Managed PostgreSQL |

**責務**:
- 資産マスタ・価格時系列データのキャッシュ（市場データ専用）
- 経済指標データの保管
- **API利用量ログの保管**（Claude API呼び出しのトークン数・コスト追跡）
- ※ ユーザーデータ、リスク診断結果、ポートフォリオ、チャット履歴はDBに保存しない

### 4.4 外部サービス

| サービス | 用途 | 認証 | レート制限 |
|----------|------|------|-----------|
| Anthropic Claude API | AI説明生成・チャット | API Key | RPM制限あり |
| yfinance | 米国株/ETF価格 | 不要 | SLA無し（キャッシュ必須） |
| J-Quants API | 日本株/ETF価格 | ID/Password→トークン | 無料プラン制限あり |
| FRED API | 債券利回り | API Key | 無制限 |
| ExchangeRate.host | 為替レート | 不要 | 制限緩い |

---

## 5. 通信設計

### 5.1 フロントエンド → バックエンド

```
プロトコル: HTTPS
フォーマット: JSON (application/json)
認証: 不要（全エンドポイントがパブリック）
CORS: frontend origin のみ許可

リクエストフロー:
1. クライアント → Next.js (SSR/CSR)
2. Next.js (or クライアント直接) → FastAPI Backend (REST API)
3. FastAPI → PostgreSQL (asyncpg) ※市場データのみ
4. FastAPI → 外部API (httpx async)

※ プロキシパターン不要。フロントエンドからFastAPIへ直接リクエスト。
```

### 5.2 チャットストリーミング

```
1. クライアント → FastAPI Backend (POST /api/v1/chat)
   - POST { messages[], portfolio_context }
   - portfolio_context はリクエストボディで直接受信（ブラウザ内保持データ）
2. FastAPI → UsageTracker（予算チェック）
   - 日次/月次上限を確認。超過時は 429 エラー返却。
3. FastAPI → Anthropic Claude API
   - anthropic Python SDKでストリーミングリクエスト
4. Anthropic → FastAPI → クライアント
   - StreamingResponse (text/event-stream)
5. FastAPI → UsageTracker（利用量記録）
   - トークン数・コストをapi_usage_logsに保存

※ チャットはFastAPIバックエンドを経由（Claude API呼び出しの一元管理・コスト追跡のため）。
  フロントエンドはfetch + ReadableStreamでSSEを消費。
  Next.js API Routeは使用しない（Vercel Hobby無料枠で運用するため）。
  チャット履歴はページ内のみ（DB保存なし）。
```

### 5.3 データパイプライン

```
手動実行 or GitHub Actions cron（サーバー常時起動不要）:

┌──────────────────────────────────────────────────────────┐
│ 方法A: 手動CLI                                           │
│   make update-market-data                                │
│                                                          │
│ 方法B: GitHub Actions cron (オプション)                    │
│   .github/workflows/update-market-data.yml               │
│   schedule: "0 22 * * 1-5" (UTC 22:00 = JST 7:00)       │
│   → Railway CLI or API経由でバックエンドのCLIコマンドを実行  │
└────────┬─────────────────────────────────────────────────┘
         │
    ┌────▼────┐   ┌────────────┐   ┌──────────┐
    │yfinance │   │ J-Quants   │   │ FRED     │
    │fetcher  │   │ fetcher    │   │ fetcher  │
    └────┬────┘   └─────┬──────┘   └────┬─────┘
         │              │               │
         └──────────────▼───────────────┘
                        │
                 ┌──────▼──────┐
                 │ PostgreSQL  │
                 │ asset_prices│
                 │ econ_indic. │
                 └─────────────┘

※ APSchedulerは使用しない（サーバー常時起動が不要になり、
  Railwayのスリープ機能でコスト削減可能）
```

---

## 6. 技術選定理由

### 6.1 FastAPI (Backend)

| 検討した選択肢 | 選定結果 | 理由 |
|---------------|---------|------|
| FastAPI | **採用** | async対応、型安全(Pydantic)、金融Pythonライブラリとの親和性、自動OpenAPIドキュメント |
| Django REST | 不採用 | 非同期対応が不十分、オーバーヘッドが大きい |
| Express.js | 不採用 | Python金融ライブラリ(PyPortfolioOpt, pandas)が使えない |

### 6.2 Next.js 16 (Frontend)

| 検討した選択肢 | 選定結果 | 理由 |
|---------------|---------|------|
| Next.js 16 | **採用** | App Router成熟、Turbopack安定、Vercel AI SDK v6統合、Build Adapters API |
| Remix | 不採用 | Vercel AI SDKとの統合が限定的 |
| SPA (Vite + React) | 不採用 | SEO不利、SSR手動構築が必要 |

### 6.3 PostgreSQL (Database)

| 検討した選択肢 | 選定結果 | 理由 |
|---------------|---------|------|
| PostgreSQL | **採用** | 堅牢、時系列データに十分、Railway managed、SQLAlchemy完全対応 |
| TimescaleDB | 不採用 | 日次データ程度ならPostgreSQL標準で十分 |
| MongoDB | 不採用 | リレーション多数、ACID保証が重要 |

### 6.4 PyPortfolioOpt (最適化)

| 検討した選択肢 | 選定結果 | 理由 |
|---------------|---------|------|
| PyPortfolioOpt | **採用** | MVO/HRP/リスクパリティ対応、Ledoit-Wolf縮約、成熟ライブラリ |
| scipy.optimize直接 | 不採用 | 制約条件の手動実装が煩雑 |
| Riskfolio-Lib | 不採用 | 機能過多、学習コスト高 |

### 6.5 チャットストリーミング

| 検討した選択肢 | 選定結果 | 理由 |
|---------------|---------|------|
| FastAPI SSE + anthropic SDK | **採用** | Claude API呼び出しの一元管理、コスト追跡が容易、Vercel無料枠で運用可能 |
| Vercel AI SDK v6 (Next.js API Route) | 不採用 | Vercel Hobbyの10秒タイムアウトでSSEが中断するリスク、API Keyが2箇所に分散しコスト追跡困難 |
| LangChain | 不採用 | オーバーヘッド大、単純なチャットには過剰 |

---

## 7. セキュリティ設計

### 7.1 概要

本サービスは認証なし（全エンドポイントがパブリック）のため、認証・認可のセキュリティは対象外。
以下の対策で、公開APIとしてのセキュリティを確保する。

### 7.2 データ保護

| 対象 | 対策 |
|------|------|
| API Key（外部サービス） | 環境変数管理、コードにハードコード禁止 |
| DB接続 | SSL/TLS接続必須 |
| CORS | フロントエンドオリジンのみ許可 |
| 入力検証 | Pydanticスキーマによるバリデーション |
| SQLインジェクション | SQLAlchemy ORM利用（パラメタライズドクエリ） |
| XSS | React自動エスケープ + CSPヘッダー |
| コスト制御 | Claude API呼び出しの日次/月次トークン予算上限（UsageTracker） |

### 7.3 環境変数一覧

```
環境変数一覧:

Backend (FastAPI / Railway):
├── ANTHROPIC_API_KEY          # Claude API（バックエンドのみ。フロントエンドには不要）
├── JQUANTS_EMAIL              # J-Quants認証
├── JQUANTS_PASSWORD           # J-Quants認証
├── FRED_API_KEY               # FRED API
├── DATABASE_URL               # PostgreSQL接続文字列
├── DAILY_TOKEN_BUDGET         # Claude API 日次トークン上限（例: 100000）
└── MONTHLY_TOKEN_BUDGET       # Claude API 月次トークン上限（例: 2000000）

Frontend (Next.js / Vercel):
└── NEXT_PUBLIC_API_URL        # FastAPI バックエンドURL
```

---

## 8. デプロイ構成

### 8.1 本番環境

```
┌────────────────┐     ┌────────────────────┐
│   Vercel       │     │   Railway          │
│   (Hobby/無料) │     │                    │
│                │     │ ┌──────────┐       │
│ ┌──────────┐   │     │ │ FastAPI  │       │
│ │ Next.js  │   │────▶│ │ Backend  │       │
│ │ Frontend │   │     │ │+チャットSSE│      │
│ └──────────┘   │     │ │+コスト追跡│       │
│                │     │ └────┬─────┘       │
│ Edge Network   │     │      │ スリープ対応 │
│ (CDN)          │     │ ┌────▼─────┐       │
│                │     │ │PostgreSQL│       │
│ ※API Route無し │     │ │ Managed  │       │
└────────────────┘     │ └──────────┘       │
                       └────────────────────┘

コスト目安（個人/少人数利用）:
  Vercel Hobby:   $0/月（無料）
  Railway:        $5-10/月（スリープ活用）
  Claude API:     $5-20/月（予算上限で制御）
  合計:           $10-30/月
```

### 8.2 開発環境

```
docker-compose.yml:
├── backend   (FastAPI + uvicorn, port 8000)
├── frontend  (Next.js dev server, port 3000)
└── db        (PostgreSQL 16, port 5432)

ローカル開発:
$ make dev                  # docker-compose up
$ make test                 # テスト実行
$ make migrate              # DBマイグレーション
$ make seed                 # シードデータ投入
$ make update-market-data   # 市場データ手動更新
```

---

## 9. 非機能要件

### 9.1 パフォーマンス

| 指標 | 目標値 |
|------|--------|
| ページ初回表示 | < 2秒 (LCP) |
| API レスポンス | < 500ms (p95) |
| ポートフォリオ最適化 | < 3秒 |
| バックテスト | < 5秒 |
| チャット初回レスポンス | < 1秒 (TTFB) |

### 9.2 スケーラビリティ

| 項目 | 個人/少人数想定 | 将来拡張（一般公開時） |
|------|---------------|---------------------|
| 同時ユーザー数 | ~5 | Railway水平スケール |
| DB接続数 | 5 (connection pool) | pgBouncer導入 |
| データ量 | ~50銘柄 × 5年分日次 | パーティショニング |
| Claude API予算 | 日次10万トークン / 月次200万トークン | Anthropic Console上限設定 |

### 9.3 可用性

| 項目 | 目標 |
|------|------|
| SLA | 99.5% (MVP) |
| ダウンタイム | メンテナンス時のみ |
| バックアップ | Railway自動バックアップ (日次) |
| 災害復旧 | マイグレーション + シードスクリプトから復元可能 |

### 9.4 監視・ログ

| 項目 | ツール |
|------|--------|
| アプリログ | Python logging → stdout → Railway Logs |
| フロントエンド | Vercel Analytics (無料枠) |
| エラー監視 | 将来: Sentry (MVP外) |
| ヘルスチェック | GET /api/v1/health |
| API利用量 | GET /api/v1/usage（日次/月次トークン消費状況） |
