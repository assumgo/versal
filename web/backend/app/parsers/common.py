"""Extracted from desktop 2.18; preserve characterized parsing decisions.

Source SHA-256: ab2203e8b0e56550dfcd1baa84e4c6a89618809b06fa9b420d722ea8fc6905c2
"""
import re
from decimal import Decimal

from .types import ParsedCompany


def br_to_decimal(s: object) -> Decimal:
    """Converte valores brasileiros para Decimal sem quebrar em textos de relatório.

    Corrige o erro decimal.ConversionSyntax quando o leitor recebe células/linhas com
    textos misturados, datas, espaços ou mais de um número. Prioriza valores monetários
    no padrão brasileiro e nunca propaga exceção de conversão para a interface.
    """
    if s is None:
        return Decimal('0')
    if isinstance(s, Decimal):
        return s
    if isinstance(s, (int, float)):
        try:
            return Decimal(str(s)).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0')
    raw = str(s).replace('\xa0', ' ').strip()
    if not raw:
        return Decimal('0')
    # Primeiro procura valores monetários explícitos: 1.234,56 ou 1234,56.
    tokens = re.findall(r'-?\d{1,3}(?:\.\d{3})*,\d{2}|-?\d+,\d{2}', raw)
    if tokens:
        txt = tokens[-1].replace('.', '').replace(',', '.')
        try:
            return Decimal(txt).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0')
    # Depois aceita decimal internacional isolado: 1234.56.
    m = re.search(r'-?\d+\.\d{1,4}', raw)
    if m:
        try:
            return Decimal(m.group(0)).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0')
    # Por fim, inteiro simples.
    m = re.search(r'-?\d+', raw)
    if m:
        try:
            return Decimal(m.group(0)).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0')
    return Decimal('0')


def parse_company_from_text(text: str) -> ParsedCompany:
    """Extrai empresa do relatório de folha pelo conteúdo do arquivo.

    Regra da v1.16:
    - O CNPJ do PDF/XLS é a chave principal da empresa.
    - A empresa do arquivo prevalece sobre a empresa logada.
    - O nome do arquivo nunca define a empresa.
    """
    raw = text or ''
    empresa = {'codigo_siagri':'', 'razao':'', 'cnpj':''}

    linhas = [' '.join(l.replace('\t', ' ').split()) for l in raw.splitlines() if l and l.strip()]
    raw_norm = '\n'.join(linhas)

    # Captura empresa em relatórios Excel onde o rótulo e o valor ficam na mesma linha.
    m_empresa_inline = re.search(r'Empresa:\s*(?:\S+\s+){0,25}?(\d{1,6})\s*-\s*([^\n]+?)(?=\s+(?:Página|Pagina|CNPJ:|CNPJ\b)|$)', raw_norm, re.I)
    if m_empresa_inline:
        empresa['codigo_siagri'] = m_empresa_inline.group(1).strip()
        empresa['razao'] = ' '.join(m_empresa_inline.group(2).split())

    # CNPJ com máscara ou sem máscara. Usa o primeiro CNPJ encontrado no cabeçalho do extrato.
    mcnpj = re.search(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', raw_norm)
    if not mcnpj:
        mcnpj = re.search(r'\b\d{14}\b', raw_norm)
    if mcnpj:
        empresa['cnpj'] = mcnpj.group(0)

    def is_company_line(linha):
        u = linha.upper()
        if any(x in u for x in ('PÁGINA', 'PAGINA', 'EMISSÃO', 'EMISSAO', 'HORAS', 'EXTRATO',
                                'EMPRESA:', 'COMPETÊNCIA', 'COMPETENCIA', 'CÁLCULO', 'CALCULO',
                                'COMPLEMENTO', 'CNPJ:', 'FOLHA MENSAL', 'SISTEMA LICENCIADO',
                                'TODOS', 'EMPREGADOS:', 'VÍNCULO:', 'VINCULO:', 'CARGO:', 'SITUAÇÃO:', 'SITUACAO:')):
            return None
        m = re.search(r'^\s*(\d{1,6})\s*-\s*(.{3,160})\s*$', linha)
        if not m:
            return None
        raz = ' '.join(m.group(2).split())
        # Evita capturar rubricas ou textos genéricos.
        if re.search(r'\b(LTDA|LTD|S/A|S\.A\.?|EIRELI|ME\b|EPP\b|CIA\b|FAZENDA|AGRO|COMERCIO|COMÉRCIO|ASSESSORIA|CONTABILIDADE)\b', raz.upper()):
            return (m.group(1), raz)
        return (m.group(1), raz)

    candidatos = []
    for idx, linha in enumerate(linhas):
        parsed = is_company_line(linha)
        if parsed:
            candidatos.append((idx, parsed[0], parsed[1]))

    escolhido = None
    if candidatos:
        # Prioriza a linha da empresa mais próxima do CNPJ detectado.
        if empresa['cnpj']:
            idxs_cnpj = [i for i,l in enumerate(linhas) if empresa['cnpj'] in l or re.sub(r'\D','',empresa['cnpj']) in re.sub(r'\D','',l)]
            idx_cnpj = idxs_cnpj[0] if idxs_cnpj else 0
            escolhido = sorted(candidatos, key=lambda t: abs(t[0]-idx_cnpj))[0]
        else:
            escolhido = candidatos[0]

    if escolhido:
        empresa['codigo_siagri'] = escolhido[1].strip()
        empresa['razao'] = escolhido[2].strip()
    return empresa


def _cell_str(v: object) -> str:
    if v is None:
        return ''
    try:
        from datetime import date, datetime
        if isinstance(v, datetime):
            return v.strftime('%d/%m/%Y')
        if isinstance(v, date):
            return v.strftime('%d/%m/%Y')
    except Exception:
        pass
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _cell_money(v: object) -> Decimal:
    if v is None or v == '':
        return Decimal('0')
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, float)):
        try:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0')
    txt = str(v).strip()
    if not txt:
        return Decimal('0')
    # Evita erro em células mescladas/linhas completas com texto e vários números.
    return br_to_decimal(txt)


def _cell_code(v: object) -> str:
    if v is None or v == '':
        return ''
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return re.sub(r'\.0$', '', str(v).strip())


def _find_first_value_after(vals: list[object], start_idx: int, max_ahead: int = 20, want: str = 'any') -> object:
    """Busca o primeiro valor útil após um rótulo numa linha XLS convertida para lista."""
    for j in range(start_idx+1, min(len(vals), start_idx+1+max_ahead)):
        v = _cell_str(vals[j])
        if not v:
            continue
        if want == 'number':
            if re.search(r'\d', v):
                return vals[j]
        else:
            if not re.match(r'^[A-Za-zÀ-ÿ .ºª/]+:$', v):
                return vals[j]
    return ''


def _is_verba_code(v: object) -> bool:
    c = _cell_code(v)
    return bool(c and re.fullmatch(r'\d{1,8}', c))
