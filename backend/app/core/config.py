from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DealerMind AI"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://dealermind:dealermind@db:5432/dealermind"
    geocoding_url: str = "https://nominatim.openstreetmap.org/search"
    geocoding_user_agent: str = "DealerMind-AI/0.1 (self-hosted logistics calculator)"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
