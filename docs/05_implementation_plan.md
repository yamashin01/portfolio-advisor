# 実装計画書

## 1. 概要

本書は AI ポートフォリオ提案サービスの実装をファイル単位で詳細に分解し、依存関係と実装順序を定義する。各タスクには前提条件・成果物・検証方法を明記する。

---

## 2. フェーズ構成と依存関係

```
Phase 1: 基盤構築
├── 1.1 プロジェクトセットアップ ──────────────────┐
├── 1.2 DB + モデル + マイグレーション ─(1.1に依存)─┤
├── 1.3 データパイプライン ─────(1.2に依存)────────┤
└── 1.4 基本API ───────────────(1.2に依存)────────┘
                                                   │
Phase 2: ポートフォリオエンジン ◀───────────────────┘
├── 2.1 リスク診断 ────────────(1.4に依存)─────────┐
├── 2.2 ポートフォリオ最適化 ──(1.3, 2.1に依存)────┤
└── 2.3 バックテスト ──────────(2.2に依存)─────────┘
                                                   │
Phase 3: AI統合 + コスト制御 ◀─────────────────────┘
├── 3.1 ポートフォリオ説明生成 ─(2.2に依存)
└── 3.2 チャットSSE + UsageTracker ─(3.1, 1.2に依存)
                                                   │
Phase 4: フロントエンド ◀──────────────────────────┘
├── 4.1 プロジェクトセットアップ ─(1.1と並行可) ──┐
├── 4.2 レイアウト + 共通コンポーネント ─(4.1)────┤
├── 4.3 リスク診断ウィザード ─(4.2, 2.1に依存)────┤
├── 4.4 ポートフォリオ詳細 ──(4.2, 2.2, 2.3に依存)┤
├── 4.5 チャットUI ──────────(4.2, 3.2に依存)─────┤
└── 4.6 その他ページ ────────(4.2に依存)──────────┘
                                                   │
Phase 5: 仕上げ + ローンチ ◀───────────────────────┘
├── 5.1 コンプライアンス
├── 5.2 パフォーマンス最適化
├── 5.3 PWA対応
├── 5.4 テスト
└── 5.5 デプロイ
```

---

## 3. Phase 1: 基盤構築

### 1.1 プロジェクトセットアップ

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 1.1.1 | ルートディレクトリ作成 | `portfolio-advisor/` | - | ディレクトリ存在確認 |
| 1.1.2 | Makefile作成 | `Makefile` | - | `make help` が動作 |
| 1.1.3 | docker-compose.yml作成 | `docker-compose.yml` | - | `docker-compose config` が通る |
| 1.1.4 | Backend pyproject.toml | `backend/pyproject.toml` | - | `uv sync` が成功 |
| 1.1.5 | Backend Dockerfile | `backend/Dockerfile` | 1.1.4 | `docker build` が成功 |
| 1.1.6 | .env.example作成 | `.env.example` | - | 必要な環境変数が網羅されている |
| 1.1.7 | .gitignore作成 | `.gitignore` | - | 適切なパターン |
| 1.1.8 | GitHub Actions (backend) | `.github/workflows/backend-ci.yml` | - | lint + test |
| 1.1.9 | GitHub Actions (frontend) | `.github/workflows/frontend-ci.yml` | - | lint + build + test |

#### 1.1.2 Makefile 詳細

```makefile
# 想定コマンド:
dev:          docker-compose up
dev-backend:  cd backend && uvicorn src.app.main:app --reload
dev-frontend: cd frontend && bun run dev
test:         backend + frontend test
test-backend:   cd backend && pytest
test-frontend:  cd frontend && bun test
lint:         ruff check + eslint
migrate:      alembic upgrade head
migrate-down: alembic downgrade -1
migration:    alembic revision --autogenerate -m "$(msg)"
seed:         python -m src.app.scripts.seed
update-market-data: python -m src.app.cli update-market-data
```

