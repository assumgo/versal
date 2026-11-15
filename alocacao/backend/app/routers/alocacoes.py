from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import alocacoes as repo
from app.schemas.alocacao import AlocacaoCreate, AlocacaoOut

router = APIRouter(prefix='/alocacoes', tags=['alocacoes'])


def _to_out(db: Session, alocacao) -> AlocacaoOut:
    equipamento = alocacao.equipamento
    produto = equipamento.produto if equipamento else None
    colaborador = alocacao.colaborador
    local = alocacao.local
    produto_id = produto.id if produto else 0
    destino_nome = ''
    if alocacao.destino_tipo == 'colaborador':
        destino_nome = colaborador.nome if colaborador else ''
    else:
        destino_nome = local.nome if local else ''
    tre_codigo = ''
    if alocacao.tre_id:
        from app.repositories import tres as tres_repo

        tre = tres_repo.get_tre(db, alocacao.tre_id)
        tre_codigo = tre.codigo if tre else ''
    return AlocacaoOut(
        id=alocacao.id,
        codigo=alocacao.codigo,
        tipo=alocacao.tipo,
        destino_tipo=alocacao.destino_tipo,
        equipamento_id=alocacao.equipamento_id,
        equipamento_codigo=equipamento.codigo if equipamento else '',
        produto_id=produto_id,
        produto_codigo=produto.codigo if produto else '',
        produto_descricao=produto.descricao if produto else '',
        numero_patrimonio=equipamento.numero_patrimonio if equipamento else '',
        quantidade=alocacao.quantidade,
        colaborador_id=alocacao.colaborador_id,
        colaborador_nome=colaborador.nome if colaborador else '',
        local_id=alocacao.local_id,
        local_nome=local.nome if local else '',
        destino_nome=destino_nome,
        tre_id=alocacao.tre_id,
        tre_codigo=tre_codigo,
        referencia_id=alocacao.referencia_id,
        data_previsao=alocacao.data_previsao,
        ativa=alocacao.ativa,
        estoque_disponivel_produto=repo.estoque_disponivel_produto(db, produto_id) if produto_id else 0,
        created_at=alocacao.created_at,
        updated_at=alocacao.updated_at,
    )


@router.get('', response_model=list[AlocacaoOut])
def listar(
    ativa: bool | None = Query(default=None),
    tipo: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AlocacaoOut]:
    return [_to_out(db, item) for item in repo.list_alocacoes(db, ativa=ativa, tipo=tipo, q=q)]


@router.get('/{alocacao_id}', response_model=AlocacaoOut)
def obter(alocacao_id: int, db: Session = Depends(get_db)) -> AlocacaoOut:
    alocacao = repo.get_alocacao(db, alocacao_id)
    if not alocacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Alocação não encontrada')
    return _to_out(db, alocacao)


@router.post('', response_model=AlocacaoOut, status_code=status.HTTP_201_CREATED)
def criar(payload: AlocacaoCreate, db: Session = Depends(get_db)) -> AlocacaoOut:
    try:
        alocacao, _tre = repo.criar_movimento(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_out(db, alocacao)


@router.delete('/{alocacao_id}', status_code=status.HTTP_204_NO_CONTENT)
def excluir(alocacao_id: int, db: Session = Depends(get_db)) -> None:
    alocacao = repo.get_alocacao(db, alocacao_id)
    if not alocacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Alocação não encontrada')
    try:
        repo.delete_alocacao(db, alocacao)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
