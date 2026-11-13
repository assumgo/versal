from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoriaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = Field(default=None, max_length=500)
    ativo: bool = True


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=80)
    descricao: str | None = Field(default=None, max_length=500)
    ativo: bool | None = None


class CategoriaOut(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
