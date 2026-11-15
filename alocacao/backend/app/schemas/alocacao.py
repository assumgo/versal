from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlocacaoCreate(BaseModel):
    colaborador_id: int
    equipamento_ids: list[int] = Field(min_length=1)


class AlocacaoDevolver(BaseModel):
    alocacao_ids: list[int] = Field(min_length=1)


class AlocacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipamento_id: int
    equipamento_codigo: str
    produto_codigo: str
    produto_descricao: str
    numero_patrimonio: str
    colaborador_id: int | None
    colaborador_nome: str
    ativa: bool
    tre_entrega_id: int | None
    tre_devolucao_id: int | None
    created_at: datetime
    updated_at: datetime


class AlocacaoCreateResult(BaseModel):
    alocacoes: list[AlocacaoOut]
    tre_id: int
    tre_codigo: str
    tre_tipo: str
