from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.produto import Produto
from app.repositories import equipamentos as repo
from app.schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoOut,
    EquipamentoUpdate,
    StatusEquipamento,
)

router = APIRouter(prefix='/equipamentos', tags=['equipamentos'])


def _to_out(db: Session, equipamento) -> EquipamentoOut:
    produto = equipamento.produto
    categoria = produto.categoria if produto else None
    return EquipamentoOut(
        id=equipamento.id,
        codigo=equipamento.codigo,
        produto_id=equipamento.produto_id,
        numero_serie=equipamento.numero_serie,
        numero_patrimonio=equipamento.numero_patrimonio,
        mac_address=equipamento.mac_address,
        status=repo.equipamento_status(db, equipamento.id),
        produto_codigo=produto.codigo if produto else '',
        produto_descricao=produto.descricao if produto else '',
        marca=produto.marca if produto else '',
        modelo=produto.modelo if produto else '',
        categoria_id=produto.categoria_id if produto else 0,
        categoria_nome=categoria.nome if categoria else '',
        created_at=equipamento.created_at,
        updated_at=equipamento.updated_at,
    )


@router.get('', response_model=list[EquipamentoOut])
def listar(
    categoria_id: int | None = Query(default=None),
    status_filtro: StatusEquipamento | None = Query(default=None, alias='status'),
    db: Session = Depends(get_db),
) -> list[EquipamentoOut]:
    items = repo.list_equipamentos(db, categoria_id=categoria_id, status=status_filtro)
    return [_to_out(db, item) for item in items]


@router.get('/{equipamento_id}', response_model=EquipamentoOut)
def obter(equipamento_id: int, db: Session = Depends(get_db)) -> EquipamentoOut:
    equipamento = repo.get_equipamento(db, equipamento_id)
    if not equipamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Equipamento não encontrado')
    return _to_out(db, equipamento)


@router.post('', response_model=EquipamentoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: EquipamentoCreate, db: Session = Depends(get_db)) -> EquipamentoOut:
    if not db.get(Produto, payload.produto_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Produto inválido')
    if repo.get_by_patrimonio(db, payload.numero_patrimonio):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Já existe equipamento com este número de patrimônio',
        )
    equipamento = repo.create_equipamento(db, payload)
    return _to_out(db, equipamento)


@router.put('/{equipamento_id}', response_model=EquipamentoOut)
def atualizar(
    equipamento_id: int,
    payload: EquipamentoUpdate,
    db: Session = Depends(get_db),
) -> EquipamentoOut:
    equipamento = repo.get_equipamento(db, equipamento_id)
    if not equipamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Equipamento não encontrado')
    if payload.produto_id is not None and not db.get(Produto, payload.produto_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Produto inválido')
    if payload.numero_patrimonio:
        other = repo.get_by_patrimonio(db, payload.numero_patrimonio)
        if other and other.id != equipamento_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Já existe equipamento com este número de patrimônio',
            )
    updated = repo.update_equipamento(db, equipamento, payload)
    return _to_out(db, updated)


@router.delete('/{equipamento_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(equipamento_id: int, db: Session = Depends(get_db)) -> None:
    equipamento = repo.get_equipamento(db, equipamento_id)
    if not equipamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Equipamento não encontrado')
    if repo.has_alocacao_ativa(db, equipamento_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Não é possível excluir equipamento com alocação ativa',
        )
    repo.delete_equipamento(db, equipamento)
