from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.categoria import Categoria

DEFAULT_CATEGORIAS = [
    {'nome': 'Notebook', 'descricao': 'Notebooks e laptops corporativos'},
    {'nome': 'Monitor', 'descricao': 'Monitores e displays'},
    {'nome': 'Periféricos', 'descricao': 'Teclados, mouses, headsets e afins'},
    {'nome': 'Rede', 'descricao': 'Roteadores, switches, access points e cabos'},
    {'nome': 'Desktop', 'descricao': 'Computadores desktop e workstations'},
    {'nome': 'Servidor', 'descricao': 'Servidores físicos e appliances'},
]


def seed_categorias(db: Session) -> None:
    existing = {nome for (nome,) in db.execute(select(Categoria.nome)).all()}
    created = False
    for item in DEFAULT_CATEGORIAS:
        if item['nome'] in existing:
            continue
        db.add(Categoria(nome=item['nome'], descricao=item['descricao'], ativo=True))
        created = True
    if created:
        db.commit()
