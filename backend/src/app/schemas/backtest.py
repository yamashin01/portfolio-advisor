"""Backtest-related Pydantic schemas."""

from pydantic import BaseModel, Field


# --- Request schemas ---

class BacktestAllocation(BaseModel):
    symbol: str
    weight: float = Field(..., ge=0, le=1)


class BacktestRequest(BaseModel):
    allocations: list[BacktestAllocation] = Field(..., min_length=1)
    period_years: int = Field(default=5, ge=1, le=20)
    initial_investment: float = Field(default=1_000_000, gt=0)
    rebalance_frequency: str = Field(
        default="quarterly",
        pattern="^(monthly|quarterly|annually|none)$",
    )


# --- Response schemas ---

class BacktestPeriod(BaseModel):
    start: str
    end: str
    years: int


class MaxDrawdownPeriod(BaseModel):
    start: str | None = None
    end: str | None = None


class BacktestMetrics(BaseModel):
    final_value: float
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_period: MaxDrawdownPeriod | None = None
    sortino_ratio: float | None = None
    calmar_ratio: float | None = None


class BenchmarkResult(BaseModel):
    total_return: float
    cagr: float


class TimeSeriesPoint(BaseModel):
    date: str
    value: float
    return_pct: float


class AnnualReturn(BaseModel):
    year: int
    return_pct: float  # renamed from `return` (reserved keyword)


class BacktestResponse(BaseModel):
    period: BacktestPeriod
    initial_investment: float
    metrics: BacktestMetrics
    benchmark_comparison: dict[str, BenchmarkResult] | None = None
    time_series: list[TimeSeriesPoint]
    annual_returns: list[AnnualReturn]
    disclaimer: str = (
        "※ 過去のパフォーマンスは将来の結果を保証するものではありません。"
        "バックテストは仮想的なシミュレーションであり、"
        "実際の取引コスト・税金は考慮されていません。"
    )
