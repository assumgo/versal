from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.documents import normalize_cpf, normalize_phone


class ColaboradorBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email_pessoal: EmailStr
    cpf: str = Field(min_length=11, max_length=14)
    data_nascimento: date
    celular: str = Field(min_length=10, max_length=20)
    ativo: bool = True

    @field_validator('nome')
    @classmethod
    def strip_nome(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Nome é obrigatório')
        return cleaned

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        return normalize_cpf(value)

    @field_validator('celular')
    @classmethod
    def validate_celular(cls, value: str) -> str:
        return normalize_phone(value)


class ColaboradorCreate(ColaboradorBase):
    pass


class ColaboradorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    email_pessoal: EmailStr | None = None
    cpf: str | None = Field(default=None, min_length=11, max_length=14)
    data_nascimento: date | None = None
    celular: str | None = Field(default=None, min_length=10, max_length=20)
    ativo: bool | None = None

    @field_validator('nome')
    @classmethod
    def strip_nome(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Nome é obrigatório')
        return cleaned

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_cpf(value)

    @field_validator('celular')
    @classmethod
    def validate_celular(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_phone(value)


class ColaboradorOut(ColaboradorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
