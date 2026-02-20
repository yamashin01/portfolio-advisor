"""Pipeline coordinator - orchestrates all data fetchers."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.services.data_pipeline.exchange_rate import ExchangeRateFetcher
from src.app.services.data_pipeline.fred import FredFetcher
from src.app.services.data_pipeline.jquants import JQuantsFetcher
from src.app.services.data_pipeline.yfinance_fetcher import YFinanceFetcher

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Coordinates all data fetchers for market data updates."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.us_fetcher = YFinanceFetcher(session)
        self.jp_fetcher = JQuantsFetcher(session)
        self.fred_fetcher = FredFetcher(session)
        self.fx_fetcher = ExchangeRateFetcher(session)

    async def update_all(self) -> None:
        """Update all market data: US prices, JP prices, economic indicators, exchange rates."""
        logger.info("Starting full market data update...")

        logger.info("Updating US market prices...")
        await self.us_fetcher.fetch()

        logger.info("Updating JP market prices...")
        await self.jp_fetcher.fetch()

        logger.info("Updating economic indicators (FRED)...")
        await self.fred_fetcher.fetch()

        logger.info("Updating exchange rates...")
        await self.fx_fetcher.fetch()

        logger.info("Full market data update completed.")

    async def update_us_prices(self) -> None:
        """Update US market prices only."""
        logger.info("Updating US market prices...")
        await self.us_fetcher.fetch()

    async def update_jp_prices(self) -> None:
        """Update JP market prices only."""
        logger.info("Updating JP market prices...")
        await self.jp_fetcher.fetch()

    async def update_indicators(self) -> None:
        """Update economic indicators and exchange rates."""
        logger.info("Updating economic indicators...")
        await self.fred_fetcher.fetch()
        await self.fx_fetcher.fetch()
