"""Market endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.models.economic_indicator import EconomicIndicator
from src.app.schemas.market import (
    BondData,
    EconomicIndicatorResponse,
    ForexData,
    IndexData,
    MarketSummaryResponse,
)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/summary", response_model=MarketSummaryResponse)
async def get_market_summary(db: AsyncSession = Depends(get_db)):
    """Get market summary with latest indices, bonds, and forex data."""
    # Get latest economic indicators
    indicators = {}
    for indicator_type in ["us_treasury_10y", "jp_govt_bond_10y", "usd_jpy", "eur_jpy"]:
        result = await db.execute(
            select(EconomicIndicator)
            .where(EconomicIndicator.indicator_type == indicator_type)
            .order_by(EconomicIndicator.date.desc())
            .limit(1)
        )
        ind = result.scalar_one_or_none()
        if ind:
            indicators[indicator_type] = ind

    bonds = {}
    if "us_treasury_10y" in indicators:
        ind = indicators["us_treasury_10y"]
        bonds["us_treasury_10y"] = BondData(value=float(ind.value), as_of=ind.date)
    if "jp_govt_bond_10y" in indicators:
        ind = indicators["jp_govt_bond_10y"]
        bonds["jp_govt_bond_10y"] = BondData(value=float(ind.value), as_of=ind.date)

    forex = {}
    if "usd_jpy" in indicators:
        ind = indicators["usd_jpy"]
        forex["usd_jpy"] = ForexData(value=float(ind.value), as_of=ind.date)
    if "eur_jpy" in indicators:
        ind = indicators["eur_jpy"]
        forex["eur_jpy"] = ForexData(value=float(ind.value), as_of=ind.date)

    return MarketSummaryResponse(
        updated_at=datetime.now(timezone.utc),
        indices={},  # TODO: indices can be derived from asset prices (SPY, 1321.T)
        bonds=bonds,
        forex=forex,
    )


@router.get("/indicators", response_model=list[EconomicIndicatorResponse])
async def get_indicators(db: AsyncSession = Depends(get_db)):
    """Get latest economic indicators."""
    # Get latest value for each indicator type
    results = []
    for indicator_type in ["us_treasury_10y", "jp_govt_bond_10y", "usd_jpy", "eur_jpy"]:
        result = await db.execute(
            select(EconomicIndicator)
            .where(EconomicIndicator.indicator_type == indicator_type)
            .order_by(EconomicIndicator.date.desc())
            .limit(1)
        )
        ind = result.scalar_one_or_none()
        if ind:
            results.append(
                EconomicIndicatorResponse(
                    indicator_type=ind.indicator_type,
                    indicator_name=ind.indicator_name,
                    value=float(ind.value),
                    currency=ind.currency,
                    date=ind.date,
                    source=ind.source,
                )
            )

    return results
