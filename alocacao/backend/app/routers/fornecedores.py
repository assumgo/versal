from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import fornecedores as repo
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate

router = APIRouter(prefix='/fornecedores', tags=['fornecedores'])


@router.get('', response_model=list[FornecedorOut])
def listar(db: Session = Depends(get_db)) -> list[FornecedorOut]:
    return repo.list_fornecedores(db)


@router.get('/{fornecedor_id}', response_model=FornecedorOut)
def obter(fornecedor_id: int, db: Session = Depends(get_db)) -> FornecedorOut:
    fornecedor = repo.get_fornecedor(db, fornecedor_id)
    if not fornecedor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Fornecedor não encontrado')
    return fornecedor


@router.post('', response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
def criar(payload: FornecedorCreate, db: Session = Depends(get_db)) -> FornecedorOut:
    if repo.get_by_documento(db, payload.documento):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe fornecedor com este CNPJ/CPF')
    return repo.create_fornecedor(db, payload)


@router.put('/{fornecedor_id}', response_model=FornecedorOut)
def atualizar(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    db: Session = Depends(get_db),
) -> FornecedorOut:
    fornecedor = repo.get_fornecedor(db, fornecedor_id)
    if not fornecedor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Fornecedor não encontrado')
    if payload.documento:
        other = repo.get_by_documento(db, payload.documento)
        if other and other.id != fornecedor_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Já existe fornecedor com este CNPJ/CPF')
    return repo.update_fornecedor(db, fornecedor, payload)


@router.delete('/{fornecedor_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(fornecedor_id: int, db: Session = Depends(get_db)) -> None:
    fornecedor = repo.get_fornecedor(db, fornecedor_id)
    if not fornecedor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Fornecedor não encontrado')
    repo.delete_fornecedor(db, fornecedor)
