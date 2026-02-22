"""Tests for portfolio optimizer service."""

import numpy as np
import pandas as pd
import pytest

from src.app.services.portfolio_optimizer import PortfolioOptimizer


class TestPortfolioOptimizerPureMethods:
    """Test pure computation methods (no DB dependency)."""

    def setup_method(self):
        # Pass None as session — only testing pure methods
        self.optimizer = PortfolioOptimizer(session=None)

    def test_auto_select_strategy_conservative(self):
        assert self.optimizer._auto_select_strategy("conservative") == "min_volatility"

    def test_auto_select_strategy_moderate(self):
        assert self.optimizer._auto_select_strategy("moderate") == "hrp"

    def test_auto_select_strategy_aggressive(self):
        assert self.optimizer._auto_select_strategy("aggressive") == "max_sharpe"

    def test_auto_select_strategy_unknown(self):
        assert self.optimizer._auto_select_strategy("unknown") == "hrp"

    def test_equal_weight(self):
        symbols = ["SPY", "AGG", "VNQ"]
        weights = self.optimizer._optimize_equal_weight(symbols)
        assert len(weights) == 3
        for w in weights.values():
            assert abs(w - 1 / 3) < 1e-10
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_equal_weight_single(self):
        weights = self.optimizer._optimize_equal_weight(["SPY"])
        assert weights["SPY"] == 1.0

    def test_calculate_returns(self):
        dates = pd.date_range("2024-01-01", periods=5)
        prices = pd.DataFrame(
            {"A": [100, 102, 101, 105, 110], "B": [50, 51, 49, 52, 55]},
            index=dates,
        )
        returns = self.optimizer._calculate_returns(prices)
        assert len(returns) == 4  # one less due to pct_change().dropna()
        assert "A" in returns.columns
        assert "B" in returns.columns

    def test_calculate_metrics(self):
        np.random.seed(42)
        dates = pd.bdate_range("2023-01-01", periods=252)
        returns = pd.DataFrame(
            {
                "A": np.random.normal(0.0004, 0.01, 252),
                "B": np.random.normal(0.0003, 0.008, 252),
            },
            index=dates,
        )
        weights = {"A": 0.6, "B": 0.4}
        metrics = self.optimizer._calculate_metrics(weights, returns, risk_free_rate=0.04)

        assert "expected_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert metrics["volatility"] > 0

    def test_calculate_metrics_missing_symbols(self):
        returns = pd.DataFrame({"A": [0.01, -0.02, 0.03]})
        weights = {"X": 0.5, "Y": 0.5}
        metrics = self.optimizer._calculate_metrics(weights, returns, 0.04)
        assert metrics["expected_return"] is None

    def test_optimize_hrp(self):
        np.random.seed(42)
        dates = pd.bdate_range("2023-01-01", periods=252)
        returns = pd.DataFrame(
            {
                "A": np.random.normal(0.0004, 0.01, 252),
                "B": np.random.normal(0.0003, 0.008, 252),
                "C": np.random.normal(0.0002, 0.012, 252),
            },
            index=dates,
        )
        weights = self.optimizer._optimize_hrp(returns)
        assert len(weights) == 3
        assert abs(sum(w for w in weights.values() if w > 0) - 1.0) < 0.01

    def test_optimize_risk_parity(self):
        np.random.seed(42)
        dates = pd.bdate_range("2023-01-01", periods=252)
        returns = pd.DataFrame(
            {
                "A": np.random.normal(0.0004, 0.01, 252),
                "B": np.random.normal(0.0003, 0.02, 252),
            },
            index=dates,
        )
        weights = self.optimizer._optimize_risk_parity(returns)
        assert len(weights) == 2
        assert abs(sum(weights.values()) - 1.0) < 0.01
        # Lower-vol asset should get higher weight
        assert weights["A"] > weights["B"]
