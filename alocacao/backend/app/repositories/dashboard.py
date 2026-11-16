"""Agregados do painel de estoque."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.seed import DEFAULT_CATEGORIAS
from app.models.alocacao import Alocacao
from app.models.categoria import Categoria
from app.models.equipamento import Equipamento
from app.models.produto import Produto

DESTINO_MANUTENCAO = 'manutencao'
# Notebook, Monitor, Periféricos, Rede, Desktop, Servidor, depois demais A→Z
CATEGORIA_ORDEM = {item['nome']: index for index, item in enumerate(DEFAULT_CATEGORIAS)}


def _ativa_por_equipamento(db: Session) -> dict[int, Alocacao]:
    rows = db.scalars(
        select(Alocacao).where(Alocacao.ativa.is_(True), Alocacao.tipo == 'entrega')
    ).all()
    return {row.equipamento_id: row for row in rows}


def _ordenar_categorias(categorias: list[Categoria]) -> list[Categoria]:
    return sorted(
        categorias,
        key=lambda item: (CATEGORIA_ORDEM.get(item.nome, len(CATEGORIA_ORDEM)), item.nome.casefold()),
    )


def build_dashboard_summary(db: Session) -> dict[str, object]:
    categorias = _ordenar_categorias(
        list(db.scalars(select(Categoria).where(Categoria.ativo.is_(True))).all())
    )
    equipamentos = list(
        db.scalars(
            select(Equipamento)
            .options(joinedload(Equipamento.produto).joinedload(Produto.categoria))
            .order_by(Equipamento.codigo.asc())
        )
        .unique()
        .all()
    )
    ativas = _ativa_por_equipamento(db)

    per_cat: dict[int, dict[str, int]] = defaultdict(
        lambda: {'disponiveis': 0, 'alocados': 0, 'em_manutencao': 0}
    )
    # Categorias sem equipamentos ainda aparecem com zero
    for categoria in categorias:
        _ = per_cat[categoria.id]

    disponiveis = 0
    alocados = 0
    em_manutencao = 0

    for equipamento in equipamentos:
        categoria_id = equipamento.produto.categoria_id if equipamento.produto else None
        ativa = ativas.get(equipamento.id)
        if ativa is None:
            disponiveis += 1
            if categoria_id is not None:
                per_cat[categoria_id]['disponiveis'] += 1
            continue
        if ativa.destino_tipo == DESTINO_MANUTENCAO:
            em_manutencao += 1
            if categoria_id is not None:
                per_cat[categoria_id]['em_manutencao'] += 1
        else:
            alocados += 1
            if categoria_id is not None:
                per_cat[categoria_id]['alocados'] += 1

    total_recursos = disponiveis + alocados
    category_rows = []
    for categoria in categorias:
        counts = per_cat[categoria.id]
        cat_disponiveis = counts['disponiveis']
        cat_alocados = counts['alocados']
        cat_manutencao = counts['em_manutencao']
        category_rows.append(
            {
                'id': categoria.id,
                'nome': categoria.nome,
                'disponiveis': cat_disponiveis,
                'alocados': cat_alocados,
                'em_manutencao': cat_manutencao,
                'total': cat_disponiveis + cat_alocados,
            }
        )

    return {
        'disponiveis': disponiveis,
        'alocados': alocados,
        'em_manutencao': em_manutencao,
        'total_recursos': total_recursos,
        'categorias': category_rows,
    }
