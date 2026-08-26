from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Indian Stock Market Research Assistant"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"

    # Database: SQLite in-memory default for V1, Postgres ready
    # For Postgres later: postgresql+asyncpg://postgres:postgres@localhost:5432/stock_ai
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    # LLM Configuration
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # MCP Provider Configuration
    MCP_PROVIDER: str = "tapetide"
    MCP_SERVER_URL: str = "https://mcp.tapetide.com/mcp"
    TAPETIDE_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
