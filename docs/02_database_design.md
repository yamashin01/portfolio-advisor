# データベース設計書

## 1. 概要

| 項目 | 内容 |
|------|------|
| DBMS | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (Mapped Column, async) |
| マイグレーション | Alembic |
| ドライバ | asyncpg |
| 命名規約 | snake_case, テーブル名は複数形 |
| 用途 | **市場データキャッシュ + API利用量追跡**（ユーザーデータは保存しない） |

**設計方針**: 本サービスはステートレス・オンデマンド生成型（パターンB）であり、DBは市場データのキャッシュおよびAPI利用量追跡に使用する。リスク診断結果・ポートフォリオ・チャット履歴はDBに保存せず、ブラウザ内（Zustand）で一時保持する。

---

## 2. ER図

```
┌──────────────┐
│   assets     │
├──────────────┤
│ id (PK)      │
│ symbol       │       ┌──────────────────┐
│ name         │       │  asset_prices    │
│ name_ja      │       ├──────────────────┤
│ asset_type   │  1:N  │ id (PK)          │
│ market       │──────▶│ asset_id (FK)    │
│ currency     │       │ date             │
│ sector       │       │ open             │
│ description  │       │ high             │
│ is_active    │       │ low              │
│ created_at   │       │ close            │
│ updated_at   │       │ adj_close        │
└──────────────┘       │ volume           │
                       └──────────────────┘

┌───────────────────────┐
│  economic_indicators  │
├───────────────────────┤
│ id (PK)               │   ※ 独立テーブル（FK無し）
│ indicator_type        │
│ indicator_name        │
│ value                 │
│ currency              │
│ date                  │
│ source                │
│ created_at            │
└───────────────────────┘

┌───────────────────────┐
│  api_usage_logs       │
├───────────────────────┤
│ id (PK)               │   ※ 独立テーブル（FK無し）
│ endpoint              │   ※ Claude API コスト追跡用
│ model                 │
│ input_tokens          │
│ output_tokens         │
│ estimated_cost_usd    │
│ created_at            │
└───────────────────────┘
```

---

## 3. テーブル定義

### 3.1 assets

投資対象の金融資産マスタ。MVPでは30-50銘柄を手動シード。

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid_generate_v4() | 主キー |
| symbol | VARCHAR(20) | NO | - | ティッカーシンボル (例: VTI, 1306.T) |
| name | VARCHAR(200) | NO | - | 英語名称 |
| name_ja | VARCHAR(200) | YES | NULL | 日本語名称 |
| asset_type | VARCHAR(20) | NO | - | 資産タイプ |
| market | VARCHAR(10) | NO | - | 市場 |
| currency | VARCHAR(3) | NO | - | 通貨 (JPY/USD) |
| sector | VARCHAR(50) | YES | NULL | セクター |
| description | TEXT | YES | NULL | 説明文 |
| is_active | BOOLEAN | NO | TRUE | 有効フラグ |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |

**インデックス**:
- `ix_assets_symbol` UNIQUE (symbol)
- `ix_assets_asset_type` (asset_type)
- `ix_assets_market` (market)

**制約**:
- symbol: UNIQUE, NOT NULL
- asset_type: CHECK (asset_type IN ('stock', 'etf', 'bond', 'reit'))
- market: CHECK (market IN ('jp', 'us'))
- currency: CHECK (currency IN ('JPY', 'USD'))

**Enum定義**:

```python
class AssetType(str, Enum):
    STOCK = "stock"   # 個別株
    ETF = "etf"       # ETF
    BOND = "bond"     # 債券（ETF経由）
    REIT = "reit"     # REIT（ETF経由）

class Market(str, Enum):
    JP = "jp"  # 日本市場
    US = "us"  # 米国市場
```

---

### 3.2 asset_prices

