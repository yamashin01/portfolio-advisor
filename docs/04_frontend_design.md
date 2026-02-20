# フロントエンド設計書

## 1. 概要

| 項目 | 内容 |
|------|------|
| フレームワーク | Next.js 16 (App Router) |
| 言語 | TypeScript 5.x |
| UIライブラリ | shadcn/ui (統合 radix-ui パッケージ) + Tailwind CSS v4 |
| チャート | Recharts v3 |
| 状態管理 | Zustand v5 (クライアント + 計算結果一時保持) + TanStack Query v5 (サーバー) |
| チャット | fetch + ReadableStream でFastAPI SSEエンドポイントを消費（Vercel AI SDK不使用） |
| ホスティング | Vercel Hobbyプラン（無料。API Routeなし、サーバーレス関数なし） |
| フォント | Noto Sans JP (Google Fonts) |
| ロケール | `<html lang="ja">` |

---

## 2. 画面一覧

| # | 画面名 | パス | 説明 |
|---|--------|------|------|
| P1 | ランディング | `/` | サービス紹介、CTA |
| P2 | リスク診断 | `/risk-assessment` | ウィザード形式のリスク診断 |
| P3 | 診断結果 | `/risk-assessment/result` | スコア表示、戦略推奨 |
| P4 | ポートフォリオ | `/portfolio` | 配分、メトリクス、バックテスト |
| P5 | AIチャット | `/chat` | ストリーミングチャット |
| P6 | マーケット情報 | `/market` | 対象銘柄ブラウズ、マーケット概要 |
| P7 | 利用規約 | `/terms` | 利用規約 |
| P8 | リスク開示 | `/risk-disclosure` | リスク開示・免責事項 |

※ 全ページパブリック（認証不要）。ログインページ・設定ページは不要。

---

## 3. 画面遷移図

```
                    ┌──────────┐
                    │ Landing  │ (/)
                    │   (P1)   │
                    └────┬─────┘
                         │ 「診断を始める」
                         ▼
                   ┌────────────┐
                   │    Risk    │ (/risk-assessment)
                   │ Assessment │
                   │   (P2)     │
                   └─────┬──────┘
                         │
                         ▼
                   ┌────────────┐
                   │  Result    │ (/risk-assessment/result)
                   │   (P3)     │ ※ Zustandに結果を保持
                   └─────┬──────┘
                         │ 「ポートフォリオ生成」
                         ▼
                   ┌──────────┐
                   │Portfolio │ (/portfolio)
                   │  (P4)    │ ※ Zustandに結果を保持
                   └─────┬────┘
                         │ 「チャットで質問」
                         ▼
                   ┌──────────┐
                   │   Chat   │ (/chat)
                   │   (P5)   │
                   └──────────┘

サイドリンク:
  マーケット情報 (P6: /market)

共通リンク（フッター）:
  利用規約 (P7), リスク開示 (P8)
```

---

