"""API v1 router aggregation."""

from fastapi import APIRouter

from src.app.api.v1.endpoints import assets, chat, health, market, portfolios, risk_assessment, usage

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(assets.router)
api_router.include_router(market.router)
api_router.include_router(risk_assessment.router)
api_router.include_router(portfolios.router)
api_router.include_router(chat.router)
api_router.include_router(usage.router)
