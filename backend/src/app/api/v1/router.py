"""API v1 router aggregation."""

from fastapi import APIRouter

from src.app.api.v1.endpoints import assets, health, market

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(assets.router)
api_router.include_router(market.router)
