"""Explicitly rebuild synthetic inputs; never regenerates expected.json.

Run with the optional requirements-corpus.txt, from any working directory.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPANY = 'Empresa: 901 - EMPRESA SINTÉTICA ALFA LTDA'
HEADER = [COMPANY, 'CNPJ: 00.000.000/0000-00', 'EXTRATO MENSAL', 'Competência: 09/2026']


def rows(edge=False):
    data = [[s] for s in HEADER[:3]] + [['Competência:', '09/2026']]
    people = [('0001', 'ANA SINTÉTICA', '000.000.000-00', '3000,00', '300,00'),
              ('0002', 'JOÃO FICTÍCIO', '111.111.111-11', '2000,00', '200,00')]
    for matricula, nome, cpf, salary, discount in people:
        data += [['Empr.:', matricula, nome, 'Situação:', 'Ativo', 'CPF:', cpf],
                 ['Cargo:', '10', 'ANALISTA SINTÉTICO', 'C.B.O:', '000000'],
                 ['CC:', '0001'], ['001', 'SALARIO BASE', '30,00', salary, 'P'],
                 ['002', 'DESCONTO SINTÉTICO', '10,00', discount, 'D']]
        if edge:
            data += [['003', 'AJUSTE NEGATIVO', '1,00', '-10,50', 'D'],
                     ['004', 'VALOR ZERADO', '0,00', '0,00', 'P'],
                     ['001', 'SALARIO BASE', '30,00', salary, 'P']]
        data += [['Líquido:', '2700,00' if matricula == '0001' else '1800,00']]
    return data


def spreadsheets(case, extension, data):
    target = ROOT / case
    target.mkdir(exist_ok=True)
    path = target / ('input.' + extension)
    if extension == 'xlsx':
        from openpyxl import Workbook
        from datetime import datetime
        book = Workbook()
        book.properties.creator = 'Versal synthetic corpus'
        book.properties.lastModifiedBy = 'Versal synthetic corpus'
        book.properties.created = book.properties.modified = datetime(2026, 1, 1)
        book.active.title = 'Extrato sintético'
        for row in data:
            book.active.append(row)
        book.save(path)
        # Freeze ZIP timestamps and Office modification metadata for reproducibility.
        import io
        import re
        import zipfile
        source = zipfile.ZipFile(io.BytesIO(path.read_bytes()))
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name in source.namelist():
                content = source.read(name)
                if name == 'docProps/core.xml':
                    content = re.sub(rb'(<dcterms:modified[^>]*>).*?(</dcterms:modified>)',
                                     rb'\g<1>2026-01-01T00:00:00Z\g<2>', content)
                info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)
    else:
        import xlwt
        book = xlwt.Workbook()
        sheet = book.add_sheet('Extrato sintetico')
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                sheet.write(i, j, value)
        book.save(str(path))


def pdf(case, empty=False, accented=False):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    target = ROOT / case
    target.mkdir(exist_ok=True)
    pdfmetrics.registerFont(TTFont('Corpus', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    doc = Canvas(str(target / 'input.pdf'), pagesize=A4, invariant=1)
    doc.setAuthor('Versal synthetic corpus')
    doc.setTitle('Extrato mensal inteiramente sintético')
    for i, (name, cpf, salary, discount, net) in enumerate([
        ('ANA SINTÉTICA', '000.000.000-00', '3.000,00', '300,00', '2.700,00'),
        ('JOÃO FICTÍCIO', '111.111.111-11', '2.000,00', '200,00', '1.800,00'),
    ] if not empty else [('','','','','')]):
        lines = HEADER.copy()
        if not empty:
            lines += [f'Empr.: {i+1:04d} {name} Situação: Ativo CPF: {cpf}',
                      'Cargo: 10 ANALISTA SINTÉTICO C.B.O: 000000', 'CC: 0001',
                      f'001 SALARIO BASE 30,00 {salary} P',
                      f'002 DESCONTO SINTÉTICO 10,00 {discount} D',
                      f'ND: 0 NF: 0 Líquido: {net}']
        else:
            lines += ['SEM MOVIMENTOS - DOCUMENTO SINTÉTICO']
        doc.setFont('Corpus', 9)
        for line_no, text in enumerate(lines):
            doc.drawString(36, A4[1] - 45 - line_no * 18, text.replace('SALARIO BASE', 'SALÁRIO BASE') if accented else text)
        doc.showPage()
    doc.save()


if __name__ == '__main__':
    spreadsheets('extrato_xls', 'xls', rows())
    spreadsheets('extrato_xlsx', 'xlsx', rows())
    spreadsheets('extrato_xlsx_edge', 'xlsx', rows(edge=True))
    spreadsheets('extrato_xlsx_empty', 'xlsx', [['DOCUMENTO SINTÉTICO SEM CABEÇALHO']])
    pdf('extrato_pdf')
    pdf('extrato_pdf_empty', empty=True)
    pdf('extrato_pdf_accent', accented=True)
    print('Seven synthetic inputs rebuilt; expected outputs untouched.')
