from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.alocacao import Alocacao
from app.models.colaborador import Colaborador
from app.models.equipamento import Equipamento
from app.models.local import Local
from app.models.produto import Produto
from app.repositories import equipamentos as equipamentos_repo
from app.repositories import tres as tres_repo
from app.schemas.alocacao import AlocacaoCreate
from app.utils.codigos import next_numeric_codigo

ALOCACAO_CODIGO_START = 1


def generate_codigo(db: Session) -> str:
    codes = list(db.scalars(select(Alocacao.codigo)).all())
    return next_numeric_codigo(codes, start=ALOCACAO_CODIGO_START)


def _load_options():
    return (
        joinedload(Alocacao.colaborador),
        joinedload(Alocacao.local),
        joinedload(Alocacao.equipamento).joinedload(Equipamento.produto).joinedload(Produto.categoria),
    )


def list_alocacoes(
    db: Session,
    *,
    ativa: bool | None = None,
    tipo: str | None = None,
    q: str | None = None,
) -> list[Alocacao]:
    query = select(Alocacao).options(*_load_options()).order_by(Alocacao.created_at.desc())
    if ativa is not None:
        query = query.where(Alocacao.ativa.is_(ativa))
    if tipo:
        query = query.where(Alocacao.tipo == tipo)
    if q and q.strip():
        term = f'%{q.strip()}%'
        query = (
            query.outerjoin(Alocacao.colaborador)
            .outerjoin(Alocacao.local)
            .outerjoin(Alocacao.equipamento)
            .where(
                (Alocacao.codigo.ilike(term))
                | (Colaborador.nome.ilike(term))
                | (Local.nome.ilike(term))
                | (Equipamento.codigo.ilike(term))
            )
        )
    return list(db.scalars(query).unique().all())


def get_alocacao(db: Session, alocacao_id: int) -> Alocacao | None:
    return db.scalars(
        select(Alocacao).options(*_load_options()).where(Alocacao.id == alocacao_id)
    ).unique().first()


def get_ativa_por_equipamento(db: Session, equipamento_id: int) -> Alocacao | None:
    return db.scalars(
        select(Alocacao)
        .options(*_load_options())
        .where(
            Alocacao.equipamento_id == equipamento_id,
            Alocacao.tipo == 'entrega',
            Alocacao.ativa.is_(True),
        )
        .order_by(Alocacao.id.desc())
    ).unique().first()


def estoque_disponivel_produto(db: Session, produto_id: int) -> int:
    """Quantidade de equipamentos do produto sem entrega ativa."""
    equipamentos = list(
        db.scalars(select(Equipamento.id).where(Equipamento.produto_id == produto_id)).all()
    )
    if not equipamentos:
        return 0
    alocados = set(
        db.scalars(
            select(Alocacao.equipamento_id).where(
                Alocacao.equipamento_id.in_(equipamentos),
                Alocacao.tipo == 'entrega',
                Alocacao.ativa.is_(True),
            )
        ).all()
    )
    return len([eid for eid in equipamentos if eid not in alocados])


def _item_snapshot(equipamento: Equipamento, quantidade: int) -> dict:
    produto = equipamento.produto
    categoria = produto.categoria if produto else None
    return {
        'equipamento_id': equipamento.id,
        'categoria_nome': categoria.nome if categoria else '',
        'descricao': produto.descricao if produto else 'Equipamento',
        'marca': produto.marca if produto else '',
        'modelo': produto.modelo if produto else '',
        'numero_patrimonio': equipamento.numero_patrimonio,
        'quantidade': quantidade,
    }


def criar_movimento(db: Session, payload: AlocacaoCreate) -> tuple[Alocacao, object | None]:
    equipamento = equipamentos_repo.get_equipamento(db, payload.equipamento_id)
    if not equipamento:
        raise ValueError('Equipamento não encontrado')
    if not equipamento.produto_id:
        raise ValueError('Equipamento sem produto vinculado não pode ser movimentado')

    produto = equipamento.produto
    if not produto:
        raise ValueError('Produto do equipamento não encontrado')

    colaborador = None
    local = None
    if payload.destino_tipo == 'colaborador':
        colaborador = db.get(Colaborador, payload.colaborador_id)
        if not colaborador:
            raise ValueError('Colaborador inválido')
        if not colaborador.ativo:
            raise ValueError('Colaborador inativo')
    else:
        local = db.get(Local, payload.local_id)
        if not local:
            raise ValueError('Local inválido')

    if payload.quantidade != 1:
        raise ValueError('Quantidade deve ser 1 por equipamento')

    disponivel = estoque_disponivel_produto(db, produto.id)
    ativa_atual = get_ativa_por_equipamento(db, equipamento.id)

    tre = None
    referencia_id = None
    ativa = False

    if payload.tipo == 'entrega':
        if ativa_atual:
            raise ValueError(f'Equipamento {equipamento.codigo} já está alocado')
        if disponivel < payload.quantidade:
            raise ValueError('Estoque disponível insuficiente para o produto')
        ativa = True
    else:
        if not ativa_atual:
            raise ValueError(f'Equipamento {equipamento.codigo} não possui entrega ativa para devolução')
        if ativa_atual.destino_tipo != payload.destino_tipo:
            raise ValueError('Destino da devolução deve ser o mesmo da entrega ativa')
        if payload.destino_tipo == 'colaborador' and ativa_atual.colaborador_id != payload.colaborador_id:
            raise ValueError('Devolução deve ser para o mesmo colaborador da entrega')
        if payload.destino_tipo == 'local' and ativa_atual.local_id != payload.local_id:
            raise ValueError('Devolução deve ser para o mesmo local da entrega')
        referencia_id = ativa_atual.id
        ativa_atual.ativa = False
        db.add(ativa_atual)

    alocacao = Alocacao(
        codigo=generate_codigo(db),
        tipo=payload.tipo,
        destino_tipo=payload.destino_tipo,
        equipamento_id=equipamento.id,
        quantidade=payload.quantidade,
        colaborador_id=payload.colaborador_id,
        local_id=payload.local_id,
        referencia_id=referencia_id,
        data_previsao=payload.data_previsao,
        ativa=ativa,
    )
    db.add(alocacao)
    db.flush()

    if payload.destino_tipo == 'colaborador' and colaborador:
        snap = _item_snapshot(equipamento, payload.quantidade)
        snap['alocacao_id'] = alocacao.id
        data_doc = payload.data_previsao
        if data_doc is None and ativa_atual is not None:
            data_doc = ativa_atual.data_previsao
        tre = tres_repo.create_tre_with_pdf(
            db,
            tipo=payload.tipo,
            colaborador=colaborador,
            itens=[snap],
            data_documento=data_doc,
        )
        alocacao.tre_id = tre.id
        db.add(alocacao)
        db.commit()
    else:
        db.commit()

    refreshed = get_alocacao(db, alocacao.id)
    return refreshed, tre  # type: ignore[return-value]


def delete_alocacao(db: Session, alocacao: Alocacao) -> None:
    if alocacao.ativa:
        raise ValueError('Não é possível excluir entrega ativa; registre a devolução')
    if alocacao.tre_id:
        raise ValueError('Não é possível excluir alocação com TRE vinculado')
    db.delete(alocacao)
    db.commit()
