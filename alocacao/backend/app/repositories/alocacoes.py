from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.alocacao import Alocacao
from app.models.colaborador import Colaborador
from app.models.equipamento import Equipamento
from app.models.produto import Produto
from app.repositories import equipamentos as equipamentos_repo
from app.repositories import tres as tres_repo


def list_alocacoes(db: Session, *, ativa: bool | None = True) -> list[Alocacao]:
    query = (
        select(Alocacao)
        .options(
            joinedload(Alocacao.colaborador),
            joinedload(Alocacao.equipamento).joinedload(Equipamento.produto).joinedload(Produto.categoria),
        )
        .order_by(Alocacao.id.desc())
    )
    if ativa is not None:
        query = query.where(Alocacao.ativa.is_(ativa))
    return list(db.scalars(query).unique().all())


def get_alocacao(db: Session, alocacao_id: int) -> Alocacao | None:
    return db.scalars(
        select(Alocacao)
        .options(
            joinedload(Alocacao.colaborador),
            joinedload(Alocacao.equipamento).joinedload(Equipamento.produto).joinedload(Produto.categoria),
        )
        .where(Alocacao.id == alocacao_id)
    ).unique().first()


def _item_snapshot(equipamento: Equipamento) -> dict:
    produto = equipamento.produto
    categoria = produto.categoria if produto else None
    descricao_parts = [p for p in [produto.marca if produto else '', produto.modelo if produto else ''] if p]
    return {
        'equipamento_id': equipamento.id,
        'categoria_nome': categoria.nome if categoria else (produto.descricao if produto else 'Equipamento'),
        'descricao': ' '.join(descricao_parts) or (produto.descricao if produto else ''),
        'numero_patrimonio': equipamento.numero_patrimonio,
        'quantidade': 1,
    }


def criar_alocacao(db: Session, colaborador_id: int, equipamento_ids: list[int]) -> tuple[list[Alocacao], object]:
    colaborador = db.get(Colaborador, colaborador_id)
    if not colaborador:
        raise ValueError('Colaborador inválido')
    if not colaborador.ativo:
        raise ValueError('Colaborador inativo')

    unique_ids = list(dict.fromkeys(equipamento_ids))
    equipamentos: list[Equipamento] = []
    for equipamento_id in unique_ids:
        equipamento = equipamentos_repo.get_equipamento(db, equipamento_id)
        if not equipamento:
            raise ValueError(f'Equipamento {equipamento_id} não encontrado')
        if equipamentos_repo.has_alocacao_ativa(db, equipamento_id):
            raise ValueError(f'Equipamento {equipamento.codigo} já está alocado')
        equipamentos.append(equipamento)

    alocacoes: list[Alocacao] = []
    for equipamento in equipamentos:
        alocacao = Alocacao(
            equipamento_id=equipamento.id,
            colaborador_id=colaborador.id,
            ativa=True,
        )
        db.add(alocacao)
        alocacoes.append(alocacao)
    db.flush()

    itens = []
    for alocacao, equipamento in zip(alocacoes, equipamentos, strict=True):
        snap = _item_snapshot(equipamento)
        snap['alocacao_id'] = alocacao.id
        itens.append(snap)

    tre = tres_repo.create_tre_with_pdf(db, tipo='entrega', colaborador=colaborador, itens=itens)
    for alocacao in alocacoes:
        alocacao.tre_entrega_id = tre.id
        db.add(alocacao)
    db.commit()

    refreshed = [get_alocacao(db, item.id) for item in alocacoes]
    return [item for item in refreshed if item], tre


def devolver_alocacoes(db: Session, alocacao_ids: list[int]) -> tuple[list[Alocacao], object]:
    unique_ids = list(dict.fromkeys(alocacao_ids))
    alocacoes: list[Alocacao] = []
    for alocacao_id in unique_ids:
        alocacao = get_alocacao(db, alocacao_id)
        if not alocacao:
            raise ValueError(f'Alocação {alocacao_id} não encontrada')
        if not alocacao.ativa:
            raise ValueError(f'Alocação {alocacao_id} já está encerrada')
        if not alocacao.colaborador_id:
            raise ValueError(f'Alocação {alocacao_id} sem colaborador')
        alocacoes.append(alocacao)

    colaborador_ids = {item.colaborador_id for item in alocacoes}
    if len(colaborador_ids) != 1:
        raise ValueError('Selecione alocações do mesmo colaborador')

    colaborador = db.get(Colaborador, alocacoes[0].colaborador_id)
    if not colaborador:
        raise ValueError('Colaborador inválido')

    itens = []
    for alocacao in alocacoes:
        equipamento = alocacao.equipamento or equipamentos_repo.get_equipamento(db, alocacao.equipamento_id)
        if not equipamento:
            raise ValueError('Equipamento da alocação não encontrado')
        snap = _item_snapshot(equipamento)
        snap['alocacao_id'] = alocacao.id
        itens.append(snap)

    tre = tres_repo.create_tre_with_pdf(db, tipo='devolucao', colaborador=colaborador, itens=itens)
    for alocacao in alocacoes:
        alocacao.ativa = False
        alocacao.tre_devolucao_id = tre.id
        db.add(alocacao)
    db.commit()

    refreshed = [get_alocacao(db, item.id) for item in alocacoes]
    return [item for item in refreshed if item], tre
