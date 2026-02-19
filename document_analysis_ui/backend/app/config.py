"""Configuration settings for the Document Analysis UI backend."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Session settings
    session_base_dir: str = "/tmp/document_analysis_ui"
    session_expiry_hours: int = 24
    max_upload_size_mb: int = 50

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Master orchestrator settings (relative to project root)
    master_orchestrator_path: str = "../master_orchestrator_agent"
    financial_threshold: float = 15000.0
    
    # API timeout settings
    api_timeout_seconds: int = 600  # Timeout for agent API calls
    api_retry_attempts: int = 3  # Number of retry attempts
    api_retry_delay_seconds: int = 2  # Delay between retries

    # Celery settings
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_prefix = "DAU_"
        env_file = ".env"
        extra = "ignore"

    @property
    def session_base_path(self) -> Path:
        """Get the base path for sessions."""
        return Path(self.session_base_dir)


settings = Settings()
