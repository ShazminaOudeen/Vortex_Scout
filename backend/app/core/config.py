from functools import lru_cache
from typing import Any, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Scout API"
    cors_origins: str = "http://localhost:3000,*"

    @property
    def cors_origins_list(self) -> list[str]:
        val = (self.cors_origins or "").strip()
        if not val or val == "*":
            return ["*"]
        if val.startswith("[") and val.endswith("]"):
            import json
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        return [x.strip() for x in val.split(",") if x.strip()]

    # Supabase (leave blank to run on the in-memory demo store)
    supabase_url: str = ""
    supabase_key: str = ""

    # Gemini. NOTE: gemini-1.5-flash has been retired by Google; keep the
    # model name in env so it can be swapped without a code change.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # Ingestion
    default_store_id: str = "store_01"
    ingest_chunk_size: int = 500  # rows per Supabase insert

    # Alert trigger: flag when P(void) >= threshold AND ledger stock > 0
    void_threshold: float = 0.75


@lru_cache
def get_settings() -> Settings:
    return Settings()
