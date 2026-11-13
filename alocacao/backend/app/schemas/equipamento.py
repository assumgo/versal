from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

StatusEquipamento = Literal['disponivel', 'alocado']


class EquipamentoBase(BaseModel):
    descricao: str = Field(min_length=1, max_length=200)
    marca: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=100)
    numero_serie: str = Field(min_length=1, max_length=100)
    numero_patrimonio: str = Field(min_length=1, max_length=100)
    mac_address: str | None = Field(default=None, max_length=32)
    categoria_id: int

    @field_validator('descricao', 'marca', 'modelo', 'numero_serie', 'numero_patrimonio')
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Campo obrigatório')
        return cleaned

    @field_validator('mac_address')
    @classmethod
    def normalize_mac(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        return cleaned or None


class EquipamentoCreate(EquipamentoBase):
    pass


class EquipamentoUpdate(BaseModel):
    descricao: str | None = Field(default=None, min_length=1, max_length=200)
    marca: str | None = Field(default=None, min_length=1, max_length=100)
    modelo: str | None = Field(default=None, min_length=1, max_length=100)
    numero_serie: str | None = Field(default=None, min_length=1, max_length=100)
    numero_patrimonio: str | None = Field(default=None, min_length=1, max_length=100)
    mac_address: str | None = Field(default=None, max_length=32)
    categoria_id: int | None = None

    @field_validator('descricao', 'marca', 'modelo', 'numero_serie', 'numero_patrimonio')
    @classmethod
    def strip_required(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Campo obrigatório')
        return cleaned

    @field_validator('mac_address')
    @classmethod
    def normalize_mac(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        return cleaned or None


class EquipamentoOut(EquipamentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusEquipamento
    categoria_nome: str
    created_at: datetime
    updated_at: datetime
