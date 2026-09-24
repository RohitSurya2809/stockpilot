"""
StockPilot Configuration Module

Loads and validates environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://postgres:root@localhost:5432/stockpilot",
        description="PostgreSQL database connection URL"
    )

    # n8n Webhooks
    n8n_po_webhook_url: str = Field(
        default="",
        description="n8n webhook URL for purchase order notifications"
    )
    n8n_alert_webhook_url: str = Field(
        default="",
        description="n8n webhook URL for critical alerts"
    )
    n8n_inventory_webhook_url: str = Field(
        default="",
        description="n8n webhook URL for inventory updates"
    )

    # Google Sheets
    google_sheet_id: str = Field(
        default="",
        description="Google Sheet ID for data export"
    )
    google_credentials_path: str = Field(
        default="./credentials/google-service-account.json",
        description="Path to Google service account credentials"
    )

    # LLM Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="qwen2.5:8b",
        description="Ollama model to use"
    )
    ollama_think: bool = Field(
        default=False,
        description="Enable Ollama thinking mode (increases latency)"
    )
    ollama_keep_alive: int = Field(
        default=-1,
        description="Keep model loaded in memory (-1 = indefinitely, 0 = unload immediately, N seconds)"
    )
    gemini_api_key: str = Field(
        default="",
        description="Gemini API key for fallback"
    )
    llm_provider: str = Field(
        default="ollama",
        description="Primary LLM provider (ollama or gemini)"
    )

    # StockPilot API
    stockpilot_api_url: str = Field(
        default="http://localhost:8000",
        description="StockPilot API URL for n8n callbacks"
    )

    # Application Settings
    environment: str = Field(
        default="development",
        description="Environment (development, production)"
    )
    debug: bool = Field(
        default=True,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Analytics Settings
    service_level: float = Field(
        default=0.95,
        description="Target service level for safety stock calculation"
    )
    forecast_horizon_days: int = Field(
        default=30,
        description="Forecast horizon in days"
    )
    moving_average_window: int = Field(
        default=14,
        description="Moving average window in days"
    )

    # Optional API Security
    api_key: Optional[str] = Field(
        default=None,
        description="Optional API key for endpoint security"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Helper functions
def get_database_url() -> str:
    """Get database URL as string."""
    return str(settings.database_url)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return settings.debug


def get_llm_provider() -> str:
    """Get configured LLM provider."""
    return settings.llm_provider.lower()


# Validate critical settings on import
def validate_settings():
    """Validate critical settings."""
    if not settings.database_url:
        raise ValueError("DATABASE_URL must be set")

    print(f"✓ Configuration loaded successfully")
    print(f"  Environment: {settings.environment}")
    print(f"  Debug: {settings.debug}")
    print(f"  Database: {str(settings.database_url).split('@')[1] if '@' in str(settings.database_url) else 'localhost'}")
    print(f"  LLM Provider: {settings.llm_provider}")


if __name__ == "__main__":
    validate_settings()
