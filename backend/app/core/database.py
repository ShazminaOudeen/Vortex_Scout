"""Supabase client. Returns None when credentials aren't configured so the
API can still run locally against the in-memory store (app/core/store.py)."""
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client | None:
    s = get_settings()
    if not (s.supabase_url and s.supabase_key):
        return None
    return create_client(s.supabase_url, s.supabase_key)
