from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.schemas.auth import normalize_email


class UserCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: SecretStr = Field(min_length=12, max_length=1024)
    is_admin: bool = False

    @field_validator('name')
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('Informe o nome')
        return stripped

    @field_validator('email')
    @classmethod
    def normalize(cls, value: str) -> str:
        return normalize_email(value)
