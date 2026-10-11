from functools import lru_cache
from typing import Any, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Scout API"
    cors_origins: Union[str, list[str]] = ["http://localhost:3000", "*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            val = v.strip()
            if val == "*":
                return ["*"]
            if val.startswith("[") and val.endswith("]"):
                import json
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return [x.strip() for x in val.split(",") if x.strip()]
        return v

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
