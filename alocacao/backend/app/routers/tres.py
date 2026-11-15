from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import tres as repo
from app.schemas.tre import TreItemOut, TreOut

router = APIRouter(prefix='/tres', tags=['tres'])


def _to_out(tre) -> TreOut:
    return TreOut(
        id=tre.id,
        codigo=tre.codigo,
        tipo=tre.tipo,  # type: ignore[arg-type]
        colaborador_id=tre.colaborador_id,
        colaborador_nome=tre.colaborador.nome if tre.colaborador else '',
        created_at=tre.created_at,
        itens=[
            TreItemOut(
                id=item.id,
                equipamento_id=item.equipamento_id,
                quantidade=item.quantidade,
                categoria_nome=item.categoria_nome,
                descricao=item.descricao,
                numero_patrimonio=item.numero_patrimonio,
            )
            for item in (tre.itens or [])
        ],
    )


@router.get('', response_model=list[TreOut])
def listar(
    nome: str | None = Query(default=None),
    codigo: str | None = Query(default=None),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TreOut]:
    return [_to_out(item) for item in repo.list_tres(
        db,
        nome=nome,
        codigo=codigo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )]


@router.get('/{tre_id}', response_model=TreOut)
def obter(tre_id: int, db: Session = Depends(get_db)) -> TreOut:
    tre = repo.get_tre(db, tre_id)
    if not tre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='TRE não encontrado')
    return _to_out(tre)


@router.get('/{tre_id}/pdf')
def baixar_pdf(tre_id: int, db: Session = Depends(get_db)) -> FileResponse:
    tre = repo.get_tre(db, tre_id)
    if not tre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='TRE não encontrado')
    path = Path(tre.pdf_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Arquivo PDF não encontrado')
    filename = f'TRE-{tre.codigo}-{tre.tipo}.pdf'
    return FileResponse(path, media_type='application/pdf', filename=filename)
