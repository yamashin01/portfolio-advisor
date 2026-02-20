"""CRUD operations for assets."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.asset import Asset
from src.app.models.asset_price import AssetPrice


async def get_assets(
    session: AsyncSession,
    market: str | None = None,
    asset_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Asset], int]:
    """Get paginated list of assets with optional filters."""
    query = select(Asset).where(Asset.is_active.is_(True))

    if market:
        query = query.where(Asset.market == market)
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Asset.symbol.ilike(search_filter))
            | (Asset.name.ilike(search_filter))
            | (Asset.name_ja.ilike(search_filter))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar_one()

    # Paginate
    query = query.order_by(Asset.symbol).offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(query)
    assets = list(result.scalars().all())

    return assets, total


async def get_asset_by_symbol(session: AsyncSession, symbol: str) -> Asset | None:
    """Get a single asset by symbol."""
    result = await session.execute(select(Asset).where(Asset.symbol == symbol))
    return result.scalar_one_or_none()


async def get_asset_prices(
    session: AsyncSession,
    asset_id: int,
    period: str = "1y",
    interval: str = "daily",
) -> list[AssetPrice]:
    """Get price history for an asset."""
    period_days = {
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "3y": 365 * 3,
        "5y": 365 * 5,
        "max": 365 * 30,
    }
    days = period_days.get(period, 365)
    start_date = date.today() - timedelta(days=days)

    query = (
        select(AssetPrice)
        .where(AssetPrice.asset_id == asset_id, AssetPrice.date >= start_date)
        .order_by(AssetPrice.date)
    )

    # Downsample for weekly/monthly
    if interval == "weekly":
        # Get all and sample every 5th
        result = await session.execute(query)
        prices = list(result.scalars().all())
        return prices[::5] if prices else []
    elif interval == "monthly":
        result = await session.execute(query)
        prices = list(result.scalars().all())
        return prices[::22] if prices else []

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_latest_price(session: AsyncSession, asset_id: int) -> AssetPrice | None:
    """Get the latest price for an asset."""
    result = await session.execute(
        select(AssetPrice)
        .where(AssetPrice.asset_id == asset_id)
        .order_by(AssetPrice.date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_previous_price(session: AsyncSession, asset_id: int, before_date: date) -> AssetPrice | None:
    """Get the price before a given date."""
    result = await session.execute(
        select(AssetPrice)
        .where(AssetPrice.asset_id == asset_id, AssetPrice.date < before_date)
        .order_by(AssetPrice.date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
