export interface PortfolioConstraints {
  max_single_asset_weight?: number;
  include_markets?: string[];
  include_asset_types?: string[];
}

export interface PortfolioGenerateRequest {
  risk_score: number;
  risk_tolerance: string;
  investment_horizon: string;
  strategy?: string;
  investment_amount?: number;
  currency?: string;
  constraints?: PortfolioConstraints;
}

export interface AssetSummary {
  symbol: string;
  name_ja: string | null;
  asset_type: string;
  market: string;
}

export interface AllocationResponse {
  asset: AssetSummary;
  weight: number;
  amount: number | null;
}

export interface PortfolioMetrics {
  expected_return: number | null;
  volatility: number | null;
  sharpe_ratio: number | null;
}

export interface RiskProfileSummary {
  risk_score: number;
  risk_tolerance: string;
}

export interface PortfolioResponse {
  name: string | null;
  strategy: string;
  risk_profile: RiskProfileSummary;
  metrics: PortfolioMetrics;
  allocations: AllocationResponse[];
  currency: string;
}

// Backtest
export interface BacktestAllocation {
  symbol: string;
  weight: number;
}

export interface BacktestRequest {
  allocations: BacktestAllocation[];
  period_years?: number;
  initial_investment?: number;
  rebalance_frequency?: string;
}

export interface BacktestPeriod {
  start: string;
  end: string;
  years: number;
}

export interface MaxDrawdownPeriod {
  start: string | null;
  end: string | null;
}

export interface BacktestMetrics {
  final_value: number;
  total_return: number;
  cagr: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  max_drawdown_period: MaxDrawdownPeriod | null;
  sortino_ratio: number | null;
  calmar_ratio: number | null;
}

export interface BenchmarkResult {
  total_return: number;
  cagr: number;
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
  return_pct: number;
}

export interface AnnualReturn {
  year: number;
  return_pct: number;
}

export interface BacktestResponse {
  period: BacktestPeriod;
  initial_investment: number;
  metrics: BacktestMetrics;
  benchmark_comparison: Record<string, BenchmarkResult> | null;
  time_series: TimeSeriesPoint[];
  annual_returns: AnnualReturn[];
  disclaimer: string;
}

// Explain
export interface ExplainAllocationInput {
  symbol: string;
  name_ja?: string;
  weight: number;
}

export interface ExplainRequest {
  strategy: string;
  risk_tolerance: string;
  allocations: ExplainAllocationInput[];
  metrics?: Record<string, number>;
}

export interface ExplainResponse {
  explanation: string;
}
