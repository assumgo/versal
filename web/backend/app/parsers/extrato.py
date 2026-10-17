"""Extracted from desktop 2.18; preserve characterized parsing decisions.

Source SHA-256: ab2203e8b0e56550dfcd1baa84e4c6a89618809b06fa9b420d722ea8fc6905c2
"""
import re
from decimal import Decimal

from .common import (
    _cell_code, _cell_money, _cell_str, _find_first_value_after,
    _is_verba_code, br_to_decimal, parse_company_from_text,
)
from .types import ParsedStatement


def parse_extrato_rows(rows: list[list[object]]) -> ParsedStatement:
    """Parser robusto para Extrato Mensal em XLS/XLSX."""
    competencia = ''
    for r in rows[:30]:
        vals=[_cell_str(x) for x in r]
        for i,v in enumerate(vals):
            if v.startswith('Competência') or v.startswith('Competencia'):
                for nxt in vals[i+1:i+30]:
                    m=re.search(r'(\d{2})/(\d{4})', nxt)
                    if m:
                        competencia=m.group(0); break
                    m=re.search(r'(\d{4})-(\d{2})-\d{2}', nxt)
                    if m:
                        competencia=f'{m.group(2)}/{m.group(1)}'; break
            if competencia: break
        if competencia: break

    result=[]; cur=None; patronal_values={}; in_resumo=False

    def finish():
        nonlocal cur
        if cur and (cur.get('cpf') or cur.get('nome')) and cur.get('rubricas'):
            result.append(cur.copy())
        cur=None

    def read_rubric_from(vals, idx, default_tipo='P'):
        if not _is_verba_code(vals[idx]):
            return None
        cod=_cell_code(vals[idx])
        desc_i=None
        for j in range(idx+1, min(len(vals), idx+12)):
            txt=_cell_str(vals[j])
            if txt and not re.fullmatch(r'[\d\.,/-]+', txt) and not re.match(r'^[A-Z]{1,3}:$', txt):
                desc_i=j; break
        if desc_i is None:
            return None
        desc=' '.join(_cell_str(vals[desc_i]).split())
        if not desc or desc.upper() in ('ND:', 'NF:', 'PROVENTOS:', 'DESCONTOS:'):
            return None
        nums=[]; tipo=''
        for j in range(desc_i+1, min(len(vals), desc_i+45)):
            txt=_cell_str(vals[j]).strip()
            if not txt:
                continue
            up=txt.upper()
            if up in ('P','D','E'):
                tipo=up
                break
            if re.search(r'\d', txt) and not re.match(r'^[A-Za-zÀ-ÿ]+:$', txt):
                nums.append(vals[j])
        if not nums or not tipo:
            return None
        valor=_cell_money(nums[-1])
        referencia=_cell_str(nums[0]) if len(nums) >= 2 else ''
        if valor == 0:
            return None
        return {'codigo':cod,'descricao':desc,'referencia':referencia,'valor':valor,'tipo':tipo or default_tipo}

    for r in rows:
        vals=[_cell_str(x) for x in r]

        for i,v in enumerate(vals):
            if v in ('Empresa:', 'RAT:', 'Contribuintes:', 'Terceiros:'):
                val=_find_first_value_after(vals, i, 12, 'number')
                if val != '':
                    patronal_values[v]=_cell_money(val)

        if any(v == 'Resumo por Rubrica' for v in vals):
            in_resumo=True; finish(); continue
        if any(('INSS FGTS' in v or 'Apuração Tributos' in v or 'Situações' in v) for v in vals):
            in_resumo=False; finish(); continue

        if any(v in ('Empr.:','Contr:') for v in vals):
            in_resumo=False; finish()
            cur={'matricula':'','nome':'','cpf':'','situacao':'','cargo':'','centro_custo':'','liquido':Decimal('0'),'rubricas':[]}
            for i,v in enumerate(vals):
                if v in ('Empr.:','Contr:'):
                    cur['matricula']=_cell_code(_find_first_value_after(vals, i, 10, 'number'))
                    found_matric=False
                    for j in range(i+1, min(len(vals), i+20)):
                        cell=_cell_str(vals[j])
                        if not cell:
                            continue
                        if not found_matric and re.fullmatch(r'\d+', _cell_code(cell) or ''):
                            found_matric=True; continue
                        if found_matric and cell and not cell.endswith(':') and not re.search(r'^\d+([,.]\d+)?$', cell):
                            cur['nome']=' '.join(cell.split()); break
                elif v.startswith('Situação') or v.startswith('Situacao'):
                    cur['situacao']=_cell_str(_find_first_value_after(vals, i, 12))
                elif v.startswith('CPF'):
                    cur['cpf']=_cell_str(_find_first_value_after(vals, i, 12, 'number'))
            continue

        if not cur:
            continue

        if any(('Total Geral' in v or 'Resumo por Rubrica' in v) for v in vals):
            finish(); in_resumo=True; continue

        for i,v in enumerate(vals):
            if v.startswith('CC:') and not cur.get('centro_custo'):
                cur['centro_custo']=_cell_code(_find_first_value_after(vals, i, 10, 'number'))
            if v.startswith('Cargo'):
                found_code=False
                for j in range(i+1, min(len(vals), i+20)):
                    cell=_cell_str(vals[j])
                    if not cell:
                        continue
                    if not found_code and re.fullmatch(r'\d+', _cell_code(cell) or ''):
                        found_code=True; continue
                    if found_code and cell and not cell.endswith(':'):
                        cur['cargo']=' '.join(cell.split()); break
            if v.startswith('Líquido') or v.startswith('Liquido'):
                nums=[x for x in vals[i+1:] if x and re.search(r'\d', x)]
                if nums:
                    cur['liquido']=_cell_money(nums[-1])

        for idx, cell in enumerate(vals):
            if _is_verba_code(cell):
                rub=read_rubric_from(vals, idx, 'D' if idx > 25 else 'P')
                if rub and not any(r0['codigo']==rub['codigo'] and r0['valor']==rub['valor'] for r0 in cur['rubricas']):
                    cur['rubricas'].append(rub)

    finish()
    flat='\n'.join(' '.join(_cell_str(x) for x in rr if _cell_str(x)) for rr in rows[:80])
    empresa=parse_company_from_text(flat)
    # Encargos patronais não são mais gerados pelo Extrato Mensal; vêm da aba Encargos da Empresa.
    return {'competencia': competencia, 'colaboradores': result, 'empresa': empresa, 'tipo_importacao': 'Extrato'}


