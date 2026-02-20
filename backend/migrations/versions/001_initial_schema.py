"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # assets
    op.create_table(
        "assets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_ja", sa.String(200), nullable=True),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("market", sa.String(10), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("sector", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="ix_assets_symbol"),
        sa.CheckConstraint("asset_type IN ('stock', 'etf', 'bond', 'reit')", name="ck_assets_asset_type"),
        sa.CheckConstraint("market IN ('jp', 'us')", name="ck_assets_market"),
        sa.CheckConstraint("currency IN ('JPY', 'USD')", name="ck_assets_currency"),
    )
    op.create_index("ix_assets_asset_type", "assets", ["asset_type"])
    op.create_index("ix_assets_market", "assets", ["market"])

    # asset_prices
    op.create_table(
        "asset_prices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=True),
        sa.Column("high", sa.Numeric(18, 6), nullable=True),
        sa.Column("low", sa.Numeric(18, 6), nullable=True),
        sa.Column("close", sa.Numeric(18, 6), nullable=False),
        sa.Column("adj_close", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("asset_id", "date", name="uq_asset_prices_asset_date"),
    )
    op.create_index("ix_asset_prices_date", "asset_prices", ["date"])
    op.create_index("ix_asset_prices_asset_id", "asset_prices", ["asset_id"])

    # economic_indicators
    op.create_table(
        "economic_indicators",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("indicator_type", sa.String(30), nullable=False),
        sa.Column("indicator_name", sa.String(100), nullable=False),
        sa.Column("value", sa.Numeric(18, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("indicator_type", "date", name="uq_econ_indicators_type_date"),
        sa.CheckConstraint(
            "indicator_type IN ('us_treasury_10y', 'jp_govt_bond_10y', 'usd_jpy', 'eur_jpy')",
            name="ck_economic_indicators_type",
        ),
    )
    op.create_index("ix_economic_indicators_date", "economic_indicators", ["date"])

    # api_usage_logs
    op.create_table(
        "api_usage_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("endpoint", sa.String(50), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_usage_logs_created_at", "api_usage_logs", ["created_at"])
    op.create_index("ix_api_usage_logs_endpoint", "api_usage_logs", ["endpoint"])


def downgrade() -> None:
    op.drop_table("api_usage_logs")
    op.drop_table("economic_indicators")
    op.drop_table("asset_prices")
    op.drop_table("assets")