資産の日次価格データ。データパイプラインが自動更新。

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | BIGINT | NO | GENERATED ALWAYS AS IDENTITY | 主キー (連番) |
| asset_id | UUID | NO | - | FK → assets.id |
| date | DATE | NO | - | 取引日 |
| open | NUMERIC(18,6) | YES | NULL | 始値 |
| high | NUMERIC(18,6) | YES | NULL | 高値 |
| low | NUMERIC(18,6) | YES | NULL | 安値 |
| close | NUMERIC(18,6) | NO | - | 終値 |
| adj_close | NUMERIC(18,6) | YES | NULL | 調整後終値 |
| volume | BIGINT | YES | NULL | 出来高 |

**インデックス**:
- `uq_asset_prices_asset_date` UNIQUE (asset_id, date) -- 複合ユニーク
- `ix_asset_prices_date` (date)
- `ix_asset_prices_asset_id` (asset_id)

**制約**:
- (asset_id, date): UNIQUE
- close: NOT NULL

**備考**:
- 主キーはUUIDではなくBIGINTを使用（大量レコード想定でパフォーマンス優先）
- adj_closeがNULLの場合はcloseを使用するアプリケーションロジック

---

### 3.3 economic_indicators

経済指標データ（債券利回り、為替レートなど）。

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | BIGINT | NO | GENERATED ALWAYS AS IDENTITY | 主キー |
| indicator_type | VARCHAR(30) | NO | - | 指標タイプ |
| indicator_name | VARCHAR(100) | NO | - | 指標名称 |
| value | NUMERIC(18,6) | NO | - | 値 |
| currency | VARCHAR(3) | YES | NULL | 通貨（為替の場合） |
| date | DATE | NO | - | 日付 |
| source | VARCHAR(50) | NO | - | データソース |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |

**インデックス**:
- `uq_econ_indicators_type_date` UNIQUE (indicator_type, date)
- `ix_economic_indicators_date` (date)

**制約**:
- indicator_type: CHECK (indicator_type IN ('us_treasury_10y', 'jp_govt_bond_10y', 'usd_jpy', 'eur_jpy'))

**Enum定義**:

```python
class IndicatorType(str, Enum):
    US_TREASURY_10Y = "us_treasury_10y"    # 米国10年国債利回り
    JP_GOVT_BOND_10Y = "jp_govt_bond_10y"  # 日本10年国債利回り
    USD_JPY = "usd_jpy"                    # ドル円
    EUR_JPY = "eur_jpy"                    # ユーロ円
```

---

### 3.4 api_usage_logs

Claude API呼び出しの利用量・コストを追跡する。日次/月次の予算上限チェックに使用。

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | BIGINT | NO | GENERATED ALWAYS AS IDENTITY | 主キー |
| endpoint | VARCHAR(50) | NO | - | 呼び出し元エンドポイント (chat, explain) |
| model | VARCHAR(50) | NO | - | 使用モデル (claude-sonnet-4-20250514等) |
| input_tokens | INTEGER | NO | - | 入力トークン数 |
| output_tokens | INTEGER | NO | - | 出力トークン数 |
| estimated_cost_usd | NUMERIC(10,6) | NO | - | 推定コスト (USD) |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |

**インデックス**:
- `ix_api_usage_logs_created_at` (created_at)
- `ix_api_usage_logs_endpoint` (endpoint)

**コスト計算ロジック**:
```python
# モデル別トークン単価 (USD per token)
MODEL_PRICING = {
    "claude-sonnet": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-haiku":  {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
}

# 日次/月次予算チェック
# DAILY_TOKEN_BUDGET, MONTHLY_TOKEN_BUDGET は環境変数で設定
# 超過時は 429 Too Many Requests を返却
```

---

## 4. リレーション一覧

| 親テーブル | 子テーブル | カーディナリティ | FK カラム | ON DELETE |
|-----------|-----------|---------------|----------|-----------|
| assets | asset_prices | 1:N | asset_id | CASCADE |

