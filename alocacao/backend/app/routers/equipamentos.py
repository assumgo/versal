from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.categoria import Categoria
from app.repositories import equipamentos as repo
from app.schemas.equipamento import (
    EquipamentoCreate,
    EquipamentoOut,
    EquipamentoUpdate,
    StatusEquipamento,
)

router = APIRouter(prefix='/equipamentos', tags=['equipamentos'])


def _to_out(db: Session, equipamento) -> EquipamentoOut:
    return EquipamentoOut(
        id=equipamento.id,
        descricao=equipamento.descricao,
        marca=equipamento.marca,
        modelo=equipamento.modelo,
        numero_serie=equipamento.numero_serie,
        numero_patrimonio=equipamento.numero_patrimonio,
        mac_address=equipamento.mac_address,
        categoria_id=equipamento.categoria_id,
        categoria_nome=equipamento.categoria.nome if equipamento.categoria else '',
        status=repo.equipamento_status(db, equipamento.id),
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
    if not db.get(Categoria, payload.categoria_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Categoria inválida')
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
    if payload.categoria_id is not None and not db.get(Categoria, payload.categoria_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Categoria inválida')
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