## 4. ディレクトリ構造

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                    # ルートレイアウト（フォント、プロバイダー、免責バナー）
│   │   ├── page.tsx                      # P1: ランディング
│   │   ├── globals.css                   # Tailwind グローバルCSS
│   │   ├── risk-assessment/
│   │   │   ├── page.tsx                  # P2: リスク診断ウィザード
│   │   │   └── result/page.tsx           # P3: 診断結果
│   │   ├── portfolio/
│   │   │   └── page.tsx                  # P4: ポートフォリオ詳細
│   │   ├── chat/
│   │   │   └── page.tsx                  # P5: AIチャット
│   │   ├── market/
│   │   │   └── page.tsx                  # P6: マーケット情報・資産一覧
│   │   ├── terms/page.tsx                # P7: 利用規約
│   │   └── risk-disclosure/page.tsx      # P8: リスク開示
│   │   # ※ api/ ディレクトリなし（チャットはFastAPI SSE、Vercel Hobby無料枠で運用）
│   ├── components/
│   │   ├── ui/                           # shadcn/ui コンポーネント
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── separator.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── header.tsx                # ヘッダー（ロゴ、ナビ）
│   │   │   ├── footer.tsx                # フッター（免責リンク）
│   │   │   └── disclaimer-banner.tsx     # 免責事項バナー
│   │   ├── portfolio/
│   │   │   ├── allocation-chart.tsx       # 配分ドーナツチャート (Recharts PieChart)
│   │   │   ├── performance-chart.tsx      # パフォーマンス折れ線グラフ (Recharts LineChart)
│   │   │   ├── metrics-table.tsx          # 指標テーブル
│   │   │   ├── backtest-chart.tsx         # バックテストチャート
│   │   │   └── allocation-table.tsx       # 配分一覧テーブル
│   │   ├── risk-assessment/
│   │   │   ├── question-step.tsx          # 1問表示コンポーネント
│   │   │   ├── progress-indicator.tsx     # 進捗バー
│   │   │   ├── score-gauge.tsx            # スコアゲージ表示
│   │   │   └── strategy-recommendation.tsx # 戦略推奨カード
│   │   ├── chat/
│   │   │   ├── chat-container.tsx         # チャット全体コンテナ
│   │   │   ├── message-bubble.tsx         # メッセージバブル
│   │   │   ├── chat-input.tsx             # 入力フォーム
│   │   │   └── suggestion-chips.tsx       # サジェストチップ
│   │   ├── market/
│   │   │   ├── market-summary-card.tsx    # マーケットサマリーカード
│   │   │   └── indicator-badge.tsx        # 経済指標バッジ
│   │   └── common/
│   │       ├── loading-spinner.tsx        # ローディング表示
│   │       ├── error-boundary.tsx         # エラーバウンダリ
│   │       └── empty-state.tsx            # 空状態表示
│   ├── lib/
│   │   ├── api-client.ts                 # Backend API クライアント (FastAPI直接呼び出し)
│   │   └── utils.ts                      # ユーティリティ関数
│   ├── hooks/
│   │   ├── use-assets.ts                 # TanStack Query: 資産一覧
│   │   ├── use-market-summary.ts         # TanStack Query: マーケットサマリー
│   │   └── use-stream-chat.ts            # カスタムhook: FastAPI SSEチャット（fetch + ReadableStream）
│   ├── stores/
│   │   ├── risk-assessment-store.ts      # Zustand: ウィザード状態管理
│   │   └── portfolio-result-store.ts     # Zustand: ポートフォリオ生成結果の一時保持
│   └── types/
│       ├── api.ts                        # APIレスポンス型定義
│       ├── portfolio.ts                  # ポートフォリオ関連型
│       ├── risk-assessment.ts            # リスク診断関連型
│       └── asset.ts                      # 資産関連型
├── public/
│   ├── manifest.json                     # PWA マニフェスト
│   └── icons/                            # PWA アイコン
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── components.json                       # shadcn/ui設定
```

---

## 5. 主要画面設計

### 5.1 P1: ランディング

```
┌─────────────────────────────────────────────────────────────┐
│ [免責バナー] 本サービスは教育目的であり、投資助言ではありません │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AI ポートフォリオアドバイザー                                │
│                                                             │
│  あなたのリスク許容度に合わせた                               │
│  最適なポートフォリオをAIが提案します                          │
│                                                             │
│  ┌─────────────────────────────────────────┐                │
│  │     [リスク診断を始める →]               │                │
│  └─────────────────────────────────────────┘                │
│                                                             │
│  マーケット概要                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │日経225    │ │S&P 500   │ │USD/JPY   │                    │
│  │39,245    │ │6,123     │ │150.23    │                    │
│  │+0.82%    │ │-0.12%    │ │-0.15%    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
│                                                             │
│  ※ ログイン不要。診断結果はブラウザ内に一時保存されます。      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 P5: リスク診断ウィザード

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  リスク診断                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3/8              │
│  [===========================...............]   │
│                                                 │
│  Q3. 投資期間はどれくらいを予定していますか？       │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │                                         │    │
│  │  ○ 1〜3年（短期）                        │    │
│  │                                         │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │                                         │    │
│  │  ● 3〜10年（中期）                       │    │
│  │                                         │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │                                         │    │
│  │  ○ 10年以上（長期）                      │    │
│  │                                         │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│         [← 戻る]           [次へ →]             │
│                                                 │
└─────────────────────────────────────────────────┘

