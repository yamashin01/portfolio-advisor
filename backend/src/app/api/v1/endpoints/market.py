"""Market endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.models.economic_indicator import EconomicIndicator
from src.app.models.asset import Asset
from src.app.models.asset_price import AssetPrice
from src.app.schemas.market import (
    BondData,
    EconomicIndicatorResponse,
    ForexData,
    IndexData,
    MarketSummaryResponse,
)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/summary", response_model=MarketSummaryResponse)
async def get_market_summary(response: Response, db: AsyncSession = Depends(get_db)):
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1h
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

    bonds: list[BondData] = []
    bond_names = {"us_treasury_10y": "米国10年国債利回り", "jp_govt_bond_10y": "日本10年国債利回り"}
    for key in ["us_treasury_10y", "jp_govt_bond_10y"]:
        if key in indicators:
            ind = indicators[key]
            bonds.append(BondData(name=bond_names[key], indicator_type=key, value=float(ind.value), as_of=ind.date))

    forex: list[ForexData] = []
    forex_names = {"usd_jpy": "USD/JPY", "eur_jpy": "EUR/JPY"}
    for key in ["usd_jpy", "eur_jpy"]:
        if key in indicators:
            ind = indicators[key]
            forex.append(ForexData(pair=forex_names[key], rate=float(ind.value), as_of=ind.date))

    # Get index-like assets (SPY, 1321.T) latest prices as indices
    indices: list[IndexData] = []
    index_symbols = {"SPY": "S&P 500 (SPY)", "1321.T": "日経225連動型 (1321)"}
    for symbol, name in index_symbols.items():
        result = await db.execute(
            select(AssetPrice)
            .join(Asset, Asset.id == AssetPrice.asset_id)
            .where(Asset.symbol == symbol)
            .order_by(AssetPrice.date.desc())
            .limit(2)
        )
        prices = result.scalars().all()
        if prices:
            latest = prices[0]
            change_pct = None
            if len(prices) > 1 and prices[1].close and prices[1].close > 0:
                change_pct = (float(latest.close) - float(prices[1].close)) / float(prices[1].close)
            indices.append(IndexData(
                name=name,
                symbol=symbol,
                value=float(latest.close) if latest.close else None,
                change_pct=change_pct,
                as_of=latest.date,
            ))

    return MarketSummaryResponse(
        updated_at=datetime.now(timezone.utc),
        indices=indices,
        bonds=bonds,
        forex=forex,
    )


@router.get("/indicators", response_model=list[EconomicIndicatorResponse])
async def get_indicators(response: Response, db: AsyncSession = Depends(get_db)):
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1h
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
                    as_of=ind.date,
                    source=ind.source,
                )
            )

    return results
