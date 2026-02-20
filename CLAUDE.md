# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## 技術方針

**常に各ライブラリ・フレームワークの最新バージョンおよび最新のベストプラクティスを使用すること。** 実装時はContext7 MCPやWebSearchで最新ドキュメントを確認し、非推奨APIや旧パターンの使用を避ける。設計書に記載のバージョン（Next.js 16, Tailwind CSS v4, Recharts v3, Zustand v5, TanStack Query v5, SQLAlchemy 2.0等）はベースラインであり、より新しい安定版がある場合はそちらを採用する。

**フロントエンドのパッケージマネージャーは Bun を使用すること。** `npm` / `yarn` / `pnpm` ではなく、`bun install`, `bun run`, `bun add` 等のBunコマンドを使う。

## プロジェクト概要

AIポートフォリオ提案サービス — 日米の金融資産マーケットデータを収集し、ユーザーのリスク許容度に基づいてAIが最適なポートフォリオを提案するWebサービス。チャットインターフェースでAIアドバイザーと対話可能。

**利用想定**: 個人または身内数人での利用（一般公開しない前提）。コスト最小化を最優先とする。

**設計思想: ステートレス・オンデマンド生成型**
- ログイン不要、認証なし、全エンドポイントがパブリック
- リスク診断結果・ポートフォリオはDBに保存せず、ブラウザ内（Zustand）で一時保持
- PostgreSQLは市場データキャッシュ＋API利用量追跡（4テーブル）

**言語**: UI・ユーザー向けコンテンツはすべて日本語。

## アーキテクチャ

```
portfolio-advisor/
├── backend/     # FastAPI (Python 3.13, uv)
├── frontend/    # Next.js 16 (TypeScript, App Router)
└── docker-compose.yml
```

### バックエンド (FastAPI → Railway)
- **Python 3.13**, パッケージ管理: **uv**
- **FastAPI 0.129+** (async) + **Pydantic v2** スキーマ
- **SQLAlchemy 2.0** (async) + **asyncpg** + **Alembic** マイグレーション
- **PyPortfolioOpt**: ポートフォリオ最適化（MVO, HRP, Max Sharpe, Risk Parity）
- **anthropic** (Python SDK): チャットSSEストリーミング + AI説明生成
- **UsageTracker**: 日次/月次トークン予算によるClaude APIコスト制御
- PostgreSQL 16 は市場データキャッシュ + API利用量追跡（`assets`, `asset_prices`, `economic_indicators`, `api_usage_logs`）
- 市場データ取得: 手動CLIコマンド + GitHub Actions cron（APScheduler不使用）
- ユーザーテーブル・認証ミドルウェア・セッション保存なし

### フロントエンド (Next.js → Vercel Hobbyプラン/無料)
- **Next.js 16** App Router, **TypeScript 5.x**
- **shadcn/ui** (radix-ui) + **Tailwind CSS v4**
- **Recharts v3** (円グラフ、折れ線グラフ)
- **Zustand v5**: クライアント状態（リスク診断結果、ポートフォリオ結果のブラウザ内一時保持）
- **TanStack Query v5**: サーバー状態（資産データ、マーケットデータ）
- **API Routeなし**: チャット含む全APIコールはFastAPIバックエンドへ直接リクエスト

### 設計上の重要な判断
- **ステートレス**: リスクスコア・ポートフォリオはオンデマンド計算、レスポンスで返却、DB保存なし
- **プロキシなし**: フロントエンドからFastAPIへ直接リクエスト（CORS設定済み）
- **チャットはFastAPI経由**: POST `/api/v1/chat` → UsageTracker予算チェック → Claude API (SSE) → クライアントへストリーム
- **DBはキャッシュ＋追跡**: 市場データキャッシュ + Claude API利用量ログ
- **コスト制御優先**: Vercel Hobbyプラン（無料）、Railway（スリープ可）、トークン予算制限

## 主要コマンド

