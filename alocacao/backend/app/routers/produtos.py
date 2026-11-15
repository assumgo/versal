from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.categoria import Categoria
from app.repositories import produtos as repo
from app.schemas.produto import ProdutoCreate, ProdutoOut, ProdutoUpdate

router = APIRouter(prefix='/produtos', tags=['produtos'])


def _to_out(produto) -> ProdutoOut:
    return ProdutoOut(
        id=produto.id,
        codigo=produto.codigo,
        descricao=produto.descricao,
        marca=produto.marca,
        modelo=produto.modelo,
        categoria_id=produto.categoria_id,
        categoria_nome=produto.categoria.nome if produto.categoria else '',
        created_at=produto.created_at,
        updated_at=produto.updated_at,
    )


@router.get('', response_model=list[ProdutoOut])
def listar(db: Session = Depends(get_db)) -> list[ProdutoOut]:
    return [_to_out(item) for item in repo.list_produtos(db)]


@router.get('/{produto_id}', response_model=ProdutoOut)
def obter(produto_id: int, db: Session = Depends(get_db)) -> ProdutoOut:
    produto = repo.get_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Produto não encontrado')
    return _to_out(produto)


@router.post('', response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ProdutoCreate, db: Session = Depends(get_db)) -> ProdutoOut:
    if not db.get(Categoria, payload.categoria_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Categoria inválida')
    return _to_out(repo.create_produto(db, payload))


@router.put('/{produto_id}', response_model=ProdutoOut)
def atualizar(produto_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db)) -> ProdutoOut:
    produto = repo.get_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Produto não encontrado')
    if payload.categoria_id is not None and not db.get(Categoria, payload.categoria_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Categoria inválida')
    return _to_out(repo.update_produto(db, produto, payload))


@router.delete('/{produto_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(produto_id: int, db: Session = Depends(get_db)) -> None:
    produto = repo.get_produto(db, produto_id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Produto não encontrado')
    if repo.count_equipamentos(db, produto_id) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Não é possível excluir produto com equipamentos vinculados',
        )
    repo.delete_produto(db, produto)
