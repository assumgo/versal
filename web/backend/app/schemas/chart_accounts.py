from pydantic import BaseModel, ConfigDict

from app.schemas.accounting import AccountCode, Flag, InputModel, NonEmpty, PatchModel


class ChartAccountCreate(InputModel):
    conta: AccountCode
    descricao: NonEmpty
    utiliza_cc: Flag = 0
    tipo_correntista: NonEmpty = '9-Nenhum'


class ChartAccountUpdate(PatchModel):
    descricao: NonEmpty | None = None
    utiliza_cc: Flag | None = None
    tipo_correntista: NonEmpty | None = None


class ChartAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int | None
    conta: str | None
    descricao: str | None
    utiliza_cc: int | None
    tipo_correntista: str | None
    gera_cor: int | None
