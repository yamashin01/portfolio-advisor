"""Claude API usage tracking and budget enforcement.

Tracks daily/monthly token usage via api_usage_logs table.
Enforces DAILY_TOKEN_BUDGET and MONTHLY_TOKEN_BUDGET limits.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.models.api_usage_log import ApiUsageLog

logger = logging.getLogger(__name__)

# Claude 3.5 Sonnet pricing (per 1M tokens)
TOKEN_PRICING = {
    "claude-sonnet-4-5-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}
DEFAULT_PRICING = {"input": 3.00, "output": 15.00}


class UsageTracker:
    """Claude API usage tracking and budget enforcement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_budget(self) -> None:
        """Check daily and monthly token budgets.

        Raises HTTPException(429) if either budget is exceeded.
        """
        daily = await self._get_daily_usage()
        if daily["total_tokens"] >= settings.DAILY_TOKEN_BUDGET:
            raise HTTPException(
                status_code=429,
                detail="本日のAI利用上限に達しました。明日以降に再度お試しください。",
            )

        monthly = await self._get_monthly_usage()
        if monthly["total_tokens"] >= settings.MONTHLY_TOKEN_BUDGET:
            raise HTTPException(
                status_code=429,
                detail="今月のAI利用上限に達しました。来月以降に再度お試しください。",
            )

    async def record_usage(
        self,
        endpoint: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record a usage entry to api_usage_logs."""
        cost = self._estimate_cost(model, input_tokens, output_tokens)
        log = ApiUsageLog(
            endpoint=endpoint,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=Decimal(str(round(cost, 6))),
        )
        self.session.add(log)
        await self.session.flush()
        logger.info(
            "Usage recorded: %s %s input=%d output=%d cost=$%.4f",
            endpoint, model, input_tokens, output_tokens, cost,
        )

    async def get_usage_summary(self) -> dict:
        """Return daily and monthly usage summaries."""
        daily = await self._get_daily_usage()
        monthly = await self._get_monthly_usage()

        return {
            "daily": {
                "date": date.today().isoformat(),
                "input_tokens": daily["input_tokens"],
                "output_tokens": daily["output_tokens"],
                "total_tokens": daily["total_tokens"],
                "estimated_cost_usd": round(daily["estimated_cost_usd"], 4),
                "budget_tokens": settings.DAILY_TOKEN_BUDGET,
                "remaining_tokens": max(0, settings.DAILY_TOKEN_BUDGET - daily["total_tokens"]),
            },
            "monthly": {
                "month": date.today().strftime("%Y-%m"),
                "input_tokens": monthly["input_tokens"],
                "output_tokens": monthly["output_tokens"],
                "total_tokens": monthly["total_tokens"],
                "estimated_cost_usd": round(monthly["estimated_cost_usd"], 4),
                "budget_tokens": settings.MONTHLY_TOKEN_BUDGET,
                "remaining_tokens": max(0, settings.MONTHLY_TOKEN_BUDGET - monthly["total_tokens"]),
            },
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    async def _get_daily_usage(self) -> dict:
        today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
        return await self._aggregate_usage(today_start)

    async def _get_monthly_usage(self) -> dict:
        month_start = datetime(
            date.today().year, date.today().month, 1, tzinfo=timezone.utc,
        )
        return await self._aggregate_usage(month_start)

    async def _aggregate_usage(self, since: datetime) -> dict:
        result = await self.session.execute(
            sa.select(
                sa.func.coalesce(sa.func.sum(ApiUsageLog.input_tokens), 0).label("input_tokens"),
                sa.func.coalesce(sa.func.sum(ApiUsageLog.output_tokens), 0).label("output_tokens"),
                sa.func.coalesce(sa.func.sum(ApiUsageLog.estimated_cost_usd), 0).label("estimated_cost_usd"),
            ).where(ApiUsageLog.created_at >= since),
        )
        row = result.one()
        input_t = int(row.input_tokens)
        output_t = int(row.output_tokens)
        return {
            "input_tokens": input_t,
            "output_tokens": output_t,
            "total_tokens": input_t + output_t,
            "estimated_cost_usd": float(row.estimated_cost_usd),
        }

    @staticmethod
    def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = TOKEN_PRICING.get(model, DEFAULT_PRICING)
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
