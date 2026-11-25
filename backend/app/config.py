from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "postgresql+psycopg://leaflet:leaflet@localhost:5432/leaflet"
    redis_url: str = "redis://localhost:6379/0"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 20.0
    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    seed_demo: bool = False
    auto_create_schema: bool = False
    worker_poll_seconds: float = 2.0
    worker_port: int = 8000
    dispatch_lock_seconds: int = 60
    log_level: str = "INFO"


def cors_origin_list(settings: Settings) -> list[str]:
    return [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