#### 1.1.4 pyproject.toml 主要依存パッケージ

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.129",
    "uvicorn[standard]",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg",
    "alembic",
    "pydantic[email]>=2.0",
    "httpx",
    # apscheduler不要（手動CLI/GitHub Actions cronで代替、サーバー常時起動回避）
    "pypfopt",          # PyPortfolioOpt
    "pandas>=2.0",
    "numpy",
    "yfinance",
    "fredapi",
    "anthropic",
    "python-dotenv",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "httpx",       # TestClient用
    "ruff",
    "mypy",
]
```

---

### 1.2 DB + モデル + マイグレーション

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 1.2.1 | Core config | `src/app/core/config.py` | 1.1.4 | 環境変数読み込み確認 |
| 1.2.2 | Database接続 | `src/app/core/database.py` | 1.2.1 | DB接続テスト |
| 1.2.3 | Base Model | `src/app/models/base.py` | 1.2.2 | import成功 |
| 1.2.4 | Asset モデル | `src/app/models/asset.py` | 1.2.3 | - |
| 1.2.5 | AssetPrice モデル | `src/app/models/asset_price.py` | 1.2.4 | - |
| 1.2.6 | EconomicIndicator モデル | `src/app/models/economic_indicator.py` | 1.2.3 | - |
| 1.2.7 | models __init__.py | `src/app/models/__init__.py` | 1.2.4-6 | 全モデルimport |
| 1.2.8 | Alembic設定 | `alembic.ini`, `migrations/env.py` | 1.2.7 | `alembic check` 通る |
| 1.2.9 | 初期マイグレーション | `migrations/versions/001_*.py` | 1.2.8 | `alembic upgrade head` 成功 |
| 1.2.10 | シードスクリプト | `src/app/scripts/seed.py` | 1.2.9 | assets テーブルに30-50行 |

#### 1.2.1 config.py 詳細

```python
# Settings (Pydantic BaseSettings)
class Settings(BaseSettings):
    # App
    APP_NAME: str = "Portfolio Advisor API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str  # postgresql+asyncpg://...

    # External APIs
    ANTHROPIC_API_KEY: str = ""
    JQUANTS_EMAIL: str = ""
    JQUANTS_PASSWORD: str = ""
    FRED_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env")
