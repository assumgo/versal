from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

from app.models.user import User
from app.schemas.auth import UserResponse

RoleName = Literal['Administrador', 'Contador', 'Operador', 'Consulta']


def _clean_name(value: object) -> object:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    return stripped or None


def _clean_login(value: object) -> object:
    if not isinstance(value, str):
        return value
    if any(character.isspace() for character in value):
        raise ValueError('Login não pode conter espaços')
    return value


class UserCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    email: str = Field(min_length=3, max_length=254, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: SecretStr = Field(min_length=12, max_length=1024)
    role: RoleName
    is_active: bool = True
    name: str | None = Field(default=None, max_length=120)
    login: str | None = Field(default=None, min_length=3, max_length=80)

    @field_validator('name', mode='before')
    @classmethod
    def normalize_name(cls, value: object) -> object:
        return _clean_name(value)

    @field_validator('login', mode='before')
    @classmethod
    def normalize_login(cls, value: object) -> object:
        return _clean_login(value)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    email: str | None = Field(default=None, min_length=3, max_length=254,
                              pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: SecretStr | None = Field(default=None, min_length=12, max_length=1024)
    role: RoleName | None = None
    is_active: bool | None = None
    name: str | None = Field(default=None, max_length=120)
    login: str | None = Field(default=None, min_length=3, max_length=80)

    @field_validator('name', mode='before')
    @classmethod
    def normalize_name(cls, value: object) -> object:
        return _clean_name(value)

    @field_validator('login', mode='before')
    @classmethod
    def normalize_login(cls, value: object) -> object:
        return _clean_login(value)

    @model_validator(mode='after')
    def validate_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError('Informe alterações não nulas')
        for field in self.model_fields_set:
            if field == 'name':
                continue
            if getattr(self, field) is None:
                raise ValueError('Informe alterações não nulas')
        return self


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name, login=user.login,
                        role=user.role.name, is_active=user.is_active)
