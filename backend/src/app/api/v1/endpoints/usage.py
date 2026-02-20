"""Usage tracking endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.schemas.usage import UsageSummaryResponse
from src.app.services.usage_tracker import UsageTracker

router = APIRouter(tags=["usage"])


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage(db: AsyncSession = Depends(get_db)):
    """Get daily and monthly API usage summary."""
    tracker = UsageTracker(db)
    return await tracker.get_usage_summary()
