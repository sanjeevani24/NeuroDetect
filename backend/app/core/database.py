"""
Supabase client factory.

The backend is the ONLY thing that ever holds the service-role key.
The frontend talks exclusively to FastAPI, never to Supabase directly.
"""
from functools import lru_cache

from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    settings.validate()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
