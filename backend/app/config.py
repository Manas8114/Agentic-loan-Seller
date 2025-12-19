"""
Application Configuration using Pydantic Settings

Loads configuration from environment variables with sensible defaults.
Supports .env files for local development.
"""

import json
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Agentic Loan Sales System"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = Field(default="change-me-in-production")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/loan_sales_db"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # LLM Configuration
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    openrouter_api_key: str = Field(default="")
    llm_provider: str = Field(default="openrouter")  # anthropic | openai | openrouter
    llm_model: str = Field(default="mistralai/devstral-2512:free")
    
    # JWT Configuration
    jwt_secret_key: str = Field(default="jwt-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # File Storage (S3-compatible)
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: str = Field(default="minioadmin")
    s3_bucket: str = Field(default="loan-documents")
    
    # Underwriting Configuration
    credit_score_threshold: int = 700
    max_emi_to_salary_ratio: float = 0.5
    default_interest_rate: float = 12.5  # Annual percentage
    
    # CORS - parse as JSON string or comma-separated list
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or comma-separated list."""
        if isinstance(v, str):
            # Try JSON parsing first (for ["...", "..."] format)
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    
    Returns:
        Settings: Application settings singleton.
    """
    return Settings()


# Global settings instance
settings = get_settings()
