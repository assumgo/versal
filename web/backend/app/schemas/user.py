from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from app.models.user import User
from app.schemas.auth import UserResponse

RoleName = Literal['Administrador', 'Contador', 'Operador', 'Consulta']


class UserCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    email: str = Field(min_length=3, max_length=254, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: SecretStr = Field(min_length=12, max_length=1024)
    role: RoleName
    is_active: bool = True


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    email: str | None = Field(default=None, min_length=3, max_length=254,
                              pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: SecretStr | None = Field(default=None, min_length=12, max_length=1024)
    role: RoleName | None = None
    is_active: bool | None = None

    @model_validator(mode='after')
    def validate_changes(self) -> Self:
        if not self.model_fields_set or any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError('Informe alterações não nulas')
        return self


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, role=user.role.name, is_active=user.is_active)
