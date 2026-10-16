from typing import Annotated, Literal
from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator
from app.schemas.documents import validate_document

CPF = Annotated[str, AfterValidator(validate_document)]


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nome: str | None = None
    cpf: CPF | None = None
    matricula: str | None = None
    cargo: str | None = None
    centro_custo: str | None = None
    codigo_correntista: str | None = None
    status: Literal['Ativo', 'Inativo'] = 'Ativo'


class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nome: str | None = None
    cpf: CPF | None = None
    matricula: str | None = None
    cargo: str | None = None
    centro_custo: str | None = None
    codigo_correntista: str | None = None
    status: Literal['Ativo', 'Inativo'] | None = None

    @model_validator(mode='after')
    def reject_null_required(self) -> 'EmployeeUpdate':
        for field in ('status',):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f'{field} não pode ser nulo')
        return self


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int | None
    nome: str | None
    cpf: str | None
    matricula: str | None
    cargo: str | None
    centro_custo: str | None
    codigo_correntista: str | None
    status: str | None
