"""Portfolio endpoints — generate, backtest, explain (all stateless)."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.schemas.backtest import BacktestRequest, BacktestResponse
from src.app.schemas.portfolio import (
    ExplainRequest,
    ExplainResponse,
    PortfolioGenerateRequest,
    PortfolioResponse,
)
from src.app.services.ai_advisor import AIAdvisor
from src.app.services.backtester import Backtester
from src.app.services.portfolio_optimizer import PortfolioOptimizer
from src.app.services.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("/generate", response_model=PortfolioResponse)
async def generate_portfolio(
    request: PortfolioGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate an optimised portfolio. Stateless — nothing is stored in DB."""
    optimizer = PortfolioOptimizer(db)
    try:
        result = await optimizer.optimize(
            risk_score=request.risk_score,
            risk_tolerance=request.risk_tolerance,
            investment_horizon=request.investment_horizon,
            strategy=request.strategy,
            investment_amount=request.investment_amount,
            currency=request.currency,
            constraints=request.constraints.model_dump() if request.constraints else None,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Portfolio generation failed")
        raise HTTPException(
            status_code=500,
            detail="ポートフォリオの生成に失敗しました。しばらく時間をおいて再度お試しください。",
        ) from e


@router.post("/backtest", response_model=BacktestResponse)
async def backtest_portfolio(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run a historical backtest on the given allocations. Stateless."""
    backtester = Backtester(db)
    try:
        result = await backtester.run(
            allocations=[a.model_dump() for a in request.allocations],
            period_years=request.period_years,
            initial_investment=request.initial_investment,
            rebalance_frequency=request.rebalance_frequency,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Backtest failed")
        raise HTTPException(
            status_code=500,
            detail="バックテストの実行に失敗しました。しばらく時間をおいて再度お試しください。",
        ) from e


@router.post("/explain", response_model=ExplainResponse)
async def explain_portfolio(
    request: ExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI explanation for a portfolio. Stateless."""
    tracker = UsageTracker(db)
    await tracker.check_budget()

    advisor = AIAdvisor()
    try:
        explanation, usage = await advisor.generate_explanation(
            strategy=request.strategy,
            risk_tolerance=request.risk_tolerance,
            allocations=[a.model_dump() for a in request.allocations],
            metrics=request.metrics,
        )
        await tracker.record_usage(
            endpoint="portfolios/explain",
            model="claude-sonnet-4-5-20250514",
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )
        return ExplainResponse(explanation=explanation)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Portfolio explanation failed")
        raise HTTPException(
            status_code=500,
            detail="ポートフォリオの説明生成に失敗しました。",
        ) from e
