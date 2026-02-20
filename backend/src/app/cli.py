"""CLI commands for market data management."""

import asyncio
import logging

import typer

from src.app.core.database import async_session
from src.app.services.data_pipeline.coordinator import PipelineCoordinator

app = typer.Typer(help="Portfolio Advisor CLI")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@app.command()
def update_market_data():
    """Update all market data (US stocks, JP stocks, economic indicators, exchange rates)."""
    asyncio.run(_update_market_data())


async def _update_market_data():
    async with async_session() as session:
        coordinator = PipelineCoordinator(session)
        await coordinator.update_all()


@app.command()
def update_us_prices():
    """Update US stock/ETF prices only."""
    asyncio.run(_update_us_prices())


async def _update_us_prices():
    async with async_session() as session:
        coordinator = PipelineCoordinator(session)
        await coordinator.update_us_prices()


@app.command()
def update_jp_prices():
    """Update JP stock/ETF prices only."""
    asyncio.run(_update_jp_prices())


async def _update_jp_prices():
    async with async_session() as session:
        coordinator = PipelineCoordinator(session)
        await coordinator.update_jp_prices()


@app.command()
def update_indicators():
    """Update economic indicators and exchange rates."""
    asyncio.run(_update_indicators())


async def _update_indicators():
    async with async_session() as session:
        coordinator = PipelineCoordinator(session)
        await coordinator.update_indicators()


@app.command()
def seed():
    """Seed database with initial asset data."""
    from src.app.scripts.seed import main as seed_main
    asyncio.run(seed_main())


if __name__ == "__main__":
    app()