```bash
# 開発環境 (Docker)
make dev              # docker-compose up (backend:8000, frontend:3000, db:5432)
make dev-backend      # cd backend && uvicorn src.app.main:app --reload
make dev-frontend     # cd frontend && bun run dev

# テスト
make test             # 全テスト実行
make test-backend     # cd backend && pytest
make test-frontend    # cd frontend && bun test

# リント
make lint             # ruff check (backend) + eslint (frontend)

# データベース
make migrate          # alembic upgrade head
make migrate-down     # alembic downgrade -1
make migration msg="説明"  # alembic revision --autogenerate
make seed             # python -m src.app.scripts.seed

# 市場データ更新（手動CLI）
make update-market-data   # python -m src.app.cli update-market-data

# バックエンド単体テスト
cd backend && pytest tests/test_risk_assessment.py -v
cd backend && pytest tests/test_portfolio.py::test_hrp_optimization -v
```

## バックエンド構造

```
backend/src/app/
├── main.py                          # FastAPIエントリポイント、CORS、ルーターマウント
├── core/
│   ├── config.py                    # Pydantic BaseSettings（環境変数管理）
│   └── database.py                  # async engine, sessionmaker, get_db()
├── models/                          # SQLAlchemy 2.0 モデル（4テーブル）
│   ├── asset.py                     # assets（シンボル、タイプ、市場）
│   ├── asset_price.py               # asset_prices（OHLCV日次データ）
│   ├── economic_indicator.py        # economic_indicators（債券利回り、為替）
│   └── api_usage_log.py             # api_usage_logs（Claude APIコスト追跡）
├── schemas/                         # Pydantic v2 リクエスト/レスポンススキーマ
├── crud/                            # DBクエリ関数
├── api/v1/
│   ├── router.py                    # 全エンドポイントルーターの集約
│   └── endpoints/
│       ├── health.py                # GET /api/v1/health
│       ├── assets.py                # GET /api/v1/assets/, /assets/{symbol}/prices
│       ├── market.py                # GET /api/v1/market/summary, /indicators
│       ├── risk_assessment.py       # GET 質問一覧, POST スコア計算（ステートレス）
│       ├── portfolios.py            # POST 生成, バックテスト, AI説明（全てステートレス）
│       ├── chat.py                  # POST /api/v1/chat（SSEストリーミング）
│       └── usage.py                 # GET /api/v1/usage（利用量サマリー）
├── services/
│   ├── risk_profiler.py             # 8問リスク診断スコアリング（1-10スケール）
│   ├── portfolio_optimizer.py       # PyPortfolioOpt最適化エンジン（最重要ファイル）
│   ├── backtester.py                # ヒストリカルバックテストシミュレーション
│   ├── ai_advisor.py                # Claude APIによる説明生成
│   ├── usage_tracker.py             # 日次/月次トークン予算管理・コスト計算
│   └── data_pipeline/
│       ├── yfinance_fetcher.py      # 米国市場データ取得
│       ├── jquants.py               # 日本市場データ取得
│       ├── fred.py                  # 債券利回り（FRED API）
│       ├── exchange_rate.py         # 為替レート
│       └── coordinator.py           # 全fetcher統合制御
└── cli.py                           # typer/clickベースCLIコマンド（市場データ更新等）
```

