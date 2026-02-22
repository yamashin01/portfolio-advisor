import { describe, it, expect, beforeEach } from "vitest";
import { usePortfolioResultStore } from "./portfolio-result-store";
import type { PortfolioResponse, BacktestResponse } from "@/types/portfolio";

const mockPortfolio: PortfolioResponse = {
  name: "テストポートフォリオ",
  strategy: "hrp",
  risk_profile: { risk_score: 5, risk_tolerance: "moderate" },
  metrics: { expected_return: 0.08, volatility: 0.12, sharpe_ratio: 0.5 },
  allocations: [
    {
      asset: { symbol: "SPY", name_ja: "S&P 500 ETF", asset_type: "etf", market: "us" },
      weight: 0.6,
      amount: null,
    },
  ],
  currency: "JPY",
};

const mockBacktest: BacktestResponse = {
  period: { start: "2020-01-01", end: "2024-12-31", years: 5 },
  initial_investment: 1000000,
  metrics: {
    final_value: 1500000,
    total_return: 0.5,
    cagr: 0.084,
    volatility: 0.12,
    sharpe_ratio: 0.6,
    max_drawdown: -0.15,
    max_drawdown_period: { start: "2020-03-01", end: "2020-03-23" },
    sortino_ratio: 0.8,
    calmar_ratio: 0.56,
  },
  benchmark_comparison: null,
  time_series: [],
  annual_returns: [],
};

describe("usePortfolioResultStore", () => {
  beforeEach(() => {
    usePortfolioResultStore.setState({
      portfolio: null,
      backtest: null,
      explanation: null,
    });
  });

  it("has correct initial state", () => {
    const state = usePortfolioResultStore.getState();
    expect(state.portfolio).toBeNull();
    expect(state.backtest).toBeNull();
    expect(state.explanation).toBeNull();
  });

  it("stores portfolio", () => {
    usePortfolioResultStore.getState().setPortfolio(mockPortfolio);
    expect(usePortfolioResultStore.getState().portfolio).toEqual(mockPortfolio);
  });

  it("stores backtest", () => {
    usePortfolioResultStore.getState().setBacktest(mockBacktest);
    expect(usePortfolioResultStore.getState().backtest).toEqual(mockBacktest);
  });

  it("stores explanation", () => {
    usePortfolioResultStore.getState().setExplanation("テスト説明");
    expect(usePortfolioResultStore.getState().explanation).toBe("テスト説明");
  });

  it("clears all state", () => {
    const store = usePortfolioResultStore.getState();
    store.setPortfolio(mockPortfolio);
    store.setBacktest(mockBacktest);
    store.setExplanation("テスト");
    store.clear();

    const state = usePortfolioResultStore.getState();
    expect(state.portfolio).toBeNull();
    expect(state.backtest).toBeNull();
    expect(state.explanation).toBeNull();
  });
});
