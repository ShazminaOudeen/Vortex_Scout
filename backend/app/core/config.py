from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Scout API"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Supabase (leave blank to run on the in-memory demo store)
    supabase_url: str = ""
    supabase_key: str = ""

    # Gemini. NOTE: gemini-1.5-flash has been retired by Google; keep the
    # model name in env so it can be swapped without a code change.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Alert trigger: flag when P(void) >= threshold AND ledger stock > 0
    void_threshold: float = 0.75


@lru_cache
def get_settings() -> Settings:
    return Settings()
