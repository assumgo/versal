from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints, model_validator

from app.schemas.documents import validate_document


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_siagri: str | None
    razao: str | None
    fantasia: str | None
    cnpj: str | None
    status: str | None


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CNPJ = Annotated[str, AfterValidator(lambda value: validate_document(value, cnpj=True))]


class CompanyCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    razao: Name
    cnpj: CNPJ
    codigo_siagri: str | None = None
    fantasia: str | None = None
    status: Literal['Ativa', 'Inativa'] = 'Ativa'


class CompanyUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    razao: Name | None = None
    cnpj: CNPJ | None = None
    codigo_siagri: str | None = None
    fantasia: str | None = None
    status: Literal['Ativa', 'Inativa'] | None = None

    @model_validator(mode='after')
    def reject_null_required(self) -> 'CompanyUpdate':
        for field in ('razao', 'cnpj', 'status'):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f'{field} não pode ser nulo')
        return self