### APIエンドポイント一覧（全てパブリック、認証不要）
| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/health` | ヘルスチェック |
| GET | `/api/v1/risk-assessment/questions` | リスク診断質問一覧 |
| POST | `/api/v1/risk-assessment/calculate` | リスクスコア計算（ステートレス） |
| POST | `/api/v1/portfolios/generate` | ポートフォリオ生成（ステートレス） |
| POST | `/api/v1/portfolios/backtest` | バックテスト実行（ステートレス） |
| POST | `/api/v1/portfolios/explain` | AI説明生成（ステートレス） |
| GET | `/api/v1/assets/` | 資産一覧（フィルタリング対応） |
| GET | `/api/v1/assets/{symbol}/prices` | 価格履歴 |
| GET | `/api/v1/market/summary` | マーケット概要 |
| POST | `/api/v1/chat` | チャットSSEストリーミング（予算チェック付き） |
| GET | `/api/v1/usage` | API利用量サマリー（日次/月次） |

## フロントエンド構造

```
frontend/src/
├── app/                             # Next.js App Routerページ
│   ├── layout.tsx                   # ルートレイアウト（Noto Sans JP, lang="ja", プロバイダー）
│   ├── page.tsx                     # ランディングページ (/)
│   ├── risk-assessment/
│   │   ├── page.tsx                 # 8問ウィザード (/risk-assessment)
│   │   └── result/page.tsx          # 診断結果表示 (/risk-assessment/result)
│   ├── portfolio/page.tsx           # ポートフォリオ詳細・タブ表示 (/portfolio)
│   ├── chat/page.tsx                # AIチャット (/chat)
│   └── market/page.tsx              # マーケット情報 (/market)
├── components/
│   ├── ui/                          # shadcn/ui プリミティブ
│   ├── layout/                      # header, footer, disclaimer-banner
│   ├── risk-assessment/             # question-step, score-gauge, progress
│   ├── portfolio/                   # allocation-chart, backtest-chart, metrics
│   ├── chat/                        # message-bubble, chat-input, suggestions, usage-banner
│   └── market/                      # market-summary-card
├── stores/                          # Zustand v5 ストア
│   ├── risk-assessment-store.ts     # ウィザード状態 + 診断結果（ブラウザ内のみ）
│   └── portfolio-result-store.ts    # 生成結果 + バックテスト（ブラウザ内のみ）
├── hooks/                           # カスタムフック
│   └── use-stream-chat.ts           # FastAPI SSEチャット接続フック
├── lib/
│   ├── api-client.ts                # FastAPIクライアント（streamChat(), getUsage()含む）
│   └── utils.ts
└── types/                           # APIスキーマに対応するTypeScript型定義
```

## 環境変数

```
# バックエンド専用
ANTHROPIC_API_KEY       # Claude API（バックエンドのみ。チャット・AI説明両方で使用）
JQUANTS_EMAIL           # J-Quants API認証
JQUANTS_PASSWORD        # J-Quants API認証
FRED_API_KEY            # FRED経済データAPI
DATABASE_URL            # PostgreSQL (postgresql+asyncpg://...)
DAILY_TOKEN_BUDGET      # Claude API日次トークン上限
MONTHLY_TOKEN_BUDGET    # Claude API月次トークン上限

# フロントエンド
NEXT_PUBLIC_API_URL     # FastAPIバックエンドURL (例: http://localhost:8000)
```

## データフロー

1. **リスク診断**: フロントエンドウィザード → POST `/api/v1/risk-assessment/calculate` → スコア返却（DB保存なし）
2. **ポートフォリオ生成**: スコア＋設定 → POST `/api/v1/portfolios/generate` → PyPortfolioOpt最適化 → 配分返却（DB保存なし）
3. **バックテスト**: 配分データ → POST `/api/v1/portfolios/backtest` → ヒストリカルシミュレーション → メトリクス返却
4. **チャット**: メッセージ＋Zustandのポートフォリオコンテキスト → POST `/api/v1/chat` (FastAPI) → UsageTracker予算チェック → Claude API SSEストリーム → ブラウザ表示
5. **市場データ更新**: 手動CLIコマンド or GitHub Actions cron → fetcher群 (yfinance, J-Quants, FRED, ExchangeRate) → PostgreSQLキャッシュ

## 実装フェーズ

`docs/05_implementation_plan.md` に定義された5フェーズ:
1. **基盤構築**: プロジェクトセットアップ、DBモデル、データパイプライン、CLIコマンド、基本API
2. **ポートフォリオエンジン**: リスク診断、ポートフォリオ最適化 (PyPortfolioOpt)、バックテスト
3. **AI統合**: UsageTracker、チャットSSE（FastAPI）、ポートフォリオ説明生成、利用量API
4. **フロントエンド**: 全ページ・コンポーネント
5. **仕上げ**: コンプライアンス免責表示、パフォーマンス最適化、PWA、テスト、デプロイ

## 技術上の重要事項

- `portfolio_optimizer.py` が最も複雑なバックエンドファイル — PyPortfolioOptのLedoit-Wolf縮約による共分散推定を使用
- リスクスコア: 1-10スケール、conservative (1-3) / moderate (4-7) / aggressive (8-10) に分類
- 戦略自動選択: conservative→min_volatility, moderate→HRP, aggressive→max_sharpe
- 金融免責事項を全ページに表示必須（教育目的であり投資助言ではない旨）
- MVP対象資産は約50銘柄（日本ETF、米国ETF、債券、REIT）を手動シード
- コスト制御: UsageTrackerによる日次/月次トークン予算管理、予算超過時は429エラー返却
- デプロイ: Vercel Hobbyプラン（無料）、Railway（$5〜/月、スリープ可）、月額目安$10-30
