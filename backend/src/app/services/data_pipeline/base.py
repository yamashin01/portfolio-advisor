"""Base class for data fetchers."""

import logging
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Base class for all data fetchers.

    Provides common functionality: logging, retry logic, error handling.
    """

    MAX_RETRIES = 3

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def fetch(self, **kwargs) -> None:
        """Fetch data from external source and save to DB."""

    async def _retry(self, coro_func, *args, **kwargs):
        """Retry with exponential backoff."""
        import asyncio

        for attempt in range(self.MAX_RETRIES):
            try:
                return await coro_func(*args, **kwargs)
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    self.logger.error(f"Failed after {self.MAX_RETRIES} attempts: {e}")
                    raise
                wait = 2**attempt
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