※ economic_indicators, api_usage_logs は独立テーブル（FK無し）

---

## 5. シードデータ（MVP対象資産）

### 5.1 日本市場

| symbol | name_ja | asset_type | 説明 |
|--------|---------|-----------|------|
| 1306.T | TOPIX連動型上場投資信託 | etf | TOPIX連動 |
| 1321.T | 日経225連動型上場投資信託 | etf | 日経225連動 |
| 2558.T | MAXIS米国株式(S&P500)上場投信 | etf | S&P500連動(円建て) |
| 1343.T | NEXT FUNDS 東証REIT指数連動型上場投信 | reit | J-REIT指数連動 |
| 2511.T | NEXT FUNDS 外国債券・FTSE世界国債インデックス | bond | 外国債券 |
| 1326.T | SPDRゴールド・シェア | etf | 金連動 |
| 2631.T | MAXISナスダック100上場投信 | etf | NASDAQ100連動 |
| 2559.T | MAXIS全世界株式(オール・カントリー)上場投信 | etf | 全世界株式 |
| 1476.T | iシェアーズ・コアJリート | reit | J-REIT |
| 2620.T | iシェアーズ 米国債20年超 ETF(為替ヘッジあり) | bond | 米国長期債(ヘッジ) |

### 5.2 米国市場

| symbol | name_ja | asset_type | 説明 |
|--------|---------|-----------|------|
| VTI | バンガード・トータル・ストック・マーケットETF | etf | 米国株式全体 |
| VEA | バンガード・FTSE先進国市場(除く米国)ETF | etf | 先進国株式(除米国) |
| VWO | バンガード・FTSE・エマージング・マーケッツETF | etf | 新興国株式 |
| BND | バンガード・米国トータル債券市場ETF | bond | 米国債券全体 |
| AGG | iシェアーズ・コア米国総合債券市場ETF | bond | 米国総合債券 |
| VNQ | バンガード・リアルエステートETF | reit | 米国REIT |
| GLD | SPDRゴールド・シェア | etf | 金連動 |
| TLT | iシェアーズ 米国国債 20年超 ETF | bond | 米国長期国債 |
| VXUS | バンガード・トータル・インターナショナル・ストックETF | etf | 米国外株式全体 |
| VT | バンガード・トータル・ワールド・ストックETF | etf | 全世界株式 |
| SPY | SPDR S&P 500 ETF トラスト | etf | S&P500連動 |
| QQQ | インベスコQQQトラスト | etf | NASDAQ100連動 |
| IEF | iシェアーズ 米国国債 7-10年 ETF | bond | 米国中期国債 |
| SHY | iシェアーズ 米国国債 1-3年 ETF | bond | 米国短期国債 |
| SCHD | シュワブ 米国配当株式ETF | etf | 米国高配当 |

---

## 6. データ量見積り

| テーブル | 見積りレコード数 (1年後) | 成長率 |
|---------|----------------------|--------|
| assets | ~50 (固定) | シード管理 |
| asset_prices | ~62,500 | 50銘柄×250営業日×5年 |
| economic_indicators | ~4,000 | 4指標×250日×4年 |
| api_usage_logs | ~3,000 | 個人利用想定: ~10回/日 × 365日 |

**合計想定**: ~69,550レコード（初年度）

---

## 7. マイグレーション戦略

```
Alembic で全テーブルを管理:

alembic/
├── alembic.ini
├── env.py               # async対応
├── script.py.mako
└── versions/
    ├── 001_initial_schema.py     # 4テーブル作成（assets, asset_prices, economic_indicators, api_usage_logs）
    └── 002_seed_assets.py        # MVP資産シードデータ
```

### マイグレーション運用

```bash
# マイグレーション作成
make migration msg="add_new_column"

# マイグレーション実行
make migrate         # alembic upgrade head

# ロールバック
make migrate-down    # alembic downgrade -1

# シードデータ投入
make seed
```
