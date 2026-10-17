"""HTTP preview contract; all money is serialized as decimal text."""
from typing import Literal

from pydantic import BaseModel


class PreviewIssue(BaseModel):
    code: str
    severity: Literal['warning', 'blocking']
    message: str


class PreviewSummary(BaseModel):
    employees: int
    rubrics: int
    totals_by_type: dict[str, str]
    net_total: str


class PreviewCompany(BaseModel):
    codigo_siagri: str
    razao: str
    cnpj: str


class PreviewRubric(BaseModel):
    codigo: str
    descricao: str
    referencia: str
    valor: str
    tipo: str


class PreviewEmployee(BaseModel):
    matricula: str
    nome: str
    cpf: str
    situacao: str
    cargo: str
    centro_custo: str
    liquido: str
    rubricas: list[PreviewRubric]


class PreviewStatement(BaseModel):
    competencia: str
    empresa: PreviewCompany
    tipo_importacao: Literal['Extrato']
    colaboradores: list[PreviewEmployee]


class PayrollPreviewResponse(BaseModel):
    company_id: int
    requested_competence: str
    filename: str
    size_bytes: int
    sha256: str
    status: Literal['ready', 'blocked']
    issues: list[PreviewIssue]
    summary: PreviewSummary
    statement: PreviewStatement
