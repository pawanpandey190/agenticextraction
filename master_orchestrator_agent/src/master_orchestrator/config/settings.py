"""Settings configuration for Master Orchestrator Agent."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from master_orchestrator.config.constants import ClassificationStrategy, OutputFormat


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables with MO_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="MO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    openai_api_key: str | None = None
    model_name: str = "gpt-4o"

    # Classification settings
    classification_strategy: ClassificationStrategy = ClassificationStrategy.HYBRID
    name_match_threshold: float = 0.85

    # Financial settings
    financial_threshold_eur: float = 15000.0

    # Output settings
    output_format: OutputFormat = OutputFormat.BOTH
    log_level: str = "INFO"

    # File limits
    max_file_size_bytes: int = 52428800  # 50MB

    # Performance Optimization Settings
    # Note: Parallel dispatch improves processing speed by running agents concurrently.
    # However, some PDFs may cause crashes (SIGABRT) when processed in parallel due to
    # thread-safety issues in underlying libraries (pypdfium2, OpenCV). If you encounter
    # crashes, set MO_ENABLE_PARALLEL_DISPATCH=false to use sequential processing.
    enable_parallel_dispatch: bool = False
    parallel_dispatch_timeout_seconds: int = 300
    ocr_max_workers: int = 4
    pdf_render_workers: int = 4

    # Sub-agent API keys (optional - defaults to main key if not set)
    fa_openai_api_key: str | None = None
    ea_openai_api_key: str | None = None
    pa_openai_api_key: str | None = None

    def get_financial_api_key(self) -> str:
        """Get API key for financial agent."""
        return self.fa_openai_api_key or self.openai_api_key

    def get_education_api_key(self) -> str:
        """Get API key for education agent."""
        return self.ea_openai_api_key or self.openai_api_key

    def get_passport_api_key(self) -> str:
        """Get API key for passport agent."""
        return self.pa_openai_api_key or self.openai_api_key
