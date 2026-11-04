from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


def normalize_email(value: str) -> str:
    return value.strip().lower()


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=1024)

    @field_validator('email')
    @classmethod
    def normalize(cls, value: str) -> str:
        return normalize_email(value)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
    must_change_password: bool


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra='forbid')

    current_password: SecretStr = Field(min_length=1, max_length=1024)
    new_password: SecretStr = Field(min_length=8, max_length=1024)
