"""Fetch exchange rate data using yfinance."""

import asyncio
from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.economic_indicator import EconomicIndicator
from src.app.services.data_pipeline.base import BaseFetcher

EXCHANGE_PAIRS = {
    "USDJPY=X": {
        "indicator_type": "usd_jpy",
        "indicator_name": "USD/JPY Exchange Rate",
        "currency": "JPY",
        "source": "yfinance",
    },
    "EURJPY=X": {
        "indicator_type": "eur_jpy",
        "indicator_name": "EUR/JPY Exchange Rate",
        "currency": "JPY",
        "source": "yfinance",
    },
}


class ExchangeRateFetcher(BaseFetcher):
    """Fetch exchange rate data using yfinance as source."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def fetch(self, period_years: int = 5) -> None:
        """Fetch all configured exchange rate pairs."""
        for pair, config in EXCHANGE_PAIRS.items():
            try:
                await self._retry(self._fetch_pair, pair, config, period_years)
                self.logger.info(f"Fetched exchange rate: {pair}")
            except Exception as e:
                self.logger.error(f"Failed to fetch {pair}: {e}")

    async def _fetch_pair(self, pair: str, config: dict, period_years: int) -> None:
        """Fetch a single exchange rate pair and upsert to DB."""
        # Get last date for incremental fetch
        last_date_result = await self.session.execute(
            select(EconomicIndicator.date)
            .where(EconomicIndicator.indicator_type == config["indicator_type"])
            .order_by(EconomicIndicator.date.desc())
            .limit(1)
        )
        last_date = last_date_result.scalar_one_or_none()

        loop = asyncio.get_event_loop()
        if last_date:
            start = last_date + timedelta(days=1)
            df = await loop.run_in_executor(
                None, lambda: yf.download(pair, start=start.isoformat(), progress=False)
            )
        else:
            df = await loop.run_in_executor(
                None, lambda: yf.download(pair, period=f"{period_years}y", progress=False)
            )

        if df.empty:
            self.logger.info(f"No new data for {pair}")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        records = []
        for idx, row in df.iterrows():
            close_val = row.get("Close")
            if close_val is not None and pd.notna(close_val):
                records.append({
                    "indicator_type": config["indicator_type"],
                    "indicator_name": config["indicator_name"],
                    "value": float(close_val),
                    "currency": config["currency"],
                    "date": idx.date() if hasattr(idx, "date") else idx,
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
                "currency": stmt.excluded.currency,
                "source": stmt.excluded.source,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()
        self.logger.info(f"Upserted {len(records)} records for {pair}")