※ 各選択肢は大きなタッチ対応ボタン（min-height: 56px）
※ 選択済みはハイライト + チェックマーク
※ モバイル: フルウィドス、PC: max-width 640px 中央配置
```

### 5.3 P6: 診断結果

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  あなたのリスク診断結果                           │
│                                                 │
│         ┌─────────────────┐                     │
│         │   ┌─────────┐   │                     │
│         │   │  7 / 10 │   │  スコアゲージ        │
│         │   └─────────┘   │  (円形プログレス)    │
│         └─────────────────┘                     │
│                                                 │
│  リスク許容度: バランス型（Moderate）              │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ あなたの特徴                             │    │
│  │ ・中程度のリスクを受け入れられる           │    │
│  │ ・長期投資を志向                          │    │
│  │ ・株式と債券のバランスが適切               │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  おすすめ戦略: 階層的リスクパリティ (HRP)          │
│  ┌─────────────────────────────────────────┐    │
│  │ HRPは資産間の相関構造を考慮し、            │    │
│  │ 分散効果を最大化する手法です。              │    │
│  │ 推定誤差に対して頑健な配分が得られます。     │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│     [ポートフォリオを生成する →]                  │
│     (もう一度診断する)                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 5.4 P7: ポートフォリオ詳細

```
┌─────────────────────────────────────────────────────────────┐
│ バランス型ポートフォリオ                      [チャットで質問] │
│                                                             │
│ ┌───────────┬──────────┬──────────────┬───────────┐        │
│ │  概要     │  配分    │  バックテスト  │  AI説明   │        │
│ └───┬───────┴──────────┴──────────────┴───────────┘        │
│     │                                                       │
│ [概要タブ]                                                   │
│ ┌─────────────────────┐ ┌──────────────────────────┐        │
│ │  指標                │ │  配分チャート             │        │
│ │                      │ │  ┌──────────────────┐   │        │
│ │  期待リターン: 6.82% │ │  │                  │   │        │
│ │  ボラティリティ:11.24%│ │  │  ドーナツチャート  │   │        │
│ │  シャープレシオ: 0.51│ │  │                  │   │        │
│ │  戦略: HRP          │ │  └──────────────────┘   │        │
│ └─────────────────────┘ └──────────────────────────┘        │
│                                                             │
│ 配分一覧                                                    │
│ ┌────────┬───────────────────┬──────┬────────┬─────────┐   │
│ │ シンボル│ 銘柄名              │ 種別 │ 配分比率│ 金額(円) │   │
│ ├────────┼───────────────────┼──────┼────────┼─────────┤   │
│ │ VTI    │ バンガード全米株式   │ ETF  │ 25.0%  │ 250,000 │   │
│ │ 1306.T │ TOPIX連動ETF       │ ETF  │ 20.0%  │ 200,000 │   │
│ │ BND    │ バンガード米国債券   │ 債券 │ 20.0%  │ 200,000 │   │
│ │ 2511.T │ 外国債券インデックス │ 債券 │ 15.0%  │ 150,000 │   │
│ │ VNQ    │ バンガード米国REIT  │ REIT │ 10.0%  │ 100,000 │   │
│ │ GLD    │ SPDRゴールド       │ ETF  │ 10.0%  │ 100,000 │   │
│ └────────┴───────────────────┴──────┴────────┴─────────┘   │
│                                                             │
│ [バックテストタブ]                                            │
│ ┌──────────────────────────────────────────────────┐        │
│ │  パフォーマンスチャート (5年間)                     │        │
│ │  ┌──────────────────────────────────────────┐   │        │
│ │  │  ━━ ポートフォリオ  ---- 日経225  .... S&P │   │        │
│ │  │  ^                          ___/          │   │        │
│ │  │  │                    ___/``              │   │        │
│ │  │  │             ___---                    │   │        │
│ │  │  │     ___----                           │   │        │
│ │  │  │____/                                  │   │        │
│ │  │  └──────────────────────────────────────▶│   │        │
│ │  │   2021    2022    2023    2024    2025    │   │        │
│ │  └──────────────────────────────────────────┘   │        │
│ │                                                  │        │
│ │  バックテスト指標                                  │        │
│ │  累積リターン: 41.2% │ CAGR: 7.14%               │        │
│ │  最大DD: -18.23%    │ シャープ: 0.52              │        │
│ └──────────────────────────────────────────────────┘        │
│                                                             │
│ ※ 過去のパフォーマンスは将来の結果を保証するものではありません  │
└─────────────────────────────────────────────────────────────┘
```

### 5.5 P8: AIチャット

```
┌─────────────────────────────────────────────────┐
│ AIアドバイザー                                    │
│ ※ 教育目的の情報提供です。投資助言ではありません。   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ AI: こんにちは！ポートフォリオについて     │    │
│  │ 何でもお気軽にご質問ください。              │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│       ┌─────────────────────────────────┐       │
│       │ You: このポートフォリオのリスクを │       │
│       │ 教えてください                    │       │
│       └─────────────────────────────────┘       │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ AI: お持ちのバランス型ポートフォリオの    │    │
│  │ リスクについてご説明しますね。             │    │
│  │                                         │    │
│  │ **ボラティリティ（価格変動の大きさ）**     │    │
│  │ 年率約11.2%です。これは...               │    │
│  │ █ (ストリーミング中)                     │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  サジェスト:                                     │
│  [リスクを下げたい] [もっと詳しく] [他の戦略は？]  │
│                                                 │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ [送信]      │
│ │ メッセージを入力...              │             │
│ └─────────────────────────────────┘             │
└─────────────────────────────────────────────────┘
```

---

## 6. コンポーネント設計

### 6.1 コンポーネント階層図

```
RootLayout
├── Header
│   ├── Logo
│   └── Navigation
├── DisclaimerBanner
├── [Page Content]
│   ├── LandingPage
│   │   ├── HeroCTA ("リスク診断を始める")
│   │   └── MarketSummaryCard (×3)
│   │       └── IndicatorBadge
│   ├── RiskAssessmentPage
│   │   ├── ProgressIndicator
│   │   └── QuestionStep
│   ├── RiskResultPage
│   │   ├── ScoreGauge
│   │   └── StrategyRecommendation
│   ├── PortfolioPage
│   │   ├── Tabs
│   │   ├── MetricsTable
│   │   ├── AllocationChart (full size)
│   │   ├── AllocationTable
│   │   ├── BacktestChart
│   │   └── AI Explanation (markdown)
│   ├── ChatPage
│   │   ├── UsageBanner (日次予算残量表示)
│   │   ├── ChatContainer
│   │   │   └── MessageBubble (×N)
│   │   ├── SuggestionChips
│   │   └── ChatInput
│   └── MarketPage
│       ├── MarketSummaryCard (×3)
│       └── AssetList
└── Footer
    └── FooterLinks (利用規約, リスク開示)
