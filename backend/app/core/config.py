from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DealerMind AI"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://dealermind:dealermind@db:5432/dealermind"
    geocoding_url: str = "https://nominatim.openstreetmap.org/search"
    geocoding_user_agent: str = "DealerMind-AI/0.1 (self-hosted logistics calculator)"
    # The CPA sandbox endpoint is suspended. Production CEPiK is public and
    # documented independently at api.cepik.gov.pl/doc.
    cepik_api_url: str = "https://api.cepik.gov.pl/v1/pojazdy"
    cepik_request_timeout_seconds: float = 60.0
    cepik_api_token: str | None = None  # legacy setting; not needed for production CEPiK
    cepik_consumer_key: str | None = None
    cepik_consumer_secret: str | None = None
    cepik_fleet_max_pages_per_region: int = 20
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
