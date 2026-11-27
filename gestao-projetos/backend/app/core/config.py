from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Gestão de Projetos API'
    environment: str = 'development'
    database_url: str
    jwt_secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 720
    frontend_origins: str = 'http://localhost:5174'
    seed_user_name: str | None = None
    seed_user_email: str | None = None
    seed_user_password: str | None = None

    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False, extra='ignore')

    @field_validator('jwt_secret_key')
    @classmethod
    def validate_secret(cls, value: str) -> str:
        if len(value.strip()) < 32:
            raise ValueError('JWT_SECRET_KEY deve ter pelo menos 32 caracteres não vazios')
        return value

    @field_validator('frontend_origins')
    @classmethod
    def validate_origins(cls, value: str) -> str:
        for origin in filter(None, (item.strip() for item in value.split(','))):
            parsed = urlsplit(origin)
            if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                    or '*' in origin or parsed.username or parsed.password
                    or parsed.path or parsed.query or parsed.fragment):
                raise ValueError('FRONTEND_ORIGINS exige origens HTTP(S) explícitas, sem caminho')
            parsed.port
        return value

    @field_validator('seed_user_email', 'seed_user_name', 'seed_user_password')
    @classmethod
    def blank_is_missing(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
