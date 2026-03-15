"""Configuration management for AI Debate platform."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM default settings
    default_temperature: float = 0.7
    default_max_tokens: int = 1000

    # Debate settings
    max_debate_rounds: int = 100  # 立论、驳论、自由辩论、总结
    debate_timeout: int = 60  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
