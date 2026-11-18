"""
Application configuration.

Loads environment variables required to talk to Supabase. Never hardcode
secrets here — everything comes from the environment (.env in local dev).
"""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


# Project root: neurodetect/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load the shared project-level .env
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")

    def validate(self) -> None:
        """Raise loudly at startup if required secrets are missing."""
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in your Supabase project values."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
