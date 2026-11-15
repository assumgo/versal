from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProdutoBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=60)
    descricao: str = Field(min_length=1, max_length=200)
    marca: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=100)
    categoria_id: int

    @field_validator('codigo', 'descricao', 'marca', 'modelo')
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Campo obrigatório')
        return cleaned


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=60)
    descricao: str | None = Field(default=None, min_length=1, max_length=200)
    marca: str | None = Field(default=None, min_length=1, max_length=100)
    modelo: str | None = Field(default=None, min_length=1, max_length=100)
    categoria_id: int | None = None

    @field_validator('codigo', 'descricao', 'marca', 'modelo')
    @classmethod
    def strip_required(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Campo obrigatório')
        return cleaned


class ProdutoOut(ProdutoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria_nome: str
    created_at: datetime
    updated_at: datetime