```

#### 1.2.2 database.py 詳細

```python
# async sessionmaker, engine
# get_db() 依存性注入
# 接続プール: pool_size=20, max_overflow=10
```

---

### 1.3 データパイプライン

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 1.3.1 | Base fetcher | `src/app/services/data_pipeline/base.py` | 1.2.2 | - |
| 1.3.2 | yfinance fetcher | `src/app/services/data_pipeline/yfinance_fetcher.py` | 1.3.1 | VTI価格取得テスト |
| 1.3.3 | J-Quants fetcher | `src/app/services/data_pipeline/jquants.py` | 1.3.1 | 1306.T価格取得テスト |
| 1.3.4 | FRED fetcher | `src/app/services/data_pipeline/fred.py` | 1.3.1 | DGS10取得テスト |
| 1.3.5 | ExchangeRate fetcher | `src/app/services/data_pipeline/exchange_rate.py` | 1.3.1 | USD/JPY取得テスト |
| 1.3.6 | Pipeline coordinator | `src/app/services/data_pipeline/coordinator.py` | 1.3.2-5 | 全fetcher統合実行 |
| 1.3.7 | CLI コマンド | `src/app/cli.py` | 1.3.6 | `make update-market-data` で手動実行確認 |
| 1.3.8 | GitHub Actions cron (オプション) | `.github/workflows/update-market-data.yml` | 1.3.7 | スケジュール実行確認 |
| 1.3.9 | Pipeline __init__.py | `src/app/services/data_pipeline/__init__.py` | 1.3.2-7 | - |

#### 1.3.2 yfinance_fetcher.py 詳細

```python
class YFinanceFetcher:
    """米国市場の株式/ETF価格を取得し、DBに保存する。

    - yfinanceライブラリを使用
    - リトライ: 最大3回、指数バックオフ
    - キャッシュ: DB保存済みデータがあれば差分のみ取得
    - エラーハンドリング: 取得失敗時はログ出力、他銘柄は継続
    """

    async def fetch_prices(self, symbols: list[str], period: str = "5y") -> None:
        """指定銘柄の価格データを取得し、asset_pricesテーブルにupsert"""

    async def fetch_single(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """1銘柄の価格データを取得"""
```

#### 1.3.7 cli.py 詳細

```python
# CLIコマンド（typer or click）
# サーバー常時起動不要。手動実行 or GitHub Actions cronで呼び出し。

# make update-market-data → python -m src.app.cli update-market-data
@app.command()
async def update_market_data():
    """全市場データを更新（米国株、日本株、経済指標、為替）"""
    await coordinator.update_all()

# make update-us-prices → python -m src.app.cli update-us-prices
@app.command()
async def update_us_prices():
    """米国株/ETF価格のみ更新"""
    await coordinator.update_us_prices()
```

#### 1.3.8 GitHub Actions cron（オプション）

```yaml
# .github/workflows/update-market-data.yml
name: Update Market Data
on:
  schedule:
    - cron: '0 22 * * 1-5'  # UTC 22:00 = JST 7:00, 平日のみ
  workflow_dispatch:  # 手動トリガーも可能
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          # Railway CLI or API経由でバックエンドのCLIコマンドを実行
          railway run python -m src.app.cli update-market-data
```

---

### 1.4 基本API

> **注意**: 認証は不要。全エンドポイントがパブリック。フロントエンドからFastAPIへ直接リクエストする。

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 1.4.1 | Asset schemas | `src/app/schemas/asset.py` | - | - |
| 1.4.2 | Asset CRUD | `src/app/crud/asset.py` | 1.2.4 | - |
| 1.4.3 | Assets router | `src/app/api/v1/endpoints/assets.py` | 1.4.1-2 | 資産一覧取得テスト |
| 1.4.4 | Market schemas | `src/app/schemas/market.py` | - | - |
| 1.4.5 | Market router | `src/app/api/v1/endpoints/market.py` | 1.4.4 | サマリー取得テスト |
| 1.4.6 | Health router | `src/app/api/v1/endpoints/health.py` | - | GET /health → 200 |
| 1.4.7 | API router集約 | `src/app/api/v1/router.py` | 1.4.3-6 | 全ルート登録確認 |
| 1.4.8 | FastAPIエントリポイント | `src/app/main.py` | 1.4.7 | `uvicorn` 起動、/docs 表示 |

---

## 4. Phase 2: ポートフォリオエンジン

### 2.1 リスク診断

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 2.1.1 | リスク質問定義 + スコア計算 | `src/app/services/risk_profiler.py` | - | 質問8問 + スコアリングロジックのユニットテスト |
| 2.1.2 | RiskAssessment schemas | `src/app/schemas/risk_assessment.py` | - | - |
| 2.1.3 | RiskAssessment router | `src/app/api/v1/endpoints/risk_assessment.py` | 2.1.1-2 | POST → score計算 → レスポンス返却（DB保存なし） |

#### 2.1.1 risk_profiler.py 詳細

```python
class RiskProfiler:
    """リスク許容度を数値化するサービス。

    スコア計算:
    1. 各質問のscore_weightを合計
    2. 最大可能スコアで正規化 (0-1)
    3. 1-10スケールに変換: round(normalized * 9) + 1
    4. カテゴリ分類:
       - 1-3: conservative
       - 4-7: moderate
       - 8-10: aggressive

    戦略推奨:
    - conservative → min_volatility
    - moderate → hrp
    - aggressive → max_sharpe
    """

    QUESTIONS: list[dict]  # 8問の質問定義 (DB設計書のAPI設計 §4.2参照)

    def calculate_score(self, answers: list[dict]) -> RiskScoreResult:
        """回答からリスクスコアを計算"""

    def get_recommended_strategy(self, risk_tolerance: str) -> str:
        """リスク許容度から推奨戦略を返す"""
```

---

### 2.2 ポートフォリオ最適化

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 2.2.1 | Portfolio optimizer | `src/app/services/portfolio_optimizer.py` | 1.3, 2.1.1 | 各戦略の最適化結果テスト |
| 2.2.2 | Portfolio schemas | `src/app/schemas/portfolio.py` | - | - |
| 2.2.3 | Portfolios router | `src/app/api/v1/endpoints/portfolios.py` | 2.2.1-2 | POST → 最適化 → レスポンス返却（DB保存なし） |

#### 2.2.1 portfolio_optimizer.py 詳細（最重要ファイル）

```python
class PortfolioOptimizer:
    """PyPortfolioOptを使用したポートフォリオ最適化エンジン。

    対応戦略:
    - min_volatility: 最小分散ポートフォリオ
      - EfficientFrontier → min_volatility()
      - 制約: 個別資産上限30%
    - hrp: 階層的リスクパリティ
      - HRPOpt → optimize()
      - 共分散推定: Ledoit-Wolf縮約
    - max_sharpe: 最大シャープレシオ
      - EfficientFrontier → max_sharpe()
      - リスクフリーレート: 米国10年国債利回り
    - risk_parity: リスクパリティ
      - 各資産のリスク寄与が均等
    - equal_weight: 均等配分
      - 1/N 配分

    処理フロー:
    1. DBから対象資産の価格データ取得 (asset_prices)
    2. リターン計算 (日次→年率)
    3. 共分散行列推定 (Ledoit-Wolf)
    4. 戦略に応じた最適化実行
    5. weight計算 → Pydanticスキーマとしてレスポンス返却（DB保存なし）
    6. メトリクス計算 (expected_return, volatility, sharpe_ratio)
    """

    async def optimize(
        self,
        risk_score: int,
        risk_tolerance: str,
        investment_horizon: str,
        strategy: str = "auto",
        constraints: dict | None = None,
    ) -> PortfolioResponse:
        """メインエントリポイント"""

    def _select_assets(self, risk_tolerance: str, constraints: dict) -> list[Asset]:
        """リスク許容度と制約に基づいて対象資産を選択"""

    def _get_price_matrix(self, assets: list[Asset]) -> pd.DataFrame:
        """価格データをpandas DataFrameに変換 (columns=symbols, index=date)"""

    def _calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """日次リターン計算"""

    def _optimize_min_volatility(self, returns: pd.DataFrame, constraints: dict) -> dict:
        """最小分散最適化"""

    def _optimize_hrp(self, returns: pd.DataFrame) -> dict:
        """階層的リスクパリティ最適化"""

    def _optimize_max_sharpe(self, returns: pd.DataFrame, risk_free_rate: float) -> dict:
        """最大シャープレシオ最適化"""

    def _optimize_risk_parity(self, returns: pd.DataFrame) -> dict:
        """リスクパリティ最適化"""

    def _optimize_equal_weight(self, assets: list[Asset]) -> dict:
        """均等配分"""

    def _calculate_metrics(self, weights: dict, returns: pd.DataFrame) -> PortfolioMetrics:
        """期待リターン、ボラティリティ、シャープレシオ計算"""
```

**資産選択ロジック**:

```python
# リスク許容度別の資産配分ガイドライン
ALLOCATION_GUIDELINES = {
    "conservative": {
        "bond": (0.50, 0.70),    # 50-70%
        "etf": (0.20, 0.40),     # 20-40% (株式ETF)
        "reit": (0.00, 0.10),    # 0-10%
    },
    "moderate": {
        "bond": (0.20, 0.40),    # 20-40%
        "etf": (0.40, 0.60),     # 40-60%
        "reit": (0.05, 0.15),    # 5-15%
    },
    "aggressive": {
        "bond": (0.05, 0.20),    # 5-20%
        "etf": (0.60, 0.90),     # 60-90%
        "reit": (0.05, 0.15),    # 5-15%
    },
}
```

---

### 2.3 バックテスト

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 2.3.1 | Backtester | `src/app/services/backtester.py` | 2.2.1 | 既知ポートフォリオのメトリクス検証 |
| 2.3.2 | Backtest schemas | `src/app/schemas/backtest.py` | - | - |
| 2.3.3 | Backtest endpoint追加 | `src/app/api/v1/endpoints/portfolios.py` (追記) | 2.3.1-2 | バックテストAPI応答テスト |

#### 2.3.1 backtester.py 詳細

```python
class Backtester:
    """ポートフォリオのヒストリカルバックテスト。

    処理フロー:
    1. ポートフォリオの配分(weights)を取得
    2. 対象期間の価格データ取得
    3. リバランスシミュレーション (quarterly/annual)
    4. 日次ポートフォリオ価値計算
    5. メトリクス算出

    算出指標:
    - final_value: 最終資産額
    - total_return: 累積リターン
    - cagr: 年率複合成長率
    - volatility: 年率ボラティリティ
    - sharpe_ratio: シャープレシオ
    - max_drawdown: 最大ドローダウン
    - sortino_ratio: ソルティノレシオ
    - calmar_ratio: カルマーレシオ
    - annual_returns: 年次リターン

    ベンチマーク:
    - 日経225 (1321.T or ^N225)
    - S&P 500 (SPY or ^GSPC)
    """

    async def run(
        self,
        allocations: list[dict],  # [{symbol, weight}]
        period_years: int = 5,
        initial_investment: float = 1000000,
        rebalance_frequency: str = "quarterly",
    ) -> BacktestResult:
        """バックテスト実行（ステートレス、配分データをリクエストボディで受信）"""
```

---

## 5. Phase 3: AI統合

### 3.1 ポートフォリオ説明生成

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 3.1.1 | AI Advisor | `src/app/services/ai_advisor.py` | 2.2 | 説明文生成テスト(mock) |
| 3.1.2 | Explain endpoint追加 | `src/app/api/v1/endpoints/portfolios.py` (追記) | 3.1.1 | API応答テスト |

#### 3.1.1 ai_advisor.py 詳細

```python
class AIAdvisor:
    """Claude APIを使用したAIアドバイザー。

    機能:
    1. ポートフォリオ説明生成
    2. チャットコンテキスト構築
    3. システムプロンプト管理

    システムプロンプト:
    - 日本語で回答
    - 初心者向け平易な表現
    - 売買タイミング指示禁止
    - リスク言及必須
    - 教育目的の明示
    """

    SYSTEM_PROMPT: str  # 固定のシステムプロンプト

    async def generate_explanation(self, portfolio: Portfolio) -> str:
        """ポートフォリオの説明文を生成"""

    def build_chat_context(self, portfolio: Portfolio, backtest: BacktestResult | None) -> str:
        """チャット用のコンテキスト文字列を構築"""
```

---

### 3.2 ストリーミングチャット + コスト制御

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 3.2.1 | UsageTracker | `src/app/services/usage_tracker.py` | 1.2 | 日次/月次トークン集計、予算チェックテスト |
| 3.2.2 | ApiUsageLog モデル | `src/app/models/api_usage_log.py` | 1.2.3 | - |
| 3.2.3 | Chat schemas | `src/app/schemas/chat.py` | - | - |
| 3.2.4 | Chat SSEエンドポイント | `src/app/api/v1/endpoints/chat.py` | 3.1.1, 3.2.1-3 | SSEストリーミング応答テスト |
| 3.2.5 | Usage schemas | `src/app/schemas/usage.py` | - | - |
| 3.2.6 | Usage エンドポイント | `src/app/api/v1/endpoints/usage.py` | 3.2.1, 3.2.5 | GET /usage で利用状況取得テスト |

#### 3.2.1 usage_tracker.py 詳細

```python
class UsageTracker:
    """Claude API利用量の追跡と予算制御。

    機能:
    1. 日次/月次のトークン使用量をapi_usage_logsから集計
    2. 予算上限チェック（DAILY_TOKEN_BUDGET, MONTHLY_TOKEN_BUDGET）
    3. API呼び出し後のログ記録
    4. コスト推定（モデル別トークン単価）
    """

    async def check_budget(self) -> None:
        """予算チェック。超過時はHTTPException(429)を送出"""

    async def record_usage(self, endpoint: str, model: str, input_tokens: int, output_tokens: int) -> None:
        """利用量をapi_usage_logsに記録"""

    async def get_usage_summary(self) -> UsageSummary:
        """日次/月次の利用サマリーを返す"""
```

#### 3.2.4 chat.py エンドポイント詳細

```python
# FastAPI SSEエンドポイント
# POST /api/v1/chat

from fastapi.responses import StreamingResponse

@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 1. UsageTracker: 予算チェック（超過時は429）
    # 2. システムプロンプト + portfolio_context構築
    # 3. anthropic SDK: client.messages.stream() でストリーミング呼び出し
    # 4. StreamingResponse(media_type="text/event-stream") でSSE返却
    # 5. 完了後、UsageTracker: トークン数記録
    # ※ チャット履歴はDBに保存しない（ページ内のみで保持）
```

---

## 6. Phase 4: フロントエンド

### 4.1 フロントエンド プロジェクトセットアップ

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 4.1.1 | Next.js 16 初期化 | `frontend/` (`create-next-app@latest`) | - | `bun run dev` 起動 |
| 4.1.2 | shadcn/ui初期化 | `frontend/components.json` + `src/components/ui/` | 4.1.1 | コンポーネント生成確認 |
| 4.1.3 | Tailwind CSS v4 設定 | `frontend/tailwind.config.ts` | 4.1.1 | スタイル適用確認 |
| 4.1.4 | TypeScript型定義 | `frontend/src/types/*.ts` | - | 型チェック通過 |
| 4.1.5 | APIクライアント | `frontend/src/lib/api-client.ts` | 4.1.4 | - |
| 4.1.6 | 共通ユーティリティ | `frontend/src/lib/utils.ts` | - | - |

> **依存パッケージ（追加インストール）**:
> ```bash
> bun add recharts@3 zustand@5 @tanstack/react-query
> # ※ Vercel AI SDK (@ai-sdk/anthropic, @ai-sdk/react, ai) は不使用
> # チャットはFastAPI SSEエンドポイントにfetch + ReadableStreamで接続
> ```

---

### 4.2 レイアウト + 共通コンポーネント

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 4.2.1 | ルートレイアウト | `src/app/layout.tsx` | 4.1.1 | Noto Sans JP + lang="ja" |
| 4.2.2 | ヘッダー | `src/components/layout/header.tsx` | 4.1.2 | - |
| 4.2.3 | フッター | `src/components/layout/footer.tsx` | 4.1.2 | - |
| 4.2.4 | 免責バナー | `src/components/layout/disclaimer-banner.tsx` | 4.1.2 | 常時表示確認 |
| 4.2.5 | ランディングページ | `src/app/page.tsx` | 4.2.2 | サービス紹介 + CTA表示 |

---

### 4.3 リスク診断ウィザード

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 4.3.1 | Zustandストア | `src/stores/risk-assessment-store.ts` | - | 状態管理テスト |
| 4.3.2 | プログレスバー | `src/components/risk-assessment/progress-indicator.tsx` | 4.1.2 | - |
| 4.3.3 | 質問ステップ | `src/components/risk-assessment/question-step.tsx` | 4.1.2 | タッチ対応確認 |
| 4.3.4 | リスク診断ページ | `src/app/risk-assessment/page.tsx` | 4.3.1-3 | ウィザードフロー完走 |
| 4.3.5 | スコアゲージ | `src/components/risk-assessment/score-gauge.tsx` | - | - |
| 4.3.6 | 戦略推奨カード | `src/components/risk-assessment/strategy-recommendation.tsx` | 4.1.2 | - |
| 4.3.7 | 結果ページ | `src/app/risk-assessment/result/page.tsx` | 4.3.5-6 | スコア + 戦略表示 |

---

### 4.4 ポートフォリオ詳細

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 4.4.1 | Zustandストア | `src/stores/portfolio-result-store.ts` | - | 状態管理テスト |
| 4.4.2 | 配分テーブル | `src/components/portfolio/allocation-table.tsx` | 4.1.2 | - |
| 4.4.3 | 配分チャート | `src/components/portfolio/allocation-chart.tsx` | Recharts | - |
| 4.4.4 | 指標テーブル | `src/components/portfolio/metrics-table.tsx` | 4.1.2 | - |
| 4.4.5 | バックテストチャート | `src/components/portfolio/backtest-chart.tsx` | Recharts | - |
| 4.4.6 | パフォーマンスチャート | `src/components/portfolio/performance-chart.tsx` | Recharts | - |
| 4.4.7 | ポートフォリオページ | `src/app/portfolio/page.tsx` | 4.4.1-6 | タブ切替 + データ表示 |

---

### 4.5 チャットUI

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 4.5.1 | メッセージバブル | `src/components/chat/message-bubble.tsx` | 4.1.2 | - |
| 4.5.2 | チャット入力 | `src/components/chat/chat-input.tsx` | 4.1.2 | - |
| 4.5.3 | サジェストチップ | `src/components/chat/suggestion-chips.tsx` | 4.1.2 | - |
| 4.5.4 | SSEチャットhook | `src/hooks/use-stream-chat.ts` | 4.1.5 | FastAPI SSEストリーム消費テスト |
| 4.5.5 | チャットコンテナ | `src/components/chat/chat-container.tsx` | 4.5.1-4 | - |
| 4.5.6 | チャットページ | `src/app/chat/page.tsx` | 4.5.5, 3.2.4 | ストリーミング動作確認 |

---

### 4.6 その他ページ

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 4.6.1 | マーケット情報ページ | `src/app/market/page.tsx` | 4.1.5 | マーケット概要 + 資産一覧表示 |
| 4.6.2 | マーケットサマリーカード | `src/components/market/market-summary-card.tsx` | 4.1.2 | - |
| 4.6.3 | use-market-summary hook | `src/hooks/use-market-summary.ts` | 4.1.5 | - |
| 4.6.4 | 利用規約 | `src/app/terms/page.tsx` | - | 静的ページ表示 |
| 4.6.5 | リスク開示 | `src/app/risk-disclosure/page.tsx` | - | 静的ページ表示 |

---

## 7. Phase 5: 仕上げ + ローンチ

### 5.1 コンプライアンス

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 5.1.1 | 免責バナー全ページ設置確認 | `disclaimer-banner.tsx` | 4.2.4 | 全ページで表示 |
| 5.1.2 | AI利用開示文言 | チャットページ + 説明ページ | 4.5.5 | 文言表示確認 |
| 5.1.3 | 利用規約内容作成 | `terms/page.tsx` | 4.6.4 | 法的レビュー |
| 5.1.4 | リスク開示内容作成 | `risk-disclosure/page.tsx` | 4.6.5 | 法的レビュー |

---

### 5.2 パフォーマンス最適化

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 5.2.1 | ISR設定 | `market/summary` ページ | 4.3 | revalidate動作確認 |
| 5.2.2 | チャートDynamic Import | `allocation-chart.tsx` 等 | 4.5 | SSR無効化確認 |
| 5.2.3 | バンドル分析 | `next.config.ts` | 4.1 | バンドルサイズ確認 |
| 5.2.4 | バックエンドキャッシュ | `main.py` + 各ルーター | Phase 1-3 | レスポンスタイム計測 |

---

### 5.3 PWA対応

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 5.3.1 | manifest.json | `public/manifest.json` | - | PWAインストール可能 |
| 5.3.2 | Service Worker | serwist設定 | 5.3.1 | オフラインアクセス |
| 5.3.3 | PWAアイコン | `public/icons/` | - | 各サイズ存在 |

---

### 5.4 テスト

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 5.4.1 | Backend: conftest.py | `backend/tests/conftest.py` | Phase 1 | テストDB設定 |
| 5.4.2 | Backend: risk assessment tests | `backend/tests/test_risk_assessment.py` | 2.1 | スコア計算精度 |
| 5.4.3 | Backend: portfolio tests | `backend/tests/test_portfolio.py` | 2.2 | 最適化出力検証 |
| 5.4.4 | Backend: backtest tests | `backend/tests/test_backtest.py` | 2.3 | メトリクス精度 |
| 5.4.5 | Frontend: component tests | `frontend/src/**/*.test.tsx` | Phase 4 | コンポーネントレンダリング |
| 5.4.6 | E2E: Playwright tests | `frontend/e2e/` | Phase 4 | 診断→結果→ポートフォリオ生成→チャット |

---

### 5.5 デプロイ

| # | タスク | ファイル | 依存 | 検証方法 |
|---|--------|---------|------|---------|
| 5.5.1 | Vercel設定 | `frontend/vercel.json` | Phase 4 | Vercelデプロイ成功 |
| 5.5.2 | Railway設定 | `backend/railway.toml` | Phase 1-3 | Railwayデプロイ成功 |
| 5.5.3 | 環境変数設定 | Vercel/Railway管理画面 | 5.5.1-2 | 全API Key設定済 |
| 5.5.4 | 本番マイグレーション | Railway上でalembic | 5.5.2 | テーブル作成確認 |
| 5.5.5 | 本番シードデータ | Railway上でseed | 5.5.4 | 資産データ確認 |
| 5.5.6 | 動作確認 | 本番URL | 5.5.1-5 | E2Eフロー手動確認 |

---

## 8. 実装ファイル総数

| カテゴリ | ファイル数 |
|---------|----------|
| Backend: Core + Config | 2 |
| Backend: Models | 4 |
| Backend: Schemas | 4 |
| Backend: CRUD | 1 |
| Backend: API Endpoints | 5 |
| Backend: Services | 6 | (usage_tracker追加)
| Backend: Data Pipeline | 6 | (scheduler削除、cli追加)
| Backend: Tests | 5 |
| Backend: Config (pyproject, Dockerfile, alembic等) | 6 |
| Frontend: Pages | 8 |
| Frontend: Components | 18 |
| Frontend: Hooks | 2 |
| Frontend: Stores | 2 |
| Frontend: Lib / Types | 6 |
| Frontend: API Routes | 0 | (チャットはFastAPI SSE、API Route不使用)
| Frontend: Config | 5 |
| Infrastructure | 6 |
| **合計** | **~60ファイル** |

> **設計方針**: 個人/少人数利用前提。認証なし（パブリックAPI）、DBは市場データキャッシュ＋API利用量追跡（4テーブル）、ユーザーデータはブラウザ内一時保持（Zustand）。ステートレス設計により、auth/proxy関連ファイルが不要。チャットはFastAPI SSEに統合しVercel無料枠で運用。APScheduler不要（手動CLI/GitHub Actions cron）。

---

## 9. 並行作業可能なタスク

以下のタスクグループは互いに独立しており、並行作業が可能。認証ボトルネックが解消されたため、並行度が向上。

```
並行グループA (Phase 1):
  1.1 プロジェクトセットアップ ← 最初に完了
  ├── 1.2 DB + モデル (backend)
  └── 4.1 Frontend セットアップ (frontend) ← 同時着手可

並行グループB (Phase 2 + 4前半):
  2.1 リスク診断 (backend)
  ├── 4.2 レイアウト + 共通コンポーネント (frontend) ← 同時着手可
  └── 4.3 リスク診断ウィザードUI (frontend) ← 2.1 API完了後に接続

並行グループC (Phase 2後半 + 4後半):
  2.2 ポートフォリオ最適化 (backend)
  2.3 バックテスト (backend)
  └── 4.4 ポートフォリオ詳細 (frontend)

並行グループD (Phase 3 + 4.5):
  3.1 AI Advisor (backend)
  3.2 チャットAPI Route (frontend)
  └── 4.5 チャットUI (frontend)
```

---

## 10. リスクとマイルストーン

### マイルストーン

| # | マイルストーン | 完了条件 | 対応フェーズ |
|---|-------------|---------|------------|
| M1 | Backend API動作 | 全エンドポイントがSwagger UIで操作可能 | Phase 1 |
| M2 | ポートフォリオ生成 | リスク診断→最適化→バックテストのAPI一連動作 | Phase 2 |
| M3 | AIチャット動作 | ストリーミングチャットが動作 | Phase 3 |
| M4 | Frontend画面完成 | 全画面でデータ表示・操作が可能 | Phase 4 |
| M5 | ローンチ準備完了 | 本番デプロイ + E2Eテスト通過 | Phase 5 |

### 想定タイムライン

認証ボトルネック解消・ステートレス設計により、**4-5週間**での完了を見込む。

### 技術リスク

| リスク | 影響度 | 対策 |
|--------|-------|------|
| PyPortfolioOpt最適化の不安定性 | 高 | Ledoit-Wolf縮約、HRPデフォルト、fallbackをequal_weight |
| yfinance API停止 | 中 | キャッシュ済みデータへのフォールバック |
| J-Quants認証トークン期限切れ | 中 | 自動リフレッシュ、エラー時リトライ |
| Claude API応答遅延 | 中 | タイムアウト設定、ローディング表示 |
| Claude APIコスト超過 | 中 | UsageTrackerによる日次/月次予算上限 + Anthropic Console側の上限設定 |
| Railwayスリープからの復帰遅延 | 低 | 個人利用のため許容（初回アクセス数秒の遅延） |
