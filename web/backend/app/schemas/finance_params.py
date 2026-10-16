from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.schemas.accounting import InputModel


class FinanceParamCreate(InputModel):
    tipo: Annotated[str, AfterValidator(str.strip)] = ''
    documento_id: str = ''
    parceiro_cpf_cnpj: str = ''
    codigo_parceiro_siagri: str = ''
    conta_contrapartida: str = ''
    centro_custo: str = ''
    vencimento_dia: Annotated[int, Field(strict=True, ge=1, le=31)] = 1
    historico: str = ''


class FinanceParamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int | None
    tipo: str | None
    documento_id: str | None
    parceiro_cpf_cnpj: str | None
    codigo_parceiro_siagri: str | None
    conta_contrapartida: str | None
    centro_custo: str | None
    vencimento_dia: int | None
    historico: str | None
    ativo: int | None
