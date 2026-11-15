"""Gera PDFs de TRE a partir dos modelos oficiais de entrega/devolução."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pymupdf

ASSETS_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'tre'
EMPRESA_NOME = 'VERSAL AGRO CONTABILIDADE E ASSESSORIA LTDA'
EMPRESA_CNPJ = '62.693.214/0001-48'
REPRESENTANTE = 'Leandro Ribeiro de Faria'
TZ = ZoneInfo('America/Sao_Paulo')

MESES = [
    'janeiro',
    'fevereiro',
    'março',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro',
]


@dataclass
class TreItemData:
    categoria_nome: str
    descricao: str
    numero_patrimonio: str
    quantidade: int = 1


def format_cpf(cpf: str) -> str:
    digits = ''.join(ch for ch in cpf if ch.isdigit()).zfill(11)[-11:]
    return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'


def format_cidade_data(moment: datetime) -> str:
    local = moment.astimezone(TZ) if moment.tzinfo else moment.replace(tzinfo=TZ)
    return f'Goiânia, {local.day:02d} de {MESES[local.month - 1]} de {local.year}.'


def _template_path(tipo: str) -> Path:
    name = 'TRE-Entrega.pdf' if tipo == 'entrega' else 'TRE-Devolucao.pdf'
    path = ASSETS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f'Modelo TRE não encontrado: {path}')
    return path


def _whiteout(page: pymupdf.Page, rect: pymupdf.Rect) -> None:
    page.add_redact_annot(rect, fill=(1, 1, 1))


def _apply(page: pymupdf.Page) -> None:
    page.apply_redactions(images=0)


def _insert(page: pymupdf.Page, point: tuple[float, float], text: str, fontsize: float = 10) -> None:
    page.insert_text(point, text, fontsize=fontsize, fontname='helv', color=(0, 0, 0))


def _write_items(page: pymupdf.Page, itens: list[TreItemData], start_y: float) -> None:
    y = start_y
    max_rows = 8
    for item in itens[:max_rows]:
        categoria = (item.categoria_nome or '')[:28]
        descricao = (item.descricao or '')[:42]
        patrimonio = (item.numero_patrimonio or '')[:18]
        _insert(page, (34.2, y), categoria, fontsize=10)
        _insert(page, (205.1, y), str(item.quantidade or 1), fontsize=10)
        _insert(page, (234.8, y), descricao, fontsize=10)
        _insert(page, (421.5, y), patrimonio, fontsize=10)
        _insert(page, (485.5, y), 'SIM', fontsize=10)
        y += 21.1


def generate_tre_pdf(
    *,
    tipo: str,
    codigo: str,
    colaborador_nome: str,
    colaborador_cpf: str,
    itens: list[TreItemData],
    created_at: datetime,
    output_path: Path,
) -> Path:
    doc = pymupdf.open(_template_path(tipo))
    page0 = doc[0]
    cpf = format_cpf(colaborador_cpf)
    data_txt = format_cidade_data(created_at)

    # Cabeçalho variável (nome/CPF) + número do TRE.
    _whiteout(page0, pymupdf.Rect(34, 142, 420, 158))
    _whiteout(page0, pymupdf.Rect(430, 142, 560, 158))
    _whiteout(page0, pymupdf.Rect(470, 40, 600, 58))
    _apply(page0)
    _insert(page0, (34.1, 154), colaborador_nome[:48], fontsize=11)
    _insert(page0, (435.2, 154), cpf, fontsize=11)
    _insert(page0, (480, 54), f'Nº {codigo}', fontsize=11)

    if tipo == 'entrega':
        # Limpa linhas de exemplo da tabela de itens (página 1).
        _whiteout(page0, pymupdf.Rect(30, 628, 580, 740))
        _apply(page0)
        _write_items(page0, itens, start_y=640)

        if doc.page_count > 1:
            page1 = doc[1]
            _whiteout(page1, pymupdf.Rect(388, 285, 590, 310))
            _whiteout(page1, pymupdf.Rect(130, 372, 320, 395))
            _whiteout(page1, pymupdf.Rect(130, 458, 320, 482))
            _apply(page1)
            _insert(page1, (390.4, 302), data_txt, fontsize=10)
            _insert(page1, (134.4, 388), colaborador_nome[:40], fontsize=10)
            _insert(page1, (134.4, 474), REPRESENTANTE, fontsize=10)
    else:
        _whiteout(page0, pymupdf.Rect(30, 252, 580, 335))
        _whiteout(page0, pymupdf.Rect(388, 480, 590, 510))
        _whiteout(page0, pymupdf.Rect(130, 570, 320, 595))
        _whiteout(page0, pymupdf.Rect(130, 656, 320, 682))
        _apply(page0)
        _write_items(page0, itens, start_y=264)
        _insert(page0, (390.4, 500), data_txt, fontsize=10)
        _insert(page0, (134.4, 586), colaborador_nome[:40], fontsize=10)
        _insert(page0, (134.4, 672), REPRESENTANTE, fontsize=10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()
    return output_path