def parse_extrato_text(text: str) -> ParsedStatement:
    comp = re.search(r'(?<![\d./-])(\d{2}/\d{4})(?![\d./-])', text)
    competencia = comp.group(1) if comp else ''
    result=[]
    blocks = re.split(r'(?=\b(?:Empr\.|Contr)\s*:\s*)', text)
    for b in blocks:
        head = re.search(r'(?:Empr\.|Contr)\s*:\s*(\d+)\s+(.+?)\s+Situação:\s*(.+?)\s+CPF:\s*([\d\.\-]+)', b, re.S)
        if not head: continue
        matricula, nome, situacao, cpf = head.groups()
        nome=' '.join(nome.split())
        cargo = ''
        m = re.search(r'Cargo:\s*\d*\s*(.+?)\s+C\.B\.O', b, re.S)
        if m: cargo=' '.join(m.group(1).split())
        centro_custo = ''
        m = re.search(r'\bCC:\s*([0-9A-Za-z\.\-]+)', b)
        if m: centro_custo = m.group(1).strip()
        liq = Decimal('0')
        m = re.search(r'Líquido:\s*(?:Informativa:.*?Informativa Dedutora:\s*\S+\s*)?([\d\.]+,\d{2})', b, re.S)
        if m: liq = br_to_decimal(m.group(1))
        lines=[]
        pay_area = b
        if 'Cargo:' in pay_area:
            pay_area = pay_area[pay_area.find('Cargo:'):]
        if 'ND:' in pay_area:
            pay_area = pay_area[:pay_area.find('ND:')]
        rub_pat = re.compile(r'(?<![\d/])\b(\d{3,5})\s+([A-ZÇÃÕÉÊÍÓÚ0-9][A-ZÇÃÕÉÊÍÓÚ0-9\.\-\sºª/#]+?)\s+([\d\.]+,\d{2})\s+([\d\.]+,\d{2})\s+([PD])(?=\s+\d{3,5}\s+|\s+ND:|\s+NF:|\n|$)', re.S)
        for match in rub_pat.finditer(pay_area):
            cod, desc, ref, val, tipo = match.groups()
            desc=' '.join(desc.split())
            if desc.upper().startswith(('BASE ', 'VALOR ', 'PROVENTOS', 'DESCONTOS', 'CARGO')):
                continue
            lines.append({'codigo': cod, 'descricao': desc, 'referencia': ref, 'valor': br_to_decimal(val), 'tipo': tipo})
        result.append({'matricula':matricula,'nome':nome,'cpf':cpf,'situacao':situacao.strip(),'cargo':cargo,'centro_custo':centro_custo,'liquido':liq,'rubricas':lines})
    patronal_values={}
    for key in ('Empresa:', 'RAT:', 'Contribuintes:', 'Terceiros:'):
        m = re.search(re.escape(key) + r'\s*([\d\.]+,\d{2})', text or '')
        if m:
            patronal_values[key]=br_to_decimal(m.group(1))
    # Encargos patronais não são mais gerados pelo Extrato Mensal; vêm da aba Encargos da Empresa.
    return {'competencia': competencia, 'colaboradores': result, 'empresa': parse_company_from_text(text), 'tipo_importacao': 'Extrato'}
