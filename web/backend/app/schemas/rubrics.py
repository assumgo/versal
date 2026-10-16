from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict

from app.schemas.accounting import Flag, InputModel, NonEmpty, PatchModel, normalize_account, normalize_history

Account = Annotated[str, AfterValidator(normalize_account)]
HistoryCode = Annotated[str, AfterValidator(normalize_history)]
History = Annotated[str, AfterValidator(lambda value: value.strip()[:200])]
RubricType = Literal['P', 'D', 'E']
RubricStatus = Literal['Ativa', 'Inativa']


class RubricCreate(InputModel):
    codigo: NonEmpty
    descricao: NonEmpty
    tipo: RubricType = 'P'
    conta_debito: Account | None = None
    conta_credito: Account | None = None
    historico_id: HistoryCode = '001000182'
    historico: History | None = None
    status: RubricStatus = 'Ativa'
    debito_gera_cc: Flag = 1
    debito_gera_cor: Flag = 1
    credito_gera_cc: Flag = 1
    credito_gera_cor: Flag = 1


class RubricUpdate(PatchModel):
    codigo: NonEmpty | None = None
    descricao: NonEmpty | None = None
    tipo: RubricType | None = None
    conta_debito: Account | None = None
    conta_credito: Account | None = None
    historico_id: HistoryCode | None = None
    historico: History | None = None
    status: RubricStatus | None = None
    debito_gera_cc: Flag | None = None
    debito_gera_cor: Flag | None = None
    credito_gera_cc: Flag | None = None
    credito_gera_cor: Flag | None = None


class RubricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int | None
    codigo: str | None
    descricao: str | None
    tipo: str | None
    conta_debito: str | None
    conta_credito: str | None
    historico_id: str | None
    historico: str | None
    status: str | None
    debito_gera_cc: int | None
    debito_gera_cor: int | None
    credito_gera_cc: int | None
    credito_gera_cor: int | None
