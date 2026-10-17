import re

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import ChartAccount, Employee, PayrollImport, PayrollLine, Rubric
from app.schemas.accounting import normalize_account
from app.services.accounting_review import digits, effective_cc, effective_cor, review_history

_VALID_COMPETENCE = re.compile(r'^(0[1-9]|1[0-2])/[0-9]{4}$')


def list_competences(db: Session, company_id: int) -> list[str]:
    values = db.scalars(select(PayrollImport.competencia).where(
        PayrollImport.company_id == company_id, PayrollImport.competencia.is_not(None),
        PayrollImport.competencia != '').distinct()).all()
    valid = sorted((value for value in values if _VALID_COMPETENCE.fullmatch(value)),
                   key=lambda value: (value[3:], value[:2]), reverse=True)
    return valid + sorted(value for value in values if not _VALID_COMPETENCE.fullmatch(value))


def first_by(rows, key):
    result = {}
    for row in rows:
        result.setdefault(key(row), row)
    return result


def list_for_company(db: Session, company_id: int, *, competence: str, offset: int = 0, limit: int = 50) -> dict:
    scope = (PayrollLine.company_id == company_id, PayrollImport.company_id == company_id,
             PayrollImport.competencia == competence)
    source = select(PayrollLine, PayrollImport.competencia, PayrollImport.status).join(
        PayrollImport, PayrollImport.id == PayrollLine.import_id).where(*scope)
    total = db.scalar(select(func.count()).select_from(PayrollLine).join(
        PayrollImport, PayrollImport.id == PayrollLine.import_id).where(*scope))
    page = db.execute(source.order_by(PayrollLine.nome.nulls_first(), PayrollLine.codigo_verba.nulls_first(),
                                    PayrollLine.id).offset(offset).limit(limit)).all()
    if not page:
        return {'items': [], 'total': total, 'offset': offset, 'limit': limit}
    codes = {line.codigo_verba for line, _, _ in page if line.codigo_verba is not None}
    rubrics = first_by(db.scalars(select(Rubric).where(Rubric.company_id == company_id,
        Rubric.codigo.in_(codes)).order_by(Rubric.id)), lambda row: row.codigo)
    cpfs = {line.cpf for line, _, _ in page if line.cpf}
    names = {line.nome.upper() for line, _, _ in page if not line.cpf and line.nome is not None}
    employees = list(db.scalars(select(Employee).where(Employee.company_id == company_id,
        or_(Employee.cpf.in_(cpfs), func.upper(Employee.nome).in_(names))).order_by(Employee.id)))
    by_cpf = first_by(employees, lambda row: row.cpf)
    by_name = first_by(employees, lambda row: row.nome.upper() if row.nome is not None else None)
    account_codes = {normalize_account(code) for rb in rubrics.values()
                     for code in (rb.conta_debito, rb.conta_credito) if code}
    plans = first_by(db.scalars(select(ChartAccount).where(ChartAccount.company_id == company_id,
        ChartAccount.conta.in_(account_codes)).order_by(ChartAccount.id)), lambda row: row.conta)
    result = []
    for line, comp, source in page:
        rubric = rubrics.get(line.codigo_verba)
        employee = by_cpf.get(line.cpf) if line.cpf else (by_name.get(line.nome.upper()) if line.nome is not None else None)
        row = {
            'id': line.id, 'competencia': comp, 'cpf': line.cpf, 'nome': line.nome,
            'codigo_verba': line.codigo_verba, 'verba': line.verba,
            'valor': str(line.valor) if line.valor is not None else None,
            'historico_id': review_history(rubric.historico_id) if rubric else '',
            'historico': rubric.historico if rubric else '',
            'centro_custo': employee.centro_custo if employee else '',
            'correntista': digits(employee.cpf) if employee else '', 'fonte': source,
        }
        for side in ('debito', 'credito'):
            account = getattr(rubric, f'conta_{side}') if rubric else ''
            plan = plans.get(normalize_account(account)) if account else None
            cc = getattr(rubric, f'{side}_gera_cc') if rubric else 0
            cor = getattr(rubric, f'{side}_gera_cor') if rubric else 0
            row[f'conta_{side}'] = account
            row[f'{side}_gera_cc'] = effective_cc(plan.utiliza_cc if plan else None, cc)
            row[f'{side}_gera_cor'] = bool(rubric) and effective_cor(
                account, plan.gera_cor if plan else None, cor, employee is not None)
        result.append(row)
    return {'items': result, 'total': total, 'offset': offset, 'limit': limit}
