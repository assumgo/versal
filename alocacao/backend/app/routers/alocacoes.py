from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import alocacoes as repo
from app.schemas.alocacao import AlocacaoCreate, AlocacaoCreateResult, AlocacaoDevolver, AlocacaoOut

router = APIRouter(prefix='/alocacoes', tags=['alocacoes'])


def _to_out(alocacao) -> AlocacaoOut:
    equipamento = alocacao.equipamento
    produto = equipamento.produto if equipamento else None
    colaborador = alocacao.colaborador
    return AlocacaoOut(
        id=alocacao.id,
        equipamento_id=alocacao.equipamento_id,
        equipamento_codigo=equipamento.codigo if equipamento else '',
        produto_codigo=produto.codigo if produto else '',
        produto_descricao=produto.descricao if produto else '',
        numero_patrimonio=equipamento.numero_patrimonio if equipamento else '',
        colaborador_id=alocacao.colaborador_id,
        colaborador_nome=colaborador.nome if colaborador else '',
        ativa=alocacao.ativa,
        tre_entrega_id=alocacao.tre_entrega_id,
        tre_devolucao_id=alocacao.tre_devolucao_id,
        created_at=alocacao.created_at,
        updated_at=alocacao.updated_at,
    )


@router.get('', response_model=list[AlocacaoOut])
def listar(
    ativa: bool | None = Query(default=True),
    db: Session = Depends(get_db),
) -> list[AlocacaoOut]:
    return [_to_out(item) for item in repo.list_alocacoes(db, ativa=ativa)]


@router.post('', response_model=AlocacaoCreateResult, status_code=status.HTTP_201_CREATED)
def criar(payload: AlocacaoCreate, db: Session = Depends(get_db)) -> AlocacaoCreateResult:
    try:
        alocacoes, tre = repo.criar_alocacao(db, payload.colaborador_id, payload.equipamento_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AlocacaoCreateResult(
        alocacoes=[_to_out(item) for item in alocacoes],
        tre_id=tre.id,
        tre_codigo=tre.codigo,
        tre_tipo=tre.tipo,
    )


@router.post('/devolver', response_model=AlocacaoCreateResult)
def devolver(payload: AlocacaoDevolver, db: Session = Depends(get_db)) -> AlocacaoCreateResult:
    try:
        alocacoes, tre = repo.devolver_alocacoes(db, payload.alocacao_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AlocacaoCreateResult(
        alocacoes=[_to_out(item) for item in alocacoes],
        tre_id=tre.id,
        tre_codigo=tre.codigo,
        tre_tipo=tre.tipo,
    )
