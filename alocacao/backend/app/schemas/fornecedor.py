from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.documents import normalize_cpf_cnpj


class FornecedorBase(BaseModel):
    razao_social: str = Field(min_length=1, max_length=180)
    nome_fantasia: str = Field(min_length=1, max_length=180)
    documento: str = Field(min_length=11, max_length=18, description='CNPJ ou CPF')
    ativo: bool = True

    @field_validator('razao_social', 'nome_fantasia')
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Campo obrigatório')
        return cleaned

    @field_validator('documento')
    @classmethod
    def validate_documento(cls, value: str) -> str:
        return normalize_cpf_cnpj(value)


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorUpdate(BaseModel):
    razao_social: str | None = Field(default=None, min_length=1, max_length=180)
    nome_fantasia: str | None = Field(default=None, min_length=1, max_length=180)
    documento: str | None = Field(default=None, min_length=11, max_length=18)
    ativo: bool | None = None

    @field_validator('razao_social', 'nome_fantasia')
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('Campo obrigatório')
        return cleaned

    @field_validator('documento')
    @classmethod
    def validate_documento(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_cpf_cnpj(value)


class FornecedorOut(FornecedorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
