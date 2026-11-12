from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins or ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


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
    """Resumo inicial do estoque (dados mock até persistência)."""
    return {
        'disponiveis': 48,
        'alocados': 23,
        'em_manutencao': 4,
        'aguardando_tre': 6,
    }
