"""Configuration settings for Atelier Agent."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Atelier Agent"
    app_version: str = "0.1.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    gcp_project: str = os.getenv("GCP_PROJECT", "atelier-hack")
    gcp_location: str = os.getenv("GCP_LOCATION", "europe-west3")
    firestore_db: str = os.getenv("FIRESTORE_DATABASE", "(default)")
    inbox_bucket: str = os.getenv("INBOX_BUCKET", "atelier-inbox")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
