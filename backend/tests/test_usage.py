"""Tests for usage tracker service."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.app.services.usage_tracker import UsageTracker


class TestUsageTrackerEstimateCost:
    """Test the static cost estimation method."""

    def test_known_model(self):
        cost = UsageTracker._estimate_cost(
            "claude-sonnet-4-20250514", input_tokens=1000, output_tokens=500
        )
        # input: 1000 * 3.00 / 1M = 0.003, output: 500 * 15.00 / 1M = 0.0075
        expected = (1000 * 3.00 + 500 * 15.00) / 1_000_000
        assert abs(cost - expected) < 1e-8

    def test_unknown_model_uses_default(self):
        cost = UsageTracker._estimate_cost(
            "unknown-model", input_tokens=1000, output_tokens=500
        )
        expected = (1000 * 3.00 + 500 * 15.00) / 1_000_000
        assert abs(cost - expected) < 1e-8

    def test_haiku_model(self):
        cost = UsageTracker._estimate_cost(
            "claude-haiku-4-5-20251001", input_tokens=10000, output_tokens=2000
        )
        expected = (10000 * 0.80 + 2000 * 4.00) / 1_000_000
        assert abs(cost - expected) < 1e-8

    def test_zero_tokens(self):
        cost = UsageTracker._estimate_cost("claude-sonnet-4-20250514", 0, 0)
        assert cost == 0.0


class TestUsageTrackerCheckBudget:
    """Test budget checking with mocked DB."""

    @pytest.mark.asyncio
    async def test_budget_passes(self):
        session = AsyncMock()
        row = MagicMock()
        row.input_tokens = 100
        row.output_tokens = 200
        row.estimated_cost_usd = Decimal("0.001")
        mock_result = MagicMock()
        mock_result.one.return_value = row
        session.execute.return_value = mock_result

        tracker = UsageTracker(session)
        # Should not raise
        await tracker.check_budget()

    @pytest.mark.asyncio
    async def test_daily_budget_exceeded(self):
        session = AsyncMock()
        row = MagicMock()
        row.input_tokens = 50000
        row.output_tokens = 60000  # total > 100000 default
        row.estimated_cost_usd = Decimal("1.0")
        mock_result = MagicMock()
        mock_result.one.return_value = row
        session.execute.return_value = mock_result

        tracker = UsageTracker(session)
        with pytest.raises(HTTPException) as exc_info:
            await tracker.check_budget()
        assert exc_info.value.status_code == 429
        assert "本日" in exc_info.value.detail


class TestUsageTrackerRecordUsage:
    @pytest.mark.asyncio
    async def test_record_usage(self):
        session = AsyncMock()
        tracker = UsageTracker(session)

        await tracker.record_usage(
            endpoint="chat",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
        )

        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        added_log = session.add.call_args[0][0]
        assert added_log.endpoint == "chat"
        assert added_log.input_tokens == 1000
        assert added_log.output_tokens == 500


class TestUsageTrackerSummary:
    @pytest.mark.asyncio
    async def test_get_usage_summary(self):
        session = AsyncMock()
        row = MagicMock()
        row.input_tokens = 5000
        row.output_tokens = 3000
        row.estimated_cost_usd = Decimal("0.05")
        mock_result = MagicMock()
        mock_result.one.return_value = row
        session.execute.return_value = mock_result

        tracker = UsageTracker(session)
        summary = await tracker.get_usage_summary()

        assert "daily" in summary
        assert "monthly" in summary
        assert summary["daily"]["total_tokens"] == 8000
        assert summary["daily"]["remaining_tokens"] == 100000 - 8000
        assert summary["monthly"]["total_tokens"] == 8000
