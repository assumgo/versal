from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import colaboradores as repo
from app.schemas.colaborador import ColaboradorCreate, ColaboradorOut, ColaboradorUpdate

router = APIRouter(prefix='/colaboradores', tags=['colaboradores'])


@router.get('', response_model=list[ColaboradorOut])
def listar(db: Session = Depends(get_db)) -> list[ColaboradorOut]:
    return repo.list_colaboradores(db)


@router.get('/{colaborador_id}', response_model=ColaboradorOut)
def obter(colaborador_id: int, db: Session = Depends(get_db)) -> ColaboradorOut:
    colaborador = repo.get_colaborador(db, colaborador_id)
    if not colaborador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Colaborador não encontrado')
    return colaborador


@router.post('', response_model=ColaboradorOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ColaboradorCreate, db: Session = Depends(get_db)) -> ColaboradorOut:
    if repo.get_by_cpf(db, payload.cpf):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe colaborador com este CPF')
    if repo.get_by_email(db, str(payload.email_pessoal)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe colaborador com este e-mail')
    return repo.create_colaborador(db, payload)


@router.put('/{colaborador_id}', response_model=ColaboradorOut)
def atualizar(
    colaborador_id: int,
    payload: ColaboradorUpdate,
    db: Session = Depends(get_db),
) -> ColaboradorOut:
    colaborador = repo.get_colaborador(db, colaborador_id)
    if not colaborador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Colaborador não encontrado')
    if payload.cpf:
        other = repo.get_by_cpf(db, payload.cpf)
        if other and other.id != colaborador_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe colaborador com este CPF')
    if payload.email_pessoal:
        other = repo.get_by_email(db, str(payload.email_pessoal))
        if other and other.id != colaborador_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe colaborador com este e-mail')
    return repo.update_colaborador(db, colaborador, payload)


@router.delete('/{colaborador_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(colaborador_id: int, db: Session = Depends(get_db)) -> None:
    colaborador = repo.get_colaborador(db, colaborador_id)
    if not colaborador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Colaborador não encontrado')
    repo.delete_colaborador(db, colaborador)
