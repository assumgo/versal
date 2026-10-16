# Versal Folha TXT Web

Fundação da fase 1: API FastAPI, base React/TypeScript/Vite e PostgreSQL.
Requisitos: Docker Engine com Compose v2; para execução sem containers,
Python 3.12+ com `venv` e Node.js 24 com npm.

## Executar com Docker

Na pasta `web/`:

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Preencha `POSTGRES_PASSWORD` e `JWT_SECRET_KEY` em `.env` com valores diferentes,
gerados pelo comando acima. Use a senha hexadecimal sugerida: caracteres especiais
em senhas exigem codificação na URL do PostgreSQL. Não versione `.env`.

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/health
```

Frontend: http://localhost:5173. API: http://localhost:8000.
Documentação OpenAPI: http://localhost:8000/docs.
O health check retorna `{"status":"ok"}` e verifica apenas a disponibilidade HTTP;
nesta etapa a API ainda não acessa o banco.

```bash
docker compose logs -f
docker compose down
```

O volume `postgres_data` preserva os dados ao parar a stack. Alterar a senha em
`.env` depois da primeira inicialização não altera a senha do banco já criado.
Este Compose serve ao desenvolvimento local; o frontend usa o servidor do Vite.

## Backend sem Docker

Na pasta `web/backend/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Em Debian/Ubuntu, o comando `venv` requer o pacote `python3.12-venv`.
Preencha `JWT_SECRET_KEY` com pelo menos 32 caracteres e `DATABASE_URL` com a URL
do PostgreSQL disponível no seu ambiente. O Compose não publica a porta do banco.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Os testes usam uma chave exclusiva de teste e não precisam de banco nesta etapa.

## Frontend sem Docker

Na pasta `web/frontend/`:

```bash
cp .env.example .env
npm ci
npm run dev
```

Para verificar TypeScript e gerar os arquivos estáticos:

```bash
npm run build
```

`VITE_API_BASE_URL` reserva a configuração da futura integração com a API; a
página inicial ainda não faz requisições. Variáveis `VITE_*` são públicas e não
devem conter segredos.

## Próximas etapas

Modelos SQLAlchemy e migrações Alembic, autenticação, autorização por empresa,
cadastros e interface operacional seguem o plano em
`../docs/superpowers/plans/2026-10-15-versal-folha-web-phase-1.md`.
Ainda não há tabelas, login, migrações ou importação/exportação TXT.
