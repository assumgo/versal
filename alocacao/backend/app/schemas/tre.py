from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TreTipo = Literal['entrega', 'devolucao']


class TreItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipamento_id: int | None
    quantidade: int
    categoria_nome: str
    descricao: str
    numero_patrimonio: str


class TreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    tipo: TreTipo
    colaborador_id: int
    colaborador_nome: str
    created_at: datetime
    itens: list[TreItemOut] = []
