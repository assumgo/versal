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
a rota de saúde não acessa o banco. As tabelas são criadas explicitamente com Alembic.

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

Os testes usam uma chave exclusiva de teste. Sem `TEST_DATABASE_URL`, os testes de
integração PostgreSQL são pulados; configuração, saúde e metadados continuam verificáveis.

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

## Banco de dados e migrações

A migração `0001` cria as 13 tabelas da fundação. Não há criação automática de
esquema ao iniciar a API. Após configurar o ambiente, execute na pasta `web/`:

```bash
docker compose build backend
docker compose run --rm backend python -m alembic upgrade head
docker compose run --rm backend python -m alembic current
```

Sem Docker, na pasta `web/backend/`, com `DATABASE_URL` e `JWT_SECRET_KEY`
configurados no ambiente ou no `.env`:

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic check
```

Os identificadores são UUID, timestamps usam timezone e valores monetários são
`NUMERIC(18,2)`/`Decimal`. Competências usam o primeiro dia do mês (`2026-10-01`).
As chaves estrangeiras preservam histórico por `RESTRICT`; empresas e colaboradores
possuem `is_active` para a futura inativação. Referências de folha e arquivos de
importação devem pertencer à mesma empresa. CPF/CNPJ serão validados pelos serviços
na etapa de cadastros; nesta etapa são armazenados sem pontuação.

A migração é estática e reversível. `downgrade base` remove as tabelas e seus dados;
use essa reversão somente em ambientes descartáveis.

Para verificar migração, reversão, reaplicação e todos os testes contra PostgreSQL
16 descartável, sem alterar o banco da aplicação, execute na raiz do repositório
(com Docker disponível e a `.venv` do backend preparada):

```bash
bash web/backend/tests/run_postgres.sh
```

O script usa porta local dinâmica e armazenamento temporário, removendo o container
ao terminar. Para outro Python, defina `PYTHON_BIN` com caminho absoluto.
Também é possível testar contra um banco de testes já migrado com
`TEST_DATABASE_URL=postgresql+psycopg://... .venv/bin/python -m pytest -q`.
Cada teste de integração desfaz suas alterações em uma transação; nunca use o
banco operacional como banco de testes. O gerador `get_db()` encerra a sessão e
reverte alterações não confirmadas; os futuros serviços serão responsáveis por
confirmar explicitamente as transações.

## Próximas etapas

Autenticação, autorização por empresa,
cadastros e interface operacional seguem o plano em
`../docs/superpowers/plans/2026-10-15-versal-folha-web-phase-1.md`.
Os modelos e a migração inicial estão implementados. Login e importação/exportação
TXT seguem nas próximas etapas.
