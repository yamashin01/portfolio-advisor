"""Tests for backtester service."""

import numpy as np
import pandas as pd

from src.app.services.backtester import Backtester


class TestBacktesterPureMethods:
    """Test pure computation methods (no DB dependency)."""

    def setup_method(self):
        self.backtester = Backtester(session=None)

    def test_simulate_no_rebalance(self):
        dates = pd.bdate_range("2024-01-01", periods=100)
        prices = pd.DataFrame(
            {
                "A": np.linspace(100, 120, 100),
                "B": np.linspace(50, 55, 100),
            },
            index=dates,
        )
        weights = {"A": 0.6, "B": 0.4}
        pv = self.backtester._simulate(prices, weights, 1_000_000, rebalance_interval=0)
        assert len(pv) == 100
        assert pv.iloc[0] == 1_000_000
        assert pv.iloc[-1] > 1_000_000  # prices went up

    def test_simulate_with_rebalance(self):
        dates = pd.bdate_range("2024-01-01", periods=100)
        prices = pd.DataFrame(
            {
                "A": np.linspace(100, 120, 100),
                "B": np.linspace(50, 55, 100),
            },
            index=dates,
        )
        weights = {"A": 0.5, "B": 0.5}
        pv = self.backtester._simulate(prices, weights, 1_000_000, rebalance_interval=30)
        assert len(pv) == 100
        assert pv.iloc[0] == 1_000_000

    def test_compute_metrics(self):
        dates = pd.bdate_range("2024-01-01", periods=252)
        np.random.seed(42)
        values = 1_000_000 * np.cumprod(1 + np.random.normal(0.0004, 0.01, 252))
        pv = pd.Series(values, index=dates)

        metrics = self.backtester._compute_metrics(pv, 1_000_000)

        assert "final_value" in metrics
        assert "total_return" in metrics
        assert "cagr" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "max_drawdown_period" in metrics
        assert "sortino_ratio" in metrics
        assert "calmar_ratio" in metrics
        assert metrics["max_drawdown"] <= 0  # drawdown is negative

    def test_build_time_series(self):
        dates = pd.bdate_range("2024-01-01", periods=500)
        pv = pd.Series(np.linspace(1_000_000, 1_200_000, 500), index=dates)

        ts = self.backtester._build_time_series(pv, 1_000_000)
        assert len(ts) <= 251  # max ~250 + 1
        assert ts[0]["date"] == dates[0].strftime("%Y-%m-%d")
        assert ts[-1]["date"] == dates[-1].strftime("%Y-%m-%d")
        assert ts[0]["return_pct"] == 0.0  # first point: 0% return relative to initial
        assert ts[-1]["return_pct"] > 0

    def test_compute_annual_returns(self):
        dates = pd.bdate_range("2022-01-03", periods=504)
        pv = pd.Series(np.linspace(1_000_000, 1_500_000, 504), index=dates)

        annual = self.backtester._compute_annual_returns(pv)
        assert len(annual) >= 2
        assert all("year" in a and "return_pct" in a for a in annual)
        # Each year should have positive returns (linear growth)
        for a in annual:
            assert a["return_pct"] > 0

    def test_compute_metrics_drawdown_period(self):
        """Drawdown period should have valid start/end dates."""
        dates = pd.bdate_range("2024-01-01", periods=100)
        # Create a V-shaped portfolio value
        values = list(np.linspace(1_000_000, 800_000, 50)) + list(
            np.linspace(800_000, 1_100_000, 50)
        )
        pv = pd.Series(values, index=dates)

        metrics = self.backtester._compute_metrics(pv, 1_000_000)
        assert metrics["max_drawdown_period"]["start"] is not None
        assert metrics["max_drawdown_period"]["end"] is not None
