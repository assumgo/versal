from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AlocacaoTipo = Literal['entrega', 'devolucao']
DestinoTipo = Literal['colaborador', 'local']


class AlocacaoCreate(BaseModel):
    tipo: AlocacaoTipo
    destino_tipo: DestinoTipo
    equipamento_id: int
    quantidade: int = Field(default=1, ge=1)
    colaborador_id: int | None = None
    local_id: int | None = None
    data_previsao: date | None = None

    @model_validator(mode='after')
    def validate_destino(self) -> 'AlocacaoCreate':
        if self.destino_tipo == 'colaborador':
            if not self.colaborador_id:
                raise ValueError('Informe o colaborador')
            if self.local_id:
                raise ValueError('Não informe local para destino colaborador')
            if self.tipo == 'entrega' and not self.data_previsao:
                raise ValueError('Informe a data de previsão de entrega')
        else:
            if not self.local_id:
                raise ValueError('Informe o local')
            if self.colaborador_id:
                raise ValueError('Não informe colaborador para destino local')
        return self


class AlocacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    tipo: AlocacaoTipo
    destino_tipo: DestinoTipo
    equipamento_id: int
    equipamento_codigo: str
    produto_id: int
    produto_codigo: str
    produto_descricao: str
    numero_patrimonio: str
    quantidade: int
    colaborador_id: int | None
    colaborador_nome: str
    local_id: int | None
    local_nome: str
    destino_nome: str
    tre_id: int | None
    tre_codigo: str
    referencia_id: int | None
    data_previsao: date | None
    ativa: bool
    estoque_disponivel_produto: int
    created_at: datetime
    updated_at: datetime
