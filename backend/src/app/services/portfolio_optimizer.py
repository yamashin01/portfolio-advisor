"""Portfolio optimization engine using PyPortfolioOpt.

Supports strategies:
- min_volatility: Minimum variance portfolio
- hrp: Hierarchical Risk Parity
- max_sharpe: Maximum Sharpe ratio
- risk_parity: Risk parity (equal risk contribution)
- equal_weight: 1/N allocation

Uses Ledoit-Wolf shrinkage for covariance estimation.
"""

import logging

import numpy as np
import pandas as pd
from pypfopt import (
    CovarianceShrinkage,
    EfficientFrontier,
    HRPOpt,
    expected_returns,
    risk_models,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.asset import Asset
from src.app.models.asset_price import AssetPrice
from src.app.models.economic_indicator import EconomicIndicator

logger = logging.getLogger(__name__)

# Asset allocation guidelines by risk tolerance
ALLOCATION_GUIDELINES = {
    "conservative": {
        "bond": (0.50, 0.70),
        "etf": (0.20, 0.40),
        "reit": (0.00, 0.10),
    },
    "moderate": {
        "bond": (0.20, 0.40),
        "etf": (0.40, 0.60),
        "reit": (0.05, 0.15),
    },
    "aggressive": {
        "bond": (0.05, 0.20),
        "etf": (0.60, 0.90),
        "reit": (0.05, 0.15),
    },
}

STRATEGY_NAMES = {
    "min_volatility": "安定重視ポートフォリオ",
    "hrp": "バランス型ポートフォリオ",
    "max_sharpe": "積極型ポートフォリオ",
    "risk_parity": "リスクパリティポートフォリオ",
    "equal_weight": "均等配分ポートフォリオ",
}


class PortfolioOptimizer:
    """PyPortfolioOpt-based portfolio optimization engine."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def optimize(
        self,
        risk_score: int,
        risk_tolerance: str,
        investment_horizon: str,
        strategy: str = "auto",
        investment_amount: int | None = None,
        currency: str = "JPY",
        constraints: dict | None = None,
    ) -> dict:
        """Main entry point for portfolio optimization.

        Returns a dict matching PortfolioResponse schema.
        """
        # Auto-select strategy
        if strategy == "auto":
            strategy = self._auto_select_strategy(risk_tolerance)

        # Select assets
        assets = await self._select_assets(risk_tolerance, constraints)
        if len(assets) < 2:
            raise ValueError("対象資産が不足しています。少なくとも2銘柄以上の価格データが必要です。")

        # Get price matrix
        prices_df = await self._get_price_matrix(assets)
        if prices_df.empty or len(prices_df.columns) < 2:
            raise ValueError("価格データが不足しています。市場データの更新が必要です。")

        # Drop columns with too many NaN
        min_data_points = 60
        valid_cols = prices_df.columns[prices_df.count() >= min_data_points]
        prices_df = prices_df[valid_cols]
        if len(prices_df.columns) < 2:
            raise ValueError("十分な価格データがある銘柄が不足しています。")

        # Forward-fill then drop remaining NaN rows
        prices_df = prices_df.ffill().dropna()

        # Calculate returns
        returns_df = self._calculate_returns(prices_df)

        # Get risk-free rate
        risk_free_rate = await self._get_risk_free_rate()

        # Optimize based on strategy
        try:
            if strategy == "min_volatility":
                weights = self._optimize_min_volatility(returns_df, prices_df, constraints)
            elif strategy == "hrp":
                weights = self._optimize_hrp(returns_df)
            elif strategy == "max_sharpe":
                weights = self._optimize_max_sharpe(returns_df, prices_df, risk_free_rate, constraints)
            elif strategy == "risk_parity":
                weights = self._optimize_risk_parity(returns_df)
            elif strategy == "equal_weight":
                weights = self._optimize_equal_weight(prices_df.columns.tolist())
            else:
                weights = self._optimize_hrp(returns_df)
        except Exception as e:
            logger.warning(f"Optimization failed for {strategy}: {e}. Falling back to equal_weight.")
            weights = self._optimize_equal_weight(prices_df.columns.tolist())
            strategy = "equal_weight"

        # Filter out near-zero weights
        weights = {k: v for k, v in weights.items() if v > 0.001}

        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        # Calculate metrics
        metrics = self._calculate_metrics(weights, returns_df, risk_free_rate)

        # Build asset lookup
        asset_map = {a.symbol: a for a in assets}

        # Build allocations
        allocations = []
        for symbol, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            asset = asset_map.get(symbol)
            if not asset:
                continue
            amount = round(investment_amount * weight) if investment_amount else None
            allocations.append({
                "asset": {
                    "symbol": asset.symbol,
                    "name_ja": asset.name_ja,
                    "asset_type": asset.asset_type,
                    "market": asset.market,
                },
                "weight": round(weight, 4),
                "amount": amount,
            })

        return {
            "name": STRATEGY_NAMES.get(strategy, strategy),
            "strategy": strategy,
            "risk_profile": {
                "risk_score": risk_score,
                "risk_tolerance": risk_tolerance,
            },
            "metrics": metrics,
            "allocations": allocations,
            "currency": currency,
        }

    def _auto_select_strategy(self, risk_tolerance: str) -> str:
        strategy_map = {
            "conservative": "min_volatility",
            "moderate": "hrp",
            "aggressive": "max_sharpe",
        }
        return strategy_map.get(risk_tolerance, "hrp")

    async def _select_assets(self, risk_tolerance: str, constraints: dict | None = None) -> list[Asset]:
        """Select assets based on risk tolerance and constraints."""
        query = select(Asset).where(Asset.is_active.is_(True))

        if constraints:
            if "include_markets" in constraints:
                query = query.where(Asset.market.in_(constraints["include_markets"]))
            if "include_asset_types" in constraints:
                query = query.where(Asset.asset_type.in_(constraints["include_asset_types"]))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_price_matrix(self, assets: list[Asset]) -> pd.DataFrame:
        """Build a price DataFrame (columns=symbols, index=date) from DB."""
        asset_ids = {a.id: a.symbol for a in assets}

        result = await self.session.execute(
            select(AssetPrice)
            .where(AssetPrice.asset_id.in_(asset_ids.keys()))
            .order_by(AssetPrice.date)
        )
        prices = result.scalars().all()

        if not prices:
            return pd.DataFrame()

        # Build dict of {symbol: {date: close_price}}
        data: dict[str, dict] = {}
        for p in prices:
            symbol = asset_ids.get(p.asset_id)
            if symbol:
                if symbol not in data:
                    data[symbol] = {}
                close = float(p.adj_close) if p.adj_close else float(p.close)
                data[symbol][p.date] = close

        df = pd.DataFrame(data)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df

    def _calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns."""
        return prices.pct_change().dropna()

    async def _get_risk_free_rate(self) -> float:
        """Get US 10-Year Treasury yield as risk-free rate."""
        result = await self.session.execute(
            select(EconomicIndicator)
            .where(EconomicIndicator.indicator_type == "us_treasury_10y")
            .order_by(EconomicIndicator.date.desc())
            .limit(1)
        )
        indicator = result.scalar_one_or_none()
        if indicator:
            return float(indicator.value) / 100  # Convert percentage to decimal
        return 0.04  # Default 4%

    def _optimize_min_volatility(
        self, returns: pd.DataFrame, prices: pd.DataFrame, constraints: dict | None
    ) -> dict[str, float]:
        """Minimum variance optimization."""
        mu = expected_returns.mean_historical_return(prices)
        S = CovarianceShrinkage(prices).ledoit_wolf()

        max_weight = 0.30
        if constraints and "max_single_asset_weight" in constraints:
            max_weight = constraints["max_single_asset_weight"]

        ef = EfficientFrontier(mu, S, weight_bounds=(0, max_weight))
        ef.min_volatility()
        return dict(ef.clean_weights())

    def _optimize_hrp(self, returns: pd.DataFrame) -> dict[str, float]:
        """Hierarchical Risk Parity optimization."""
        hrp = HRPOpt(returns)
        hrp.optimize()
        return dict(hrp.clean_weights())

    def _optimize_max_sharpe(
        self, returns: pd.DataFrame, prices: pd.DataFrame, risk_free_rate: float, constraints: dict | None
    ) -> dict[str, float]:
        """Maximum Sharpe ratio optimization."""
        mu = expected_returns.mean_historical_return(prices)
        S = CovarianceShrinkage(prices).ledoit_wolf()

        max_weight = 0.30
        if constraints and "max_single_asset_weight" in constraints:
            max_weight = constraints["max_single_asset_weight"]

        ef = EfficientFrontier(mu, S, weight_bounds=(0, max_weight))
        ef.max_sharpe(risk_free_rate=risk_free_rate)
        return dict(ef.clean_weights())

    def _optimize_risk_parity(self, returns: pd.DataFrame) -> dict[str, float]:
        """Risk parity: equal risk contribution from each asset."""
        cov = returns.cov().values
        n = cov.shape[0]

        # Inverse volatility as starting point
        vols = np.sqrt(np.diag(cov))
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()

        # Simple iterative risk parity
        for _ in range(100):
            port_vol = np.sqrt(weights @ cov @ weights)
            marginal_risk = (cov @ weights) / port_vol
            risk_contribution = weights * marginal_risk
            target_risk = port_vol / n

            adjustment = target_risk / risk_contribution
            weights = weights * adjustment
            weights = weights / weights.sum()

        return dict(zip(returns.columns, weights, strict=False))

    def _optimize_equal_weight(self, symbols: list[str]) -> dict[str, float]:
        """Equal weight allocation (1/N)."""
        n = len(symbols)
        weight = 1.0 / n
        return {s: weight for s in symbols}

    def _calculate_metrics(
        self, weights: dict[str, float], returns: pd.DataFrame, risk_free_rate: float
    ) -> dict:
        """Calculate expected return, volatility, Sharpe ratio."""
        symbols = list(weights.keys())
        available = [s for s in symbols if s in returns.columns]
        if not available:
            return {"expected_return": None, "volatility": None, "sharpe_ratio": None}

        w = np.array([weights[s] for s in available])
        w = w / w.sum()  # Renormalize

        ret = returns[available]
        mean_returns = ret.mean() * 252  # Annualize
        cov_matrix = ret.cov() * 252

        expected_return = float(w @ mean_returns)
        volatility = float(np.sqrt(w @ cov_matrix @ w))
        sharpe_ratio = (
            float((expected_return - risk_free_rate) / volatility) if volatility > 0 else 0.0
        )

        return {
            "expected_return": round(expected_return, 4),
            "volatility": round(volatility, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
        }
