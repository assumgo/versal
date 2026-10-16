# API Versal Folha TXT

Python 3.12+, FastAPI e PostgreSQL 16. Execute os comandos abaixo em `web/backend/`.
O [guia da stack](../README.md) descreve instalação, Docker e migrações.

## Configurar e iniciar

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Configure `DATABASE_URL` e `JWT_SECRET_KEY` (pelo menos 32 caracteres, diferente
da senha do banco) em `.env`. Não versione esse arquivo.

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://localhost:8000/docs. Contrato: http://localhost:8000/openapi.json.
Em `/docs`, faça login com `POST /api/v1/auth/login`, copie `access_token` e use
**Authorize** para informar o Bearer token. Refresh e logout usam cookie HttpOnly;
o refresh token não aparece no JSON. O banco não é criado nem populado ao iniciar a API.

## Primeiro administrador de desenvolvimento

Aplique as migrações antes. O comando exige `ENVIRONMENT=development`, cria os
papéis Administrador, Contador, Operador e Consulta e uma conta ativa com senha
Argon2id. Recebe as credenciais exclusivamente de `FIRST_ADMIN_EMAIL` e
`FIRST_ADMIN_PASSWORD` no ambiente do processo; não há senha padrão.
O e-mail segue a validação do cadastro de usuários e a senha exige 12–1024 caracteres.

Para fornecer os valores no Bash sem gravar a senha no histórico:

```bash
read -r -p 'E-mail do primeiro administrador: ' FIRST_ADMIN_EMAIL
read -r -s -p 'Senha do primeiro administrador: ' FIRST_ADMIN_PASSWORD
export FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD
.venv/bin/python -m app.scripts.seed_admin
unset FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD
```

Configure `ENVIRONMENT=development` em `.env` ou no ambiente. Em produção,
staging ou outro valor o comando retorna código 1 antes de acessar o banco.
Código 0 indica criação ou repetição sem alterações. A repetição para o mesmo
administrador ativo preserva sua senha e não duplica eventos de auditoria.
A criação de uma nova conta é recusada se já houver qualquer usuário. Também
há recusa se o e-mail pertencer a uma conta inativa ou de outro papel. A repetição
para o mesmo administrador ativo continua sem alterações mesmo havendo outros usuários. Não serve para recuperar contas,
reativar usuários ou redefinir senhas; use a administração autenticada.
Papéis, conta e auditoria são confirmados na mesma transação; falhas revertem
as alterações. Execuções simultâneas do bootstrap são serializadas no PostgreSQL.
O evento `user.bootstrap` tem ator nulo por ocorrer antes da primeira sessão.
Nenhuma empresa ou vínculo é criado: o administrador cria empresas pela API e
recebe vínculo ao criá-las, ou concede vínculos explicitamente.

Com Docker, execute na pasta `web/`, após reconstruir a imagem e migrar o banco.
Leia e exporte as duas variáveis acima no shell e use:

```bash
docker compose run --rm -e FIRST_ADMIN_EMAIL -e FIRST_ADMIN_PASSWORD backend python -m app.scripts.seed_admin
unset FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD
```

O Compose configura `ENVIRONMENT=development`. As credenciais não precisam ser
adicionadas ao Compose nem aos arquivos `.env`.

## CORS e autenticação

`FRONTEND_ORIGINS` recebe origens explícitas separadas por vírgula, por exemplo
`http://localhost:5173,http://127.0.0.1:5173`. Cada origem contém protocolo,
host e porta quando necessária, sem caminho, barra final, query ou fragmento.
O padrão é `http://localhost:5173`; valor vazio desabilita acesso entre origens.
Wildcards são rejeitados. CORS permite credenciais, os métodos usados pela API
e os cabeçalhos `Authorization` e `Content-Type`, somente para as origens configuradas.
O frontend deve usar `credentials: 'include'` e access token em memória.
CORS não concede permissão: papel e vínculo por empresa continuam validados no servidor.

## Verificar

```bash
.venv/bin/python -m pytest -q
```

Sem `TEST_DATABASE_URL`, testes PostgreSQL são pulados. Para a verificação
completa, da raiz do repositório:

```bash
bash web/backend/tests/run_postgres.sh
```

O script usa PostgreSQL descartável, verifica upgrade, suíte completa, drift,
downgrade com schema vazio e reaplicação. Nunca use o banco operacional para testes.
O bootstrap não é executado contra a stack por esses testes.
