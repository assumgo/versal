from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import locais as repo
from app.schemas.local import LocalCreate, LocalOut, LocalUpdate

router = APIRouter(prefix='/locais', tags=['locais'])


@router.get('', response_model=list[LocalOut])
def listar(q: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[LocalOut]:
    return [LocalOut.model_validate(item) for item in repo.list_locais(db, q=q)]


@router.get('/{local_id}', response_model=LocalOut)
def obter(local_id: int, db: Session = Depends(get_db)) -> LocalOut:
    local = repo.get_local(db, local_id)
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Local não encontrado')
    return LocalOut.model_validate(local)


@router.post('', response_model=LocalOut, status_code=status.HTTP_201_CREATED)
def criar(payload: LocalCreate, db: Session = Depends(get_db)) -> LocalOut:
    return LocalOut.model_validate(repo.create_local(db, payload))


@router.put('/{local_id}', response_model=LocalOut)
def atualizar(local_id: int, payload: LocalUpdate, db: Session = Depends(get_db)) -> LocalOut:
    local = repo.get_local(db, local_id)
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Local não encontrado')
    return LocalOut.model_validate(repo.update_local(db, local, payload))


@router.delete('/{local_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(local_id: int, db: Session = Depends(get_db)) -> None:
    local = repo.get_local(db, local_id)
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Local não encontrado')
    if repo.count_alocacoes(db, local_id) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Não é possível excluir local com alocações vinculadas',
        )
    repo.delete_local(db, local)
