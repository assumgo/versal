from typing import Annotated

from pydantic import BaseModel, StringConstraints

Competence = Annotated[str, StringConstraints(pattern=r'^(0[1-9]|1[0-2])/[0-9]{4}$')]


class AccountingReviewRow(BaseModel):
    id: int
    competencia: str
    cpf: str | None
    nome: str | None
    codigo_verba: str | None
    verba: str | None
    valor: str | None
    conta_debito: str | None
    debito_gera_cc: bool
    debito_gera_cor: bool
    conta_credito: str | None
    credito_gera_cc: bool
    credito_gera_cor: bool
    historico_id: str
    historico: str | None
    centro_custo: str | None
    correntista: str
    fonte: str | None