```

### 6.2 主要コンポーネント仕様

#### AllocationChart

| 項目 | 内容 |
|------|------|
| 用途 | ポートフォリオ配分のドーナツチャート |
| ライブラリ | Recharts PieChart |
| Props | `allocations: Allocation[]`, `size?: "sm" | "lg"` |
| 動作 | ホバーでツールチップ（銘柄名、比率、金額）、クリックで資産詳細 |
| レスポンシブ | sm: 150x150, lg: 300x300 |

#### PerformanceChart / BacktestChart

| 項目 | 内容 |
|------|------|
| 用途 | 時系列パフォーマンスの折れ線グラフ |
| ライブラリ | Recharts LineChart |
| Props | `timeSeries: TimeSeriesPoint[]`, `benchmarks?: Benchmark[]` |
| 動作 | ツールチップ（日付、値、リターン）、ベンチマーク比較線表示 |
| レスポンシブ | ResponsiveContainer使用 |

#### QuestionStep

| 項目 | 内容 |
|------|------|
| 用途 | リスク診断の1問表示 |
| Props | `question: Question`, `onAnswer: (value: string) => void`, `selectedValue?: string` |
| 動作 | 大きなタッチ対応ボタン、選択時ハイライト、アニメーション遷移 |
| アクセシビリティ | radiogroup role, aria-checked, keyboard navigation |

#### ChatContainer

| 項目 | 内容 |
|------|------|
| 用途 | AIチャットのメッセージ表示エリア |
| Props | `messages: Message[]`, `isLoading: boolean` |
| 動作 | 自動スクロール、ストリーミング表示、マークダウンレンダリング |
| 依存 | カスタム `useStreamChat` hook（fetch + ReadableStream でFastAPI SSEを消費） |

#### ScoreGauge

| 項目 | 内容 |
|------|------|
| 用途 | リスクスコアの円形ゲージ表示 |
| Props | `score: number` (1-10), `tolerance: RiskTolerance` |
| 動作 | スコアに応じた色変化（緑→黄→赤）、アニメーション |

---

## 7. 状態管理設計

### 7.1 サーバー状態 (TanStack Query)

市場データ・資産データなど、APIから取得するデータはTanStack Queryで管理する。リスク診断結果やポートフォリオ生成結果はDBに保存しないため、TanStack Queryでは管理しない（Zustandで一時保持）。

```typescript
// hooks/use-assets.ts, use-market-summary.ts
const queryKeys = {
  riskAssessment: {
    questions: ['risk-assessment', 'questions'] as const,
  },
  assets: {
    all: ['assets'] as const,
    prices: (symbol: string) => ['assets', symbol, 'prices'] as const,
  },
  market: {
    summary: ['market', 'summary'] as const,
  },
} as const;

