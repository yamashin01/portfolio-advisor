# Portfolio Advisor

AIポートフォリオ提案サービス — 日米の金融資産マーケットデータを収集し、ユーザーのリスク許容度に基づいてAIが最適なポートフォリオを提案するWebサービス。

## 機能

- **リスク診断**: 8問の質問によるリスク許容度スコアリング（1-10スケール）
- **ポートフォリオ最適化**: PyPortfolioOptによる複数戦略（Max Sharpe, HRP, Min Volatility, Risk Parity, Equal Weight）
- **バックテスト**: ヒストリカルデータに基づくパフォーマンスシミュレーション
- **AIチャット**: Claude APIによるポートフォリオ相談（SSEストリーミング）
- **マーケット情報**: 日米市場の主要指標・資産価格一覧

## 技術スタック

### バックエンド
- Python 3.13 / FastAPI / SQLAlchemy 2.0 (async)
- PostgreSQL 16 (asyncpg)
- PyPortfolioOpt / Pandas / NumPy
- Anthropic Python SDK (Claude API)
- パッケージ管理: uv

### フロントエンド
- Next.js 16 (App Router) / TypeScript
- shadcn/ui (Radix UI) / Tailwind CSS v4
- Recharts v3 / Zustand v5 / TanStack Query v5
- パッケージ管理: Bun

### インフラ
- バックエンド: Railway
- フロントエンド: Vercel (Hobbyプラン)
- DB: PostgreSQL (Railway)

## アーキテクチャ

```
portfolio-advisor/
├── backend/          # FastAPI
├── frontend/         # Next.js 16
├── docs/             # 設計書
└── docker-compose.yml
```

**設計思想: ステートレス・オンデマンド生成型**
- 認証なし（個人利用前提）
- リスク診断結果・ポートフォリオはDBに保存せず、ブラウザ内（Zustand）で一時保持
- PostgreSQLは市場データキャッシュ + API利用量追跡のみ（4テーブル）

## セットアップ

### 前提条件

- Python 3.13+
- Node.js 20+ / Bun
- PostgreSQL 16
- uv (Pythonパッケージマネージャー)

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd portfolio-advisor
```

### 2. 環境変数の設定

プロジェクトルートに `.env` を作成:

```env
# Database
DATABASE_URL=postgresql+asyncpg://<user>@localhost:5432/portfolio_advisor

# External APIs
ANTHROPIC_API_KEY=sk-ant-xxxxx
JQUANTS_EMAIL=your-email@example.com
JQUANTS_PASSWORD=your-password
FRED_API_KEY=your-fred-api-key

# Claude API Budget
DAILY_TOKEN_BUDGET=100000
MONTHLY_TOKEN_BUDGET=2000000

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. データベースの準備

```bash
createdb portfolio_advisor
```

### 4. バックエンドのセットアップ

```bash
cd backend
ln -sf ../.env .env        # .envをシンボリックリンク
uv sync                    # 依存パッケージのインストール
uv run alembic upgrade head  # マイグレーション実行
uv run python -m src.app.cli seed  # 初期データ投入（資産マスタ）
```

### 5. フロントエンドのセットアップ

```bash
cd frontend
bun install
```

### 6. 市場データの取得

```bash
cd backend
uv run python -m src.app.cli update-us-prices  # 米国市場データ
# uv run python -m src.app.cli update-jp-prices  # 日本市場データ（J-Quants APIキー必要）
```

## 開発サーバーの起動

### Docker Compose（推奨）

```bash
docker-compose up
```

- バックエンド: http://localhost:8000
- フロントエンド: http://localhost:3000
- PostgreSQL: localhost:5432

### 個別起動

```bash
# バックエンド
cd backend
uv run uvicorn src.app.main:app --reload --port 8000

# フロントエンド（別ターミナル）
cd frontend
bun run dev
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/health` | ヘルスチェック |
| GET | `/api/v1/risk-assessment/questions` | リスク診断質問一覧 |
| POST | `/api/v1/risk-assessment/calculate` | リスクスコア計算 |
| POST | `/api/v1/portfolios/generate` | ポートフォリオ生成 |
| POST | `/api/v1/portfolios/backtest` | バックテスト実行 |
| POST | `/api/v1/portfolios/explain` | AI説明生成 |
| GET | `/api/v1/assets/` | 資産一覧 |
| GET | `/api/v1/assets/{symbol}/prices` | 価格履歴 |
| GET | `/api/v1/market/summary` | マーケット概要 |
| POST | `/api/v1/chat` | AIチャット（SSE） |
| GET | `/api/v1/usage` | API利用量サマリー |

## データフロー

1. **リスク診断**: 8問ウィザード → スコア計算（1-10） → 戦略自動選択
2. **ポートフォリオ生成**: リスクスコア + 設定 → PyPortfolioOpt最適化 → 配分返却
3. **バックテスト**: 配分データ → ヒストリカルシミュレーション → メトリクス返却
4. **チャット**: メッセージ → FastAPI → UsageTracker予算チェック → Claude API (SSE) → ブラウザ

## コスト管理

- Claude APIの日次/月次トークン予算を `DAILY_TOKEN_BUDGET` / `MONTHLY_TOKEN_BUDGET` で制御
- 予算超過時は429エラーを返却
- GET `/api/v1/usage` で現在の利用量を確認可能

## デプロイ

Railway + Vercel へのデプロイ手順は [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) を参照。

## 免責事項

本サービスは教育・情報提供目的であり、投資助言ではありません。投資判断はご自身の責任で行ってください。
