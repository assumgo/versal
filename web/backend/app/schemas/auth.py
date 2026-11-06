from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=80)
    password: SecretStr = Field(min_length=1, max_length=1024)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    login: str | None = None
    role: str
    is_active: bool
