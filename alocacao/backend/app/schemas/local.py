from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LocalCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(default='', max_length=2000)

    @field_validator('nome')
    @classmethod
    def strip_nome(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Nome é obrigatório')
        return cleaned

    @field_validator('descricao')
    @classmethod
    def strip_descricao(cls, value: str) -> str:
        return (value or '').strip()


class LocalUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)

    @field_validator('nome')
    @classmethod
    def strip_nome(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Nome é obrigatório')
        return cleaned

    @field_validator('descricao')
    @classmethod
    def strip_descricao(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class LocalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str
    descricao: str
    created_at: datetime
    updated_at: datetime