// キャッシュ戦略
const cacheConfig = {
  riskQuestions: { staleTime: 24 * 60 * 60 * 1000 }, // 24時間（質問は固定）
  assets:        { staleTime: 60 * 60 * 1000 },      // 1時間
  marketSummary: { staleTime: 5 * 60 * 1000 },       // 5分
  assetPrices:   { staleTime: 60 * 60 * 1000 },      // 1時間
};
```

### 7.2 クライアント状態 (Zustand)

リスク診断ウィザードの進行状態と、生成結果の一時保持をZustandで管理。DBには保存しない。

```typescript
// stores/risk-assessment-store.ts
interface RiskAssessmentState {
  // 状態
  currentStep: number;
  answers: Record<number, string>;  // question_id → selected value
  isSubmitting: boolean;
  result: RiskAssessmentResult | null;  // 診断結果（スコア、カテゴリ、推奨戦略）

  // アクション
  setAnswer: (questionId: number, value: string) => void;
  nextStep: () => void;
  prevStep: () => void;
  setResult: (result: RiskAssessmentResult) => void;
  reset: () => void;
  getProgress: () => number;  // 0.0-1.0
}

// stores/portfolio-result-store.ts
interface PortfolioResultState {
  // 状態
  portfolio: PortfolioResult | null;     // 生成されたポートフォリオ
  backtest: BacktestResult | null;       // バックテスト結果
  explanation: string | null;            // AI説明文

  // アクション
  setPortfolio: (portfolio: PortfolioResult) => void;
  setBacktest: (backtest: BacktestResult) => void;
  setExplanation: (explanation: string) => void;
  clear: () => void;
}
```

※ 認証なし。全ページパブリック。ユーザー状態はブラウザ内のみで一時保持。

---

## 8. APIクライアント設計

全エンドポイントがパブリック。フロントエンドからFastAPIへ直接リクエストする（プロキシ不要）。

```typescript
// lib/api-client.ts

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  // 共通fetchラッパー
  private async request<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(response.status, error.detail, error.errors);
    }

    return response.json();
  }

  // Risk Assessment（ステートレス）
  getQuestions(): Promise<QuestionsResponse> { ... }
  calculateRisk(data: RiskAssessmentRequest): Promise<RiskAssessmentResponse> { ... }

  // Portfolio（ステートレス、都度生成）
  generatePortfolio(data: GenerateRequest): Promise<PortfolioResponse> { ... }
  runBacktest(data: BacktestRequest): Promise<BacktestResponse> { ... }
  explainPortfolio(data: ExplainRequest): Promise<ExplainResponse> { ... }

  // Chat（FastAPI SSE — fetch + ReadableStreamで消費）
  streamChat(data: ChatRequest): Promise<Response> { ... }  // SSEストリームを返す

  // Assets
  getAssets(params?: AssetQuery): Promise<PaginatedResponse<AssetResponse>> { ... }
  getAssetPrices(symbol: string, params?: PriceQuery): Promise<PriceResponse> { ... }

  // Market
  getMarketSummary(): Promise<MarketSummaryResponse> { ... }

  // Usage（コスト確認）
  getUsage(): Promise<UsageResponse> { ... }
}

export const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_URL!);
```

---

## 9. レスポンシブ設計

### ブレークポイント (Tailwind CSS)

| 名称 | 幅 | 用途 |
|------|-----|------|
| sm | 640px | モバイル横向き |
| md | 768px | タブレット |
| lg | 1024px | デスクトップ |
| xl | 1280px | ワイドデスクトップ |

### レイアウト対応

| 画面 | モバイル | デスクトップ |
|------|---------|------------|
| ランディング | マーケットカード縦並び | 横並び |
| リスク診断 | フルウィドス、大きなボタン | max-w-xl中央配置 |
| ポートフォリオ詳細 | タブ縦スクロール | 2カラム配置 |
| チャット | フルスクリーン | 右サイドパネル or 中央配置 |

---

## 10. パフォーマンス最適化

| 手法 | 対象 | 実装 |
|------|------|------|
| ISR | マーケットサマリー | `revalidate: 3600` (1時間) |
| Dynamic Import | チャートコンポーネント | `next/dynamic` with `loading` |
| Image Optimization | アイコン・ロゴ | `next/image` |
| Code Splitting | 各ページ | App Router自動分割 |
| Query Prefetch | ランディング | `prefetchQuery` on hover |
| Font Optimization | Noto Sans JP | `next/font/google` subset |

---

## 11. アクセシビリティ

| 対応項目 | 実装方法 |
|---------|---------|
| キーボードナビゲーション | shadcn/ui標準（Radix UI）ベース |
| スクリーンリーダー | aria-label, aria-describedby, role属性 |
| カラーコントラスト | WCAG 2.1 AA準拠（4.5:1以上） |
| フォーカス表示 | `focus-visible` リング |
| 言語指定 | `<html lang="ja">` |
| フォームバリデーション | aria-invalid, aria-errormessage |
| チャート代替 | テーブル形式のデータ提供 |
