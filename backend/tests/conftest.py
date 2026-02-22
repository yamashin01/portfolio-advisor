"""Test configuration and fixtures."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.main import app


@pytest.fixture
def mock_db():
    """Provide an AsyncMock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
async def client(mock_db):
    """Provide an httpx AsyncClient with DB dependency overridden."""

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
