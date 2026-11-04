# Agenda de salas

Reserva de salas de reunião, com banco e autenticação próprios. A paleta segue o Versal Folha (`#315f2f`, `#89bf21`, fundo `#f7faf5`).

Requisitos: Docker Engine com Compose v2. Sem containers: Python 3.12+, Node.js 24 e PostgreSQL 16.

## Executar com Docker

Na pasta `agenda_sala_reuniao/`:

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Preencha `POSTGRES_PASSWORD` e `JWT_SECRET_KEY` em `.env` com valores diferentes. A senha do banco entra na URL do PostgreSQL; prefira o hexadecimal gerado acima. Não versione `.env`.

```bash
docker compose up --build -d --wait --wait-timeout 180
bash tests/smoke_compose.sh
```

Frontend: http://localhost:5174. API: http://localhost:8010. OpenAPI: http://localhost:8010/docs.
O health check responde `{"status":"ok"}` e não acessa o banco. As portas padrão (8010 e 5174) convivem com o Folha em 8000 e 5173.

Nenhuma conta é criada na subida. Com a stack no ar, crie o primeiro administrador só em desenvolvimento:

```bash
docker compose exec -e FIRST_ADMIN_NAME='Ada' -e FIRST_ADMIN_EMAIL='ada@example.com' -e FIRST_ADMIN_PASSWORD='uma-senha-de-12+' backend python -m app.scripts.seed_admin
```

O comando exige `ENVIRONMENT=development`, recusa se já existir outro usuário e, se o mesmo administrador já estiver ativo, preserva a senha. A senha fica só na variável de ambiente desta execução.

O administrador cadastra salas e contas. Qualquer usuário ativo reserva uma sala e cancela as próprias reservas. O administrador também cancela reservas de outras pessoas. Dois horários na mesma sala não podem se sobrepor; um pode começar no instante em que o outro termina. Os horários da tela usam America/Sao_Paulo, no formato de 24 horas. Depois do login, a aplicação abre o painel com as reservas do dia, da semana e do mês.

```bash
docker compose logs -f
docker compose down
```

O volume `postgres_data` preserva os dados. Trocar `POSTGRES_PASSWORD` depois da primeira subida não altera a senha do banco já criado.

## Backend sem Docker

Na pasta `agenda_sala_reuniao/backend/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Defina `JWT_SECRET_KEY` com pelo menos 32 caracteres e `DATABASE_URL` apontando para um PostgreSQL descartável. Aplique as migrações e suba a API:

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Os testes de conflito usam PostgreSQL de verdade, porque o bloqueio é uma restrição `EXCLUDE` com `btree_gist`. Sem `TEST_DATABASE_URL`, esses testes são pulados; saúde e configuração continuam verificáveis.

```bash
TEST_DATABASE_URL='postgresql+psycopg://agenda:agenda@127.0.0.1:5432/agenda_sala_test' \
  .venv/bin/python -m pytest -q
```

Não aponte `TEST_DATABASE_URL` para o banco operacional.

## Frontend sem Docker

Na pasta `agenda_sala_reuniao/frontend/`:

```bash
npm ci
npm test
npm run dev
```

O Vite publica http://localhost:5174. `VITE_API_BASE_URL` aponta para a API; o valor padrão é `http://localhost:8010/api/v1`.
