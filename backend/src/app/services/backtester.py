"""Historical backtest engine for portfolio allocations.

Simulates portfolio performance over a given period with periodic rebalancing.
Computes standard risk/return metrics and benchmark comparisons.
"""

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.asset import Asset
from src.app.models.asset_price import AssetPrice

logger = logging.getLogger(__name__)

# Benchmark symbols: Nikkei225 ETF and S&P500 ETF
BENCHMARKS = {
    "nikkei225": "1321.T",
    "sp500": "SPY",
}

REBALANCE_DAYS = {
    "monthly": 30,
    "quarterly": 90,
    "annually": 365,
    "none": 0,
}


class Backtester:
    """Historical backtest simulator."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run(
        self,
        allocations: list[dict],
        period_years: int = 5,
        initial_investment: float = 1_000_000,
        rebalance_frequency: str = "quarterly",
    ) -> dict:
        """Execute a historical backtest.

        Parameters
        ----------
        allocations : list[dict]
            Each item must have "symbol" and "weight" keys.
        period_years : int
            Look-back period in years.
        initial_investment : float
            Starting portfolio value.
        rebalance_frequency : str
            One of "monthly", "quarterly", "annually", "none".

        Returns
        -------
        dict matching BacktestResponse schema.
        """
        symbols = [a["symbol"] for a in allocations]
        weights = {a["symbol"]: a["weight"] for a in allocations}

        end_date = date.today()
        start_date = end_date - timedelta(days=period_years * 365)

        # Fetch price matrix
        prices_df = await self._get_price_matrix(symbols, start_date, end_date)
        if prices_df.empty or len(prices_df.columns) == 0:
            raise ValueError("バックテストに必要な価格データが不足しています。")

        # Keep only symbols that have price data
        available = [s for s in symbols if s in prices_df.columns]
        if not available:
            raise ValueError("価格データのある銘柄が見つかりませんでした。")

        # Re-normalise weights to available symbols
        w_total = sum(weights[s] for s in available)
        norm_weights = {s: weights[s] / w_total for s in available}

        # Forward-fill and drop leading NaN rows
        prices_df = prices_df[available].ffill().dropna()
        if len(prices_df) < 2:
            raise ValueError("バックテスト期間の価格データが不足しています。")

        # --- Portfolio value simulation ---
        rebalance_interval = REBALANCE_DAYS.get(rebalance_frequency, 90)
        portfolio_values = self._simulate(
            prices_df, norm_weights, initial_investment, rebalance_interval,
        )

        # --- Metrics ---
        metrics = self._compute_metrics(portfolio_values, initial_investment)

        # --- Benchmark comparison ---
        benchmark_comparison = await self._compute_benchmarks(start_date, end_date, period_years)

        # --- Time series (sampled for reasonable payload size) ---
        time_series = self._build_time_series(portfolio_values, initial_investment)

        # --- Annual returns ---
        annual_returns = self._compute_annual_returns(portfolio_values)

        actual_start = portfolio_values.index[0].strftime("%Y-%m-%d")
        actual_end = portfolio_values.index[-1].strftime("%Y-%m-%d")

        return {
            "period": {
                "start": actual_start,
                "end": actual_end,
                "years": period_years,
            },
            "initial_investment": initial_investment,
            "metrics": metrics,
            "benchmark_comparison": benchmark_comparison if benchmark_comparison else None,
            "time_series": time_series,
            "annual_returns": annual_returns,
        }

    # ------------------------------------------------------------------ #
    #  Price data
    # ------------------------------------------------------------------ #

    async def _get_price_matrix(
        self, symbols: list[str], start_date: date, end_date: date,
    ) -> pd.DataFrame:
        """Build price DataFrame from DB for given symbols & date range."""
        # Map symbol → asset_id
        result = await self.session.execute(
            select(Asset).where(Asset.symbol.in_(symbols)),
        )
        assets = result.scalars().all()
        if not assets:
            return pd.DataFrame()

        asset_id_map = {a.id: a.symbol for a in assets}

        result = await self.session.execute(
            select(AssetPrice)
            .where(
                AssetPrice.asset_id.in_(asset_id_map.keys()),
                AssetPrice.date >= start_date,
                AssetPrice.date <= end_date,
            )
            .order_by(AssetPrice.date),
        )
        prices = result.scalars().all()

        if not prices:
            return pd.DataFrame()

        data: dict[str, dict] = {}
        for p in prices:
            sym = asset_id_map.get(p.asset_id)
            if sym:
                if sym not in data:
                    data[sym] = {}
                close = float(p.adj_close) if p.adj_close else float(p.close)
                data[sym][p.date] = close

        df = pd.DataFrame(data)
        df.index = pd.to_datetime(df.index)
        return df.sort_index()

    # ------------------------------------------------------------------ #
    #  Simulation
    # ------------------------------------------------------------------ #

    def _simulate(
        self,
        prices: pd.DataFrame,
        weights: dict[str, float],
        initial_investment: float,
        rebalance_interval: int,
    ) -> pd.Series:
        """Simulate daily portfolio value with optional rebalancing."""
        symbols = list(weights.keys())
        daily_returns = prices[symbols].pct_change().fillna(0)

        n_days = len(daily_returns)
        portfolio_value = np.empty(n_days)
        portfolio_value[0] = initial_investment

        # Current allocation in monetary terms
        w_arr = np.array([weights[s] for s in symbols])
        holdings = initial_investment * w_arr  # dollar value per asset

        days_since_rebalance = 0

        for i in range(1, n_days):
            ret = daily_returns.iloc[i].values
            holdings = holdings * (1 + ret)
            total = holdings.sum()
            portfolio_value[i] = total

            days_since_rebalance += 1
            if rebalance_interval > 0 and days_since_rebalance >= rebalance_interval:
                holdings = total * w_arr
                days_since_rebalance = 0

        return pd.Series(portfolio_value, index=daily_returns.index)

    # ------------------------------------------------------------------ #
    #  Metrics
    # ------------------------------------------------------------------ #

    def _compute_metrics(self, pv: pd.Series, initial: float) -> dict:
        final_value = float(pv.iloc[-1])
        total_return = (final_value - initial) / initial

        n_days = len(pv)
        n_years = n_days / 252
        cagr = (final_value / initial) ** (1 / n_years) - 1 if n_years > 0 else 0.0

        daily_returns = pv.pct_change().dropna()
        volatility = float(daily_returns.std() * np.sqrt(252))

        risk_free_daily = 0.04 / 252
        excess = daily_returns - risk_free_daily
        sharpe = float(excess.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0.0

        # Max drawdown
        cummax = pv.cummax()
        drawdown = (pv - cummax) / cummax
        max_dd = float(drawdown.min())

        # Max drawdown period
        dd_end_idx = drawdown.idxmin()
        dd_start_idx = pv[:dd_end_idx].idxmax()
        max_dd_period = {
            "start": dd_start_idx.strftime("%Y-%m-%d"),
            "end": dd_end_idx.strftime("%Y-%m-%d"),
        }

        # Sortino ratio (downside deviation)
        downside = daily_returns[daily_returns < 0]
        downside_std = float(downside.std() * np.sqrt(252)) if len(downside) > 0 else 0.0
        sortino = float((cagr - 0.04) / downside_std) if downside_std > 0 else 0.0

        # Calmar ratio
        calmar = float(cagr / abs(max_dd)) if max_dd != 0 else 0.0

        return {
            "final_value": round(final_value, 0),
            "total_return": round(total_return, 4),
            "cagr": round(cagr, 4),
            "volatility": round(volatility, 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_dd, 4),
            "max_drawdown_period": max_dd_period,
            "sortino_ratio": round(sortino, 4),
            "calmar_ratio": round(calmar, 4),
        }

    # ------------------------------------------------------------------ #
    #  Benchmarks
    # ------------------------------------------------------------------ #

    async def _compute_benchmarks(
        self, start_date: date, end_date: date, period_years: int,
    ) -> dict | None:
        benchmarks = {}
        for name, symbol in BENCHMARKS.items():
            result = await self.session.execute(
                select(Asset).where(Asset.symbol == symbol),
            )
            asset = result.scalar_one_or_none()
            if not asset:
                continue

            result = await self.session.execute(
                select(AssetPrice)
                .where(
                    AssetPrice.asset_id == asset.id,
                    AssetPrice.date >= start_date,
                    AssetPrice.date <= end_date,
                )
                .order_by(AssetPrice.date),
            )
            prices = result.scalars().all()
            if len(prices) < 2:
                continue

            first = float(prices[0].adj_close or prices[0].close)
            last = float(prices[-1].adj_close or prices[-1].close)
            if first <= 0:
                continue

            total_return = (last - first) / first
            n_years = len(prices) / 252
            bench_cagr = (last / first) ** (1 / n_years) - 1 if n_years > 0 else 0.0

            benchmarks[name] = {
                "total_return": round(total_return, 4),
                "cagr": round(bench_cagr, 4),
            }

        return benchmarks if benchmarks else None

    # ------------------------------------------------------------------ #
    #  Time series
    # ------------------------------------------------------------------ #

    def _build_time_series(
        self, pv: pd.Series, initial: float,
    ) -> list[dict]:
        """Build time series for charting. Sample to ~250 points max."""
        n = len(pv)
        step = max(1, n // 250)
        sampled = pv.iloc[::step]
        # Always include last point
        if sampled.index[-1] != pv.index[-1]:
            sampled = pd.concat([sampled, pv.iloc[[-1]]])

        return [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "value": round(float(val), 0),
                "return_pct": round((float(val) - initial) / initial, 4),
            }
            for idx, val in sampled.items()
        ]

    # ------------------------------------------------------------------ #
    #  Annual returns
    # ------------------------------------------------------------------ #

    def _compute_annual_returns(self, pv: pd.Series) -> list[dict]:
        annual = []
        years = sorted(set(pv.index.year))
        for year in years:
            year_data = pv[pv.index.year == year]
            if len(year_data) < 2:
                continue
            start_val = float(year_data.iloc[0])
            end_val = float(year_data.iloc[-1])
            ret = (end_val - start_val) / start_val if start_val > 0 else 0.0
            annual.append({"year": year, "return_pct": round(ret, 4)})
        return annual
