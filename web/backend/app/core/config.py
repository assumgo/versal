from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Versal Folha TXT API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://versal:versal@db:5432/versal_folha"
    jwt_secret_key: str = "change-this-development-value"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    frontend_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
