"""Fetch Japanese market data from J-Quants API or yfinance fallback."""

import asyncio
from datetime import timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.asset import Asset
from src.app.models.asset_price import AssetPrice
from src.app.services.data_pipeline.base import BaseFetcher


class JQuantsFetcher(BaseFetcher):
    """Fetch Japanese market data.

    Uses yfinance as primary source for JP market symbols (e.g., 1306.T).
    J-Quants API can be added later for more comprehensive data.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def fetch(self, symbols: list[str] | None = None, period: str = "5y") -> None:
        """Fetch prices for all JP assets or specified symbols."""
        if symbols is None:
            result = await self.session.execute(
                select(Asset).where(Asset.market == "jp", Asset.is_active.is_(True))
            )
            assets = result.scalars().all()
            symbols = [a.symbol for a in assets]

        for symbol in symbols:
            try:
                await self._retry(self._fetch_single, symbol, period)
                self.logger.info(f"Fetched prices for {symbol}")
            except Exception as e:
                self.logger.error(f"Failed to fetch {symbol}: {e}")

    async def _fetch_single(self, symbol: str, period: str) -> None:
        """Fetch a single JP symbol's price data via yfinance and upsert."""
        result = await self.session.execute(select(Asset).where(Asset.symbol == symbol))
        asset = result.scalar_one_or_none()
        if asset is None:
            self.logger.warning(f"Asset {symbol} not found in DB, skipping.")
            return

        # Get last date for incremental fetch
        last_date_result = await self.session.execute(
            select(AssetPrice.date)
            .where(AssetPrice.asset_id == asset.id)
            .order_by(AssetPrice.date.desc())
            .limit(1)
        )
        last_date = last_date_result.scalar_one_or_none()

        loop = asyncio.get_event_loop()
        if last_date:
            start = last_date + timedelta(days=1)
            df = await loop.run_in_executor(
                None, lambda: yf.download(symbol, start=start.isoformat(), progress=False)
            )
        else:
            df = await loop.run_in_executor(
                None, lambda: yf.download(symbol, period=period, progress=False)
            )

        if df.empty:
            self.logger.info(f"No new data for {symbol}")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        await self._upsert_prices(asset.id, df)

    async def _upsert_prices(self, asset_id: int, df: pd.DataFrame) -> None:
        """Upsert price data into asset_prices table."""
        records = []
        for idx, row in df.iterrows():
            record = {
                "asset_id": asset_id,
                "date": idx.date() if hasattr(idx, "date") else idx,
                "open": float(row.get("Open", 0)) if pd.notna(row.get("Open")) else None,
                "high": float(row.get("High", 0)) if pd.notna(row.get("High")) else None,
                "low": float(row.get("Low", 0)) if pd.notna(row.get("Low")) else None,
                "close": float(row["Close"]),
                "adj_close": float(row.get("Adj Close", row["Close"])) if pd.notna(row.get("Adj Close", None)) else None,
                "volume": int(row.get("Volume", 0)) if pd.notna(row.get("Volume")) else None,
            }
            records.append(record)

        if not records:
            return

        stmt = insert(AssetPrice).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_asset_prices_asset_date",
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "adj_close": stmt.excluded.adj_close,
                "volume": stmt.excluded.volume,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()
