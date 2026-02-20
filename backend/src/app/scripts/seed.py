"""Seed database with initial asset data."""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.app.core.database import async_session
from src.app.models.asset import Asset

logger = logging.getLogger(__name__)

SEED_ASSETS = [
    # 日本市場 ETF
    {"symbol": "1306.T", "name": "TOPIX ETF", "name_ja": "TOPIX連動型上場投資信託", "asset_type": "etf", "market": "jp", "currency": "JPY"},
    {"symbol": "1321.T", "name": "Nikkei 225 ETF", "name_ja": "日経225連動型上場投資信託", "asset_type": "etf", "market": "jp", "currency": "JPY"},
    {"symbol": "2558.T", "name": "MAXIS S&P 500 ETF", "name_ja": "MAXIS米国株式(S&P500)上場投信", "asset_type": "etf", "market": "jp", "currency": "JPY"},
    {"symbol": "2631.T", "name": "MAXIS NASDAQ 100 ETF", "name_ja": "MAXISナスダック100上場投信", "asset_type": "etf", "market": "jp", "currency": "JPY"},
    {"symbol": "2559.T", "name": "MAXIS All Country ETF", "name_ja": "MAXIS全世界株式(オール・カントリー)上場投信", "asset_type": "etf", "market": "jp", "currency": "JPY"},
    {"symbol": "1326.T", "name": "SPDR Gold Shares (JP)", "name_ja": "SPDRゴールド・シェア", "asset_type": "etf", "market": "jp", "currency": "JPY"},
    # 日本市場 REIT
    {"symbol": "1343.T", "name": "NEXT FUNDS J-REIT ETF", "name_ja": "NEXT FUNDS 東証REIT指数連動型上場投信", "asset_type": "reit", "market": "jp", "currency": "JPY"},
    {"symbol": "1476.T", "name": "iShares Core J-REIT ETF", "name_ja": "iシェアーズ・コアJリート", "asset_type": "reit", "market": "jp", "currency": "JPY"},
    # 日本市場 債券
    {"symbol": "2511.T", "name": "NEXT FUNDS Foreign Bond ETF", "name_ja": "NEXT FUNDS 外国債券・FTSE世界国債インデックス", "asset_type": "bond", "market": "jp", "currency": "JPY"},
    {"symbol": "2620.T", "name": "iShares USD Treasury 20+ yr ETF (Hedged)", "name_ja": "iシェアーズ 米国債20年超 ETF(為替ヘッジあり)", "asset_type": "bond", "market": "jp", "currency": "JPY"},
    # 米国市場 ETF
    {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "name_ja": "バンガード・トータル・ストック・マーケットETF", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "VEA", "name": "Vanguard FTSE Developed Markets ETF", "name_ja": "バンガード・FTSE先進国市場(除く米国)ETF", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "name_ja": "バンガード・FTSE・エマージング・マーケッツETF", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "VXUS", "name": "Vanguard Total International Stock ETF", "name_ja": "バンガード・トータル・インターナショナル・ストックETF", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "VT", "name": "Vanguard Total World Stock ETF", "name_ja": "バンガード・トータル・ワールド・ストックETF", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "name_ja": "SPDR S&P 500 ETF トラスト", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "name_ja": "インベスコQQQトラスト", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "GLD", "name": "SPDR Gold Shares", "name_ja": "SPDRゴールド・シェア", "asset_type": "etf", "market": "us", "currency": "USD"},
    {"symbol": "SCHD", "name": "Schwab U.S. Dividend Equity ETF", "name_ja": "シュワブ 米国配当株式ETF", "asset_type": "etf", "market": "us", "currency": "USD"},
    # 米国市場 債券
    {"symbol": "BND", "name": "Vanguard Total Bond Market ETF", "name_ja": "バンガード・米国トータル債券市場ETF", "asset_type": "bond", "market": "us", "currency": "USD"},
    {"symbol": "AGG", "name": "iShares Core U.S. Aggregate Bond ETF", "name_ja": "iシェアーズ・コア米国総合債券市場ETF", "asset_type": "bond", "market": "us", "currency": "USD"},
    {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "name_ja": "iシェアーズ 米国国債 20年超 ETF", "asset_type": "bond", "market": "us", "currency": "USD"},
    {"symbol": "IEF", "name": "iShares 7-10 Year Treasury Bond ETF", "name_ja": "iシェアーズ 米国国債 7-10年 ETF", "asset_type": "bond", "market": "us", "currency": "USD"},
    {"symbol": "SHY", "name": "iShares 1-3 Year Treasury Bond ETF", "name_ja": "iシェアーズ 米国国債 1-3年 ETF", "asset_type": "bond", "market": "us", "currency": "USD"},
    # 米国市場 REIT
    {"symbol": "VNQ", "name": "Vanguard Real Estate ETF", "name_ja": "バンガード・リアルエステートETF", "asset_type": "reit", "market": "us", "currency": "USD"},
]


async def seed_assets() -> None:
    async with async_session() as session:
        # Check existing count
        result = await session.execute(select(Asset.id).limit(1))
        if result.scalar_one_or_none() is not None:
            logger.info("Assets already seeded, skipping.")
            return

        stmt = insert(Asset).values(SEED_ASSETS)
        stmt = stmt.on_conflict_do_nothing(index_elements=["symbol"])
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Seeded {len(SEED_ASSETS)} assets.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await seed_assets()


if __name__ == "__main__":
    asyncio.run(main())
