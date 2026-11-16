"""Gera PDFs de TRE a partir do modelo Excel oficial (TRE-Modelo.xlsx)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pymupdf
from openpyxl import load_workbook
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.pagebreak import Break
from openpyxl.worksheet.properties import PageSetupProperties

ASSETS_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'tre'
TEMPLATE_XLSX = ASSETS_DIR / 'TRE-Modelo.xlsx'
SHEET_ENTREGA = 'TRE-Entrega'
SHEET_DEVOLUCAO = 'TRE-Devolução'
REPRESENTANTE = 'Leandro Ribeiro Faria'
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

# Linhas da tabela de itens no modelo oficial
ITEM_COLS = ('B', 'E', 'F', 'I', 'K')
ENTREGA_ITEM_START = 46
ENTREGA_ITEM_ROWS = 5
DEVOLUCAO_ITEM_START = 18
DEVOLUCAO_ITEM_ROWS = 5
# Quebra antes do 2º cabeçalho/logo da guia de entrega (página de assinaturas)
ENTREGA_PAGE_BREAK_AFTER = 51


@dataclass
class TreItemData:
    descricao: str
    marca: str
    modelo: str
    numero_patrimonio: str
    quantidade: int = 1
    # compatível com snapshots antigos
    categoria_nome: str = ''


def format_cpf(cpf: str) -> str:
    digits = ''.join(ch for ch in cpf if ch.isdigit()).zfill(11)[-11:]
    return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'


def _as_local_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        local = value.astimezone(TZ) if value.tzinfo else value.replace(tzinfo=TZ)
        return local.date()
    return value


def format_data_parts(value: date | datetime) -> tuple[str, str]:
    local = _as_local_date(value)
    mid = f'{local.day} de {MESES[local.month - 1]} de'
    year = f'{local.year}.'
    return mid, year


def _clear_item_rows(ws, start_row: int, count: int) -> None:
    for row in range(start_row, start_row + count):
        for col in ITEM_COLS:
            ws[f'{col}{row}'] = None


def _write_items(ws, itens: list[TreItemData], start_row: int, max_rows: int) -> None:
    _clear_item_rows(ws, start_row, max_rows)
    for index, item in enumerate(itens[:max_rows]):
        row = start_row + index
        descricao = (item.descricao or item.categoria_nome or '').strip()
        ws[f'B{row}'] = descricao
        ws[f'E{row}'] = int(item.quantidade or 1)
        ws[f'F{row}'] = (item.marca or '').strip()
        ws[f'I{row}'] = (item.modelo or '').strip()
        ws[f'K{row}'] = (item.numero_patrimonio or '').strip()


def _apply_print_layout(ws, *, tipo: str) -> None:
    """Ajusta impressão para PDF nítido em A4 (entrega em 2 páginas, devolução em 1)."""
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.5, bottom=0.55)

    if tipo == 'entrega':
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True, autoPageBreaks=False)
        ws.print_area = 'B2:L83'
        ws.row_breaks = type(ws.row_breaks)()
        ws.row_breaks.append(Break(id=ENTREGA_PAGE_BREAK_AFTER))
    else:
        ws.page_setup.fitToHeight = 1
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True, autoPageBreaks=False)
        ws.print_area = 'B2:L46'


def _fill_workbook(
    *,
    tipo: str,
    colaborador_nome: str,
    colaborador_cpf: str,
    itens: list[TreItemData],
    data_documento: date | datetime,
    output_xlsx: Path,
) -> None:
    if not TEMPLATE_XLSX.exists():
        raise FileNotFoundError(f'Modelo Excel TRE não encontrado: {TEMPLATE_XLSX}')

    wb = load_workbook(TEMPLATE_XLSX)
    keep = SHEET_ENTREGA if tipo == 'entrega' else SHEET_DEVOLUCAO
    for name in list(wb.sheetnames):
        if name != keep:
            del wb[name]
    ws = wb[keep]

    cpf = format_cpf(colaborador_cpf)
    data_mid, data_year = format_data_parts(data_documento)
    tipo_termo = (
        'Tipo de Termo: Entrega de Equipamentos'
        if tipo == 'entrega'
        else 'Tipo de Termo: Devolução de Equipamentos'
    )

    # 1-Nome, 2-CPF, 3-Tipo de Termo (sem número do TRE no cabeçalho)
    ws['B10'] = colaborador_nome
    ws['J10'] = cpf
    ws['B11'] = tipo_termo

    if tipo == 'entrega':
        # 4-Itens | 5-Data (previsão) | 6-Colaborador
        _write_items(ws, itens, start_row=ENTREGA_ITEM_START, max_rows=ENTREGA_ITEM_ROWS)
        ws['I71'] = 'Goiânia,'
        ws['J71'] = data_mid
        ws['L71'] = data_year
        ws['D77'] = colaborador_nome
        ws['D83'] = REPRESENTANTE
    else:
        _write_items(ws, itens, start_row=DEVOLUCAO_ITEM_START, max_rows=DEVOLUCAO_ITEM_ROWS)
        ws['I34'] = 'Goiânia,'
        ws['J34'] = data_mid
        ws['L34'] = data_year
        ws['D40'] = colaborador_nome
        ws['D46'] = REPRESENTANTE

    _apply_print_layout(ws, tipo=tipo)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_xlsx)
    wb.close()


def _convert_xlsx_to_pdf(xlsx_path: Path, output_pdf: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix='tre-pdf-') as tmp:
        tmp_dir = Path(tmp)
        result = subprocess.run(
            [
                'soffice',
                '--headless',
                '--nologo',
                '--nofirststartwizard',
                '--convert-to',
                'pdf:calc_pdf_Export',
                '--outdir',
                str(tmp_dir),
                str(xlsx_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                'Falha ao converter TRE Excel para PDF: '
                f'{result.stderr.strip() or result.stdout.strip() or result.returncode}'
            )
        produced = next(tmp_dir.glob('*.pdf'), None)
        if not produced:
            raise RuntimeError('Conversão LibreOffice não gerou PDF')
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(produced, output_pdf)
    return output_pdf


def _write_footer(pdf_path: Path, codigo: str) -> None:
    """Mantém o número do TRE apenas no rodapé (não no cabeçalho)."""
    doc = pymupdf.open(pdf_path)
    try:
        for index, page in enumerate(doc):
            footer = f'TRE Nº {codigo}  ·  Página {index + 1}/{doc.page_count}'
            page.draw_rect(
                pymupdf.Rect(36, page.rect.height - 28, page.rect.width - 36, page.rect.height - 8),
                color=(1, 1, 1),
                fill=(1, 1, 1),
            )
            page.insert_textbox(
                pymupdf.Rect(36, page.rect.height - 26, page.rect.width - 36, page.rect.height - 8),
                footer,
                fontsize=9,
                fontname='helv',
                color=(0.15, 0.15, 0.15),
                align=pymupdf.TEXT_ALIGN_CENTER,
            )
        tmp_path = pdf_path.with_suffix('.footer.pdf')
        doc.save(tmp_path, deflate=True)
    finally:
        doc.close()
    tmp_path.replace(pdf_path)


def generate_tre_pdf(
    *,
    tipo: str,
    codigo: str,
    colaborador_nome: str,
    colaborador_cpf: str,
    itens: list[TreItemData],
    created_at: datetime,
    output_path: Path,
    data_documento: date | datetime | None = None,
) -> Path:
    data_ref = data_documento or created_at
    with tempfile.TemporaryDirectory(prefix='tre-xlsx-') as tmp:
        xlsx_path = Path(tmp) / f'TRE-{codigo}-{tipo}.xlsx'
        _fill_workbook(
            tipo=tipo,
            colaborador_nome=colaborador_nome,
            colaborador_cpf=colaborador_cpf,
            itens=itens,
            data_documento=data_ref,
            output_xlsx=xlsx_path,
        )
        _convert_xlsx_to_pdf(xlsx_path, output_path)
    _write_footer(output_path, codigo)
    return output_path
