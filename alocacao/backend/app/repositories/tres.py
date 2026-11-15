from datetime import date, datetime, time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import ROOT
from app.models.colaborador import Colaborador
from app.models.tre import Tre, TreItem
from app.services.tre_pdf import TreItemData, generate_tre_pdf
from app.utils.codigos import next_numeric_codigo

TRE_CODIGO_START = 1
TRES_DIR = ROOT / 'data' / 'tres'


def generate_codigo(db: Session) -> str:
    codes = list(db.scalars(select(Tre.codigo)).all())
    return next_numeric_codigo(codes, start=TRE_CODIGO_START)


def get_tre(db: Session, tre_id: int) -> Tre | None:
    return db.scalars(
        select(Tre)
        .options(joinedload(Tre.colaborador), joinedload(Tre.itens))
        .where(Tre.id == tre_id)
    ).unique().first()


def list_tres(
    db: Session,
    *,
    nome: str | None = None,
    codigo: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[Tre]:
    query = select(Tre).options(joinedload(Tre.colaborador), joinedload(Tre.itens)).order_by(Tre.created_at.desc())
    if codigo:
        query = query.where(Tre.codigo.contains(codigo.strip()))
    if nome:
        query = query.join(Tre.colaborador).where(Colaborador.nome.ilike(f'%{nome.strip()}%'))
    if data_inicio is not None:
        start = datetime.combine(data_inicio, time.min)
        query = query.where(Tre.created_at >= start)
    if data_fim is not None:
        end = datetime.combine(data_fim, time.max)
        query = query.where(Tre.created_at <= end)
    return list(db.scalars(query).unique().all())


def create_tre_with_pdf(
    db: Session,
    *,
    tipo: str,
    colaborador: Colaborador,
    itens: list[dict],
) -> Tre:
    codigo = generate_codigo(db)
    pdf_name = f'TRE-{codigo}-{tipo}.pdf'
    pdf_path = TRES_DIR / pdf_name

    tre = Tre(
        codigo=codigo,
        tipo=tipo,
        colaborador_id=colaborador.id,
        pdf_path=str(pdf_path),
    )
    db.add(tre)
    db.flush()

    item_rows: list[TreItem] = []
    item_data: list[TreItemData] = []
    for raw in itens:
        row = TreItem(
            tre_id=tre.id,
            equipamento_id=raw.get('equipamento_id'),
            alocacao_id=raw.get('alocacao_id'),
            quantidade=raw.get('quantidade', 1),
            categoria_nome=raw['categoria_nome'],
            descricao=raw['descricao'],
            numero_patrimonio=raw['numero_patrimonio'],
        )
        db.add(row)
        item_rows.append(row)
        item_data.append(
            TreItemData(
                categoria_nome=row.categoria_nome,
                descricao=row.descricao,
                numero_patrimonio=row.numero_patrimonio,
                quantidade=row.quantidade,
            )
        )

    db.flush()
    generate_tre_pdf(
        tipo=tipo,
        codigo=codigo,
        colaborador_nome=colaborador.nome,
        colaborador_cpf=colaborador.cpf,
        itens=item_data,
        created_at=datetime.now().astimezone(),
        output_path=pdf_path,
    )
    db.commit()
    return get_tre(db, tre.id)  # type: ignore[return-value]
