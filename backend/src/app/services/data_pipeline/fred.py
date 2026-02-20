"""Fetch economic indicators from FRED API."""

import asyncio
from datetime import date, timedelta

from fredapi import Fred
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.models.economic_indicator import EconomicIndicator
from src.app.services.data_pipeline.base import BaseFetcher

# FRED series mapping
FRED_SERIES = {
    "DGS10": {
        "indicator_type": "us_treasury_10y",
        "indicator_name": "US 10-Year Treasury Yield",
        "source": "FRED",
    },
}


class FredFetcher(BaseFetcher):
    """Fetch economic indicators from FRED (Federal Reserve Economic Data).

    Currently fetches:
    - DGS10: US 10-Year Treasury Constant Maturity Rate
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.fred = Fred(api_key=settings.FRED_API_KEY) if settings.FRED_API_KEY else None

    async def fetch(self, period_years: int = 5) -> None:
        """Fetch all configured FRED series."""
        if not self.fred:
            self.logger.warning("FRED_API_KEY not set, skipping FRED data fetch.")
            return

        for series_id, config in FRED_SERIES.items():
            try:
                await self._retry(self._fetch_series, series_id, config, period_years)
                self.logger.info(f"Fetched FRED series: {series_id}")
            except Exception as e:
                self.logger.error(f"Failed to fetch FRED {series_id}: {e}")

    async def _fetch_series(self, series_id: str, config: dict, period_years: int) -> None:
        """Fetch a single FRED series and upsert to DB."""
        # Get last date for incremental fetch
        last_date_result = await self.session.execute(
            select(EconomicIndicator.date)
            .where(EconomicIndicator.indicator_type == config["indicator_type"])
            .order_by(EconomicIndicator.date.desc())
            .limit(1)
        )
        last_date = last_date_result.scalar_one_or_none()

        loop = asyncio.get_event_loop()
        start_date = last_date + timedelta(days=1) if last_date else date.today() - timedelta(days=period_years * 365)

        series = await loop.run_in_executor(
            None,
            lambda: self.fred.get_series(series_id, observation_start=start_date.isoformat()),
        )

        if series.empty:
            self.logger.info(f"No new data for {series_id}")
            return

        records = []
        for dt, value in series.items():
            if value is not None and str(value) != "." and not (hasattr(value, "__float__") and value != value):
                records.append({
                    "indicator_type": config["indicator_type"],
                    "indicator_name": config["indicator_name"],
                    "value": float(value),
                    "date": dt.date() if hasattr(dt, "date") else dt,
                    "source": config["source"],
                })

        if not records:
            return

        stmt = insert(EconomicIndicator).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_econ_indicators_type_date",
            set_={
                "value": stmt.excluded.value,
                "indicator_name": stmt.excluded.indicator_name,
                "source": stmt.excluded.source,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()
        self.logger.info(f"Upserted {len(records)} records for {series_id}")
