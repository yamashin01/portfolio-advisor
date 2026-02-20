import enum
from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.app.models.base import Base


class IndicatorType(str, enum.Enum):
    US_TREASURY_10Y = "us_treasury_10y"
    JP_GOVT_BOND_10Y = "jp_govt_bond_10y"
    USD_JPY = "usd_jpy"
    EUR_JPY = "eur_jpy"


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    indicator_type: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    indicator_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    value: Mapped[Decimal] = mapped_column(sa.Numeric(18, 6), nullable=False)
    currency: Mapped[str | None] = mapped_column(sa.String(3), nullable=True)
    date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    __table_args__ = (
        sa.UniqueConstraint("indicator_type", "date", name="uq_econ_indicators_type_date"),
        sa.CheckConstraint(
            "indicator_type IN ('us_treasury_10y', 'jp_govt_bond_10y', 'usd_jpy', 'eur_jpy')",
            name="ck_economic_indicators_type",
        ),
    )
