from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.seed import seed_categorias
from app.db.session import Base, SessionLocal, engine
from app.models import Categoria, Colaborador, Fornecedor  # noqa: F401
from app.routers import categorias, colaboradores, fornecedores

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.database_url.startswith('sqlite:///'):
        db_path = Path(settings.database_url.replace('sqlite:///', '', 1))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_categorias(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version='0.1.0', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins or ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(categorias.router, prefix=settings.api_prefix)
app.include_router(colaboradores.router, prefix=settings.api_prefix)
app.include_router(fornecedores.router, prefix=settings.api_prefix)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'alocacao-recursos'}


@app.get(f'{settings.api_prefix}/meta')
def meta() -> dict[str, object]:
    return {
        'name': settings.app_name,
        'modules': [
            'cadastros',
            'configuracoes',
            'notas-fiscais',
            'tres',
            'alocacoes',
            'equipamentos',
        ],
        'auth': {
            'provider': 'microsoft-entra-id',
            'tenant_configured': bool(settings.azure_tenant_id),
            'client_configured': bool(settings.azure_client_id),
        },
    }


@app.get(f'{settings.api_prefix}/dashboard/summary')
def dashboard_summary() -> dict[str, object]:
    """Resumo inicial do estoque (dados mock até persistência completa)."""
    return {
        'disponiveis': 48,
        'alocados': 23,
        'em_manutencao': 4,
        'aguardando_tre': 6,
    }
