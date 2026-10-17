"""Desktop statement shape; monetary values stay Decimal until serialization."""
from decimal import Decimal
from typing import Literal, TypedDict


class ParsedCompany(TypedDict):
    codigo_siagri: str
    razao: str
    cnpj: str


class ParsedRubric(TypedDict):
    codigo: str
    descricao: str
    referencia: str
    valor: Decimal
    tipo: str


class ParsedEmployee(TypedDict):
    matricula: str
    nome: str
    cpf: str
    situacao: str
    cargo: str
    centro_custo: str
    liquido: Decimal
    rubricas: list[ParsedRubric]


class ParsedStatement(TypedDict):
    competencia: str
    empresa: ParsedCompany
    tipo_importacao: Literal['Extrato']
    colaboradores: list[ParsedEmployee]
