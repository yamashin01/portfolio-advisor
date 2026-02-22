"""Asset endpoints."""

import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.crud.asset import get_asset_by_symbol, get_asset_prices, get_assets, get_latest_price, get_previous_price
from src.app.schemas.asset import (
    AssetPriceResponse,
    AssetPricesResponse,
    AssetResponse,
    LatestPrice,
    PaginatedAssetResponse,
)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=PaginatedAssetResponse)
async def list_assets(
    response: Response,
    market: str | None = Query(None, description="Filter by market (jp/us)"),
    asset_type: str | None = Query(None, description="Filter by asset type (etf/bond/reit/stock)"),
    search: str | None = Query(None, description="Search by name or symbol"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1h
    """Get paginated list of assets with optional filters."""
    assets, total = await get_assets(db, market=market, asset_type=asset_type, search=search, page=page, per_page=per_page)

    items = []
    for asset in assets:
        latest = await get_latest_price(db, asset.id)
        latest_price = None
        if latest:
            prev = await get_previous_price(db, asset.id, latest.date)
            change_pct = None
            if prev and prev.close:
                change_pct = float((latest.close - prev.close) / prev.close)
            latest_price = LatestPrice(close=float(latest.close), date=latest.date, change_pct=change_pct)

        items.append(
            AssetResponse(
                symbol=asset.symbol,
                name=asset.name,
                name_ja=asset.name_ja,
                asset_type=asset.asset_type,
                market=asset.market,
                currency=asset.currency,
                sector=asset.sector,
                latest_price=latest_price,
            )
        )

    return PaginatedAssetResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/{symbol}/prices", response_model=AssetPricesResponse)
async def get_prices(
    response: Response,
    symbol: str,
    period: str = Query("1y", description="Period (1m/3m/6m/1y/3y/5y/max)"),
    interval: str = Query("daily", description="Interval (daily/weekly/monthly)"),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1h
    """Get price history for a specific asset."""
    asset = await get_asset_by_symbol(db, symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")

    prices = await get_asset_prices(db, asset.id, period=period, interval=interval)

    return AssetPricesResponse(
        symbol=symbol,
        period=period,
        interval=interval,
        prices=[
            AssetPriceResponse(
                date=p.date,
                open=float(p.open) if p.open else None,
                high=float(p.high) if p.high else None,
                low=float(p.low) if p.low else None,
                close=float(p.close),
                adj_close=float(p.adj_close) if p.adj_close else None,
                volume=p.volume,
            )
            for p in prices
        ],
    )
