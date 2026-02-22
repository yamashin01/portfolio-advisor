from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Portfolio Advisor API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_advisor"

    @model_validator(mode="after")
    def _normalize_database_url(self) -> "Settings":
        """Railway provides DATABASE_URL as postgresql:// — convert to asyncpg."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            self.DATABASE_URL = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            self.DATABASE_URL = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self

    # External APIs
    ANTHROPIC_API_KEY: str = ""
    JQUANTS_EMAIL: str = ""
    JQUANTS_PASSWORD: str = ""
    FRED_API_KEY: str = ""

    # Claude API Budget
    DAILY_TOKEN_BUDGET: int = 100000
    MONTHLY_TOKEN_BUDGET: int = 2000000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
