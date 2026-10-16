from pydantic import BaseModel, ConfigDict


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_siagri: str | None
    razao: str | None
    fantasia: str | None
    cnpj: str | None
    status: str | None
