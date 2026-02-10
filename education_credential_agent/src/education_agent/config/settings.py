"""Application settings using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field, SecretStr, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="EA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic API Configuration
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("EA_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
        description="Anthropic API key for Claude access",
    )

    # LLM Model Configuration
    llm_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model to use for analysis",
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for LLM responses",
    )
    llm_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Temperature for LLM responses",
    )

    # Bachelor's Degree Settings
    default_bachelor_semesters: int = Field(
        default=8,
        ge=4,
        le=12,
        description="Default number of semesters for Bachelor's degrees",
    )

    # Processing Limits
    max_file_size_mb: int = Field(
        default=50,
        ge=1,
        description="Maximum file size in MB",
    )
    max_pdf_pages: int = Field(
        default=100,
        ge=1,
        description="Maximum number of PDF pages to process",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: str = Field(
        default="json",
        description="Logging format (json or console)",
    )

    # Performance Optimization Settings
    ocr_max_workers: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum concurrent OCR API calls",
    )
    pdf_render_workers: int = Field(
        default=4,
        ge=1,
        le=8,
        description="Maximum concurrent PDF rendering threads",
    )
    enable_llm_cache: bool = Field(
        default=False,
        description="Enable LLM response caching (opt-in)",
    )
    llm_cache_ttl_minutes: int = Field(
        default=60,
        ge=1,
        description="LLM cache TTL in minutes",
    )
    llm_cache_max_size: int = Field(
        default=100,
        ge=10,
        description="Maximum number of cached LLM responses",
    )

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
