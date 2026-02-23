# デプロイガイド

本サービスを Railway（バックエンド + DB）+ Vercel（フロントエンド）にデプロイする手順。

## 必要なサービスアカウント

| サービス | 用途 | 費用目安 |
|---------|------|---------|
| [Railway](https://railway.app) | バックエンド + PostgreSQL | ~$5-10/月（スリープ有効） |
| [Vercel](https://vercel.com) | フロントエンド | 無料（Hobbyプラン） |
| [Anthropic](https://console.anthropic.com/) | Claude API | 従量課金（予算制御あり） |
| [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) | 米国経済データAPI | 無料 |
| [J-Quants](https://jpx-jquants.com/) | 日本市場データAPI | 無料プランあり |

**月額コスト目安**: $10-30（Railway + Claude API従量課金）

## 1. 外部APIキーの取得

### Anthropic API キー（必須）

1. https://console.anthropic.com/ でアカウント作成・ログイン
2. 左メニュー「API Keys」→「Create Key」
3. `sk-ant-api03-...` 形式のキーをコピー（再表示不可）
4. 左メニュー「Billing」→「Add Credits」でクレジット追加（最低$5）

### FRED API キー（市場データ更新時に必要）

1. https://fred.stlouisfed.org/docs/api/api_key.html にアクセス
2. 「Request or view your API keys」をクリック
3. FREDアカウント作成（無料）→ ログイン
4. 「Request API Key」→ 用途を入力（例: `Personal portfolio analysis tool`）
5. 発行されたキーをコピー

### J-Quants アカウント（市場データ更新時に必要）

1. https://jpx-jquants.com/ でユーザー登録（無料プランあり）
2. 登録時のメールアドレスとパスワードをそのまま環境変数に使用

## 2. Railway セットアップ（バックエンド + DB）

### 2-1. PostgreSQL サービスの追加

1. https://railway.app/dashboard にログイン
2. 「New Project」でプロジェクト作成（または既存を開く）
3. 画面右上の「+ New」→「Database」→「Add PostgreSQL」
4. PostgreSQL サービスが自動作成される

**公開ネットワークの有効化**（ローカルからの初回セットアップに必要）:

1. PostgreSQL サービスをクリック
2. 「Settings」→「Networking」→「TCP Proxy」を有効化
3. 「Variables」タブに `DATABASE_PUBLIC_URL` が追加されるのでコピー

### 2-2. バックエンドサービスの追加

1. 「+ New」→「GitHub Repo」→ 本リポジトリを選択
2. Root Directory に `backend` を指定
3. 「Variables」タブで以下の環境変数を設定:

```env
# DB接続（PostgreSQLサービスの内部URLを使用、先頭を書き換え）
# postgresql://... → postgresql+asyncpg://...
DATABASE_URL=postgresql+asyncpg://postgres:xxxx@postgres.railway.internal:5432/railway

# Claude API（必須）
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# トークン予算（推奨）
DAILY_TOKEN_BUDGET=100000
MONTHLY_TOKEN_BUDGET=2000000

# CORS（Vercelデプロイ後にURLを設定）
CORS_ORIGINS=["https://your-app.vercel.app"]

# 市場データAPI（後から追加可）
FRED_API_KEY=your-fred-api-key
JQUANTS_EMAIL=your-email@example.com
JQUANTS_PASSWORD=your-password
```

> **注意**: `DATABASE_URL` の先頭は必ず `postgresql+asyncpg://` にすること。Railway が自動生成する `postgresql://` のままでは async ドライバが使われない。

### 2-3. デプロイ確認

デプロイ完了後、ヘルスチェックで動作確認:

```
https://your-backend.up.railway.app/api/v1/health
```

## 3. Vercel セットアップ（フロントエンド）

1. https://vercel.com にログイン（GitHub連携）
2. 「Add New...」→「Project」→ 本リポジトリをインポート
3. **Root Directory** を `frontend` に設定
4. 環境変数を設定:

```env
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
```

5. 「Deploy」をクリック

デプロイ完了後、Vercel が割り当てたURL（例: `https://portfolio-advisor-abc.vercel.app`）を確認し、Railway バックエンドの `CORS_ORIGINS` に設定する。

## 4. 初回データセットアップ

ローカルPCのターミナルから、Railway の公開 DB URL を使ってマイグレーションとシードを実行する。

### 4-1. 準備

```bash
cd backend
```

Railway PostgreSQL の「Variables」タブから `DATABASE_PUBLIC_URL` をコピーし、先頭を `postgresql+asyncpg://` に書き換えて export する:

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:xxxx@monorail.proxy.rlwy.net:12345/railway"
```

### 4-2. マイグレーション（テーブル作成）

```bash
uv run alembic upgrade head
```

### 4-3. 資産データシード（約50銘柄の登録）

```bash
uv run python -m src.app.cli seed
```

### 4-4. 市場データ取得（APIキー設定済みの場合のみ）

```bash
FRED_API_KEY="your-key" \
JQUANTS_EMAIL="your-email" \
JQUANTS_PASSWORD="your-pass" \
uv run python -m src.app.cli update-market-data
```

> 市場データ取得は後からでも可。シードデータだけでリスク診断とチャットは動作する。ただし、ポートフォリオ最適化やバックテストには価格データが必要。

## 5. GitHub Actions の設定（市場データ自動更新）

リポジトリの Settings → Secrets and variables → Actions に以下を追加:

| シークレット名 | 値 |
|---------------|---|
| `DATABASE_URL` | Railway PostgreSQL の公開URL（`postgresql+asyncpg://...`） |
| `FRED_API_KEY` | FRED APIキー |
| `JQUANTS_EMAIL` | J-Quants メールアドレス |
| `JQUANTS_PASSWORD` | J-Quants パスワード |

設定後、`.github/workflows/update-market-data.yml` が平日 22:00 UTC（JST 翌7:00）に自動実行される。

## 6. デプロイ後の確認チェックリスト

- [ ] Railway: `/api/v1/health` が 200 を返す
- [ ] Vercel: フロントエンドが表示される
- [ ] フロントエンドからバックエンドへの API 通信が成功する（CORS）
- [ ] リスク診断の質問が表示される
- [ ] チャット機能が動作する（Claude API）
- [ ] （市場データ設定後）ポートフォリオ生成・バックテストが動作する

## 環境変数まとめ

### Railway（バックエンド）

| 変数 | 必須度 | 説明 |
|------|--------|------|
| `DATABASE_URL` | 必須 | PostgreSQL接続（`postgresql+asyncpg://...`） |
| `ANTHROPIC_API_KEY` | 必須 | Claude API キー |
| `CORS_ORIGINS` | 必須 | Vercel の URL（JSON配列形式） |
| `DAILY_TOKEN_BUDGET` | 推奨 | 日次トークン上限（デフォルト推奨: `100000`） |
| `MONTHLY_TOKEN_BUDGET` | 推奨 | 月次トークン上限（デフォルト推奨: `2000000`） |
| `FRED_API_KEY` | 任意 | 米国経済データ取得に必要 |
| `JQUANTS_EMAIL` | 任意 | 日本市場データ取得に必要 |
| `JQUANTS_PASSWORD` | 任意 | 日本市場データ取得に必要 |

### Vercel（フロントエンド）

| 変数 | 必須度 | 説明 |
|------|--------|------|
| `NEXT_PUBLIC_API_URL` | 必須 | Railway バックエンドの URL |
