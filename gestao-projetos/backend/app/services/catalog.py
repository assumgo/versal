from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import ProjectTemplate, TemplatePhase, TemplateTask

TEMPLATES = (
    {
        'key': 'rack',
        'name': 'Montagem de rack',
        'phases': (
            ('Levantamento', ('Conferir local e medidas',)),
            ('Materiais', ('Separar equipamentos e acessórios',)),
            ('Montagem', ('Fixar o rack e organizar os cabos',)),
            ('Testes', ('Validar energia e rede',)),
            ('Entrega', ('Registrar a conclusão com o responsável',)),
        ),
    },
    {
        'key': 'system',
        'name': 'Sistema',
        'phases': (
            ('Descoberta', ('Levantar requisitos e restrições',)),
            ('Desenho', ('Desenhar a solução e os fluxos',)),
            ('Construção', ('Implementar o sistema',)),
            ('Homologação', ('Validar com quem vai usar',)),
            ('Implantação', ('Colocar em uso e acompanhar o início',)),
        ),
    },
)


def ensure_templates(session: Session) -> None:
    existing = set(session.scalars(select(ProjectTemplate.key)))
    for spec in TEMPLATES:
        if spec['key'] in existing:
            continue
        template = ProjectTemplate(key=spec['key'], name=spec['name'])
        session.add(template)
        session.flush()
        for phase_index, (phase_name, tasks) in enumerate(spec['phases']):
            phase = TemplatePhase(template_id=template.id, name=phase_name, position=phase_index)
            session.add(phase)
            session.flush()
            for task_index, title in enumerate(tasks):
                session.add(TemplateTask(template_phase_id=phase.id, title=title, position=task_index))
    session.flush()


def list_templates(session: Session) -> list[ProjectTemplate]:
    ensure_templates(session)
    return list(session.scalars(
        select(ProjectTemplate)
        .options(selectinload(ProjectTemplate.phases).selectinload(TemplatePhase.tasks))
        .order_by(ProjectTemplate.id)
    ))


def get_template(session: Session, key: str) -> ProjectTemplate | None:
    ensure_templates(session)
    return session.scalar(
        select(ProjectTemplate)
        .options(selectinload(ProjectTemplate.phases).selectinload(TemplatePhase.tasks))
        .where(ProjectTemplate.key == key)
    )
