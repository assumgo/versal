from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import categorias as repo
from app.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate

router = APIRouter(prefix='/categorias', tags=['categorias'])


@router.get('', response_model=list[CategoriaOut])
def listar(
    ativo: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CategoriaOut]:
    return repo.list_categorias(db, apenas_ativos=ativo)


@router.get('/{categoria_id}', response_model=CategoriaOut)
def obter(categoria_id: int, db: Session = Depends(get_db)) -> CategoriaOut:
    categoria = repo.get_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Categoria não encontrada')
    return categoria


@router.post('', response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar(payload: CategoriaCreate, db: Session = Depends(get_db)) -> CategoriaOut:
    if repo.get_by_nome(db, payload.nome):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe categoria com este nome')
    return repo.create_categoria(db, payload)


@router.put('/{categoria_id}', response_model=CategoriaOut)
def atualizar(
    categoria_id: int,
    payload: CategoriaUpdate,
    db: Session = Depends(get_db),
) -> CategoriaOut:
    categoria = repo.get_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Categoria não encontrada')
    if payload.nome:
        other = repo.get_by_nome(db, payload.nome)
        if other and other.id != categoria_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe categoria com este nome')
    return repo.update_categoria(db, categoria, payload)


@router.delete('/{categoria_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(categoria_id: int, db: Session = Depends(get_db)) -> None:
    categoria = repo.get_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Categoria não encontrada')
    repo.delete_categoria(db, categoria)
