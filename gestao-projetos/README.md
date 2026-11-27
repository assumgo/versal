# Gestão de projetos

App separado da folha de pagamento. Acompanha um projeto da criação à conclusão, com portfólio, fases e tarefas. O progresso e a saúde são calculados. Cada indicador abre o detalhe correspondente.

## Primeira versão

- Projeto, fases e tarefas, com responsável, prazo e motivo de bloqueio.
- Portfólio com ativos, no prazo, em atenção e atrasados.
- Modelos Montagem de rack e Sistema, além de projeto em branco.
- Rascunho pode ser apagado. Nos demais status, o encerramento é concluir ou cancelar.
- Concluir com tarefas abertas pede confirmação.

Datas de saúde usam o calendário de `America/Sao_Paulo`.

## Subir localmente

Na pasta `gestao-projetos`:

```bash
cp .env.example .env
cp .env backend/.env
docker compose up db -d
```

API, a partir de `gestao-projetos/backend`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload --port 8010
```

Interface, a partir de `gestao-projetos/frontend`:

```bash
npm ci
npm run dev
```

A interface fica em `http://localhost:5174` e a API em `http://127.0.0.1:8010`. O primeiro boot cria a pessoa definida por `SEED_USER_EMAIL` quando o banco ainda não tem esse e-mail. Troque a senha e o `JWT_SECRET_KEY` do exemplo antes de qualquer uso compartilhado.

Testes da API, em `gestao-projetos/backend`:

```bash
.venv/bin/python -m pytest -q
```
