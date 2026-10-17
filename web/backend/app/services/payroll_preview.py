"""Read-only comparison and exact totals for a parsed monthly statement."""
from decimal import Decimal, localcontext
import re

from app.parsers.types import ParsedStatement
from app.schemas.payroll_preview import PayrollPreviewResponse, PreviewIssue, PreviewSummary

COMPETENCE = re.compile(r'^(0[1-9]|1[0-2])/[0-9]{4}$')


def exact_sum(values: list[Decimal]) -> str:
    if not values:
        return '0'
    lowest = min(v.as_tuple().exponent for v in values)
    highest = max(v.adjusted() for v in values)
    with localcontext() as context:
        context.prec = max(28, highest - lowest + len(str(len(values))) + 2)
        return str(sum(values, Decimal('0')))


def summarize(statement: ParsedStatement) -> PreviewSummary:
    people = statement['colaboradores']
    rubrics = [rubric for person in people for rubric in person['rubricas']]
    return PreviewSummary(
        employees=len(people), rubrics=len(rubrics),
        totals_by_type={kind: exact_sum([r['valor'] for r in rubrics if r['tipo'] == kind])
                        for kind in ('P', 'D', 'E')},
        net_total=exact_sum([p['liquido'] for p in people]),
    )


def build_preview(statement: ParsedStatement, *, company_id: int, company_cnpj: str | None,
                  competence: str, filename: str, size_bytes: int, sha256: str,
                  extension: str) -> PayrollPreviewResponse:
    issues = []

    def issue(code: str, message: str, severity: str = 'blocking') -> None:
        issues.append(PreviewIssue(code=code, severity=severity, message=message))

    detected = re.sub(r'\D', '', statement['empresa']['cnpj'])
    registered = re.sub(r'\D', '', company_cnpj or '')
    if len(detected) != 14 or len(registered) != 14:
        issue('company_cnpj_missing', 'Confira o CNPJ: o arquivo ou o cadastro não informa 14 dígitos.')
    elif detected != registered:
        issue('company_cnpj_mismatch', 'O CNPJ do arquivo difere da empresa selecionada.')
    actual = statement['competencia']
    if not actual:
        issue('competence_missing', 'O arquivo não informa a competência.')
    elif not COMPETENCE.fullmatch(actual):
        issue('competence_invalid', 'A competência detectada não está no formato MM/AAAA válido.')
    elif actual != competence:
        issue('competence_mismatch', 'A competência do arquivo difere da selecionada.')
    summary = summarize(statement)
    if not summary.employees:
        issue('no_employees', 'Nenhum colaborador foi identificado. Confira o documento e seu layout.')
    if not summary.rubrics:
        issue('no_rubrics', 'Nenhuma rubrica foi identificada. Confira o documento e seu layout.')
    issue('homologation_pending', 'A homologação funcional e Windows permanece pendente.', 'warning')
    if extension == '.pdf':
        issue('pdf_known_limitations', 'O leitor PDF mantém limitações conhecidas de acentos e captura de centro de custo como código de rubrica.', 'warning')
    else:
        issue('excel_known_limitations', 'Somente a primeira aba é lida. O leitor legado suprime rubricas de valor zero e duplicatas de código/valor.', 'warning')
    # Build a new structure; Decimal and the parser output remain untouched.
    public = dict(statement, colaboradores=[
        dict(person, liquido=str(person['liquido']), rubricas=[
            dict(rubric, valor=str(rubric['valor'])) for rubric in person['rubricas']
        ]) for person in statement['colaboradores']
    ])
    return PayrollPreviewResponse(
        company_id=company_id, requested_competence=competence, filename=filename,
        size_bytes=size_bytes, sha256=sha256,
        status='blocked' if any(i.severity == 'blocking' for i in issues) else 'ready',
        issues=issues, summary=summary, statement=public,
    )
