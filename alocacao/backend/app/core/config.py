from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / 'data' / 'alocacao.db'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Alocação de Recursos'
    api_prefix: str = '/api'
    cors_origins: str = 'http://localhost:5174'
    database_url: str = f'sqlite:///{DEFAULT_DB}'
    azure_tenant_id: str = ''
    azure_client_id: str = ''
    azure_audience: str = ''

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
