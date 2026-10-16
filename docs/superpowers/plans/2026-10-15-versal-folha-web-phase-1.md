# Versal Folha TXT Web — Fase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a fundação web multiusuário do Versal Folha TXT com autenticação segura, escopo por empresa, CRUDs iniciais e interface fiel ao desktop.

**Architecture:** Uma API FastAPI versionada persiste em PostgreSQL via SQLAlchemy/Alembic e aplica RBAC mais vínculo por empresa antes de acessar recursos. Um SPA React/Vite usa access token em memória e refresh token `HttpOnly`; a interface reutiliza componentes do design system Versal.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Argon2, PyJWT, pytest, React, TypeScript, Vite, React Router, Vitest, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-15-versal-folha-web-design.md`

## Global Constraints

- Criar todo produto novo sob `web/`; não alterar `C:\Folhas2_18\versal_folha_txt_v2_18`.
- Usar PostgreSQL, SQLAlchemy 2.x e Alembic; valores monetários são `NUMERIC`.
- Não versionar segredos, senhas, tokens reais ou bancos de dados.
- Preservar as sete tabelas operacionais do desktop: campos e nomes originais, IDs/FKs inteiros de 64 bits e competência textual; detalhes na revisão de compatibilidade da spec.
- Usar Argon2, refresh token rotativo/revogável com hash persistido e cookie `HttpOnly`.
- Validar papel e `user_companies` no servidor em toda operação por empresa.
- Preservar logo/ícone e tokens visuais `#315f2f`, `#89bf21`, `#f7faf5`, `#cfdccc`.
- Não migrar parsers, importação completa, exportação TXT ou SQLite nesta fase.

## Review Focus

- Um usuário com papel válido, mas sem vínculo à empresa, recebe `403` e nenhum dado da empresa é exposto (Task 4).
- Refresh token revogado, vencido ou reutilizado não emite nova sessão (Task 3).
- Exclusão/inativação de empresa com histórico preserva integridade referencial e é auditada (Task 5).
- Tela pequena mantém o botão de menu, empresa e competência acessíveis; a tabela rola horizontalmente sem cortar colunas (Task 7).
- Entrada malformada de CPF/CNPJ, competência ou valores decimais retorna erro de validação, sem persistência parcial (Tasks 4 e 5).

---

## Estrutura de arquivos

- `web/backend/app/core/`: configuração, banco, segurança, dependências e auditoria.
- `web/backend/app/models/`: modelos SQLAlchemy das entidades iniciais.
- `web/backend/app/schemas/`: contratos Pydantic de entrada e saída.
- `web/backend/app/repositories/`: consultas segregadas por empresa.
- `web/backend/app/services/`: autenticação e regras de negócio.
- `web/backend/app/api/`: roteadores HTTP e dependências de autorização.
- `web/backend/alembic/`: configuração e revisão inicial de esquema.
- `web/frontend/src/`: shell, design system, API client, estado de sessão e páginas.
- `web/docker-compose.yml`, `web/README.md`: execução local documentada.

### Task 1: Scaffold, configuração e execução local

**Files:**
- Create: `web/backend/requirements.txt`, `web/backend/.env.example`, `web/backend/app/main.py`, `web/backend/app/core/config.py`, `web/backend/tests/test_health.py`
- Create: `web/frontend/package.json`, `web/frontend/.env.example`, `web/docker-compose.yml`, `web/README.md`, `.gitignore`

**Interfaces:**
- Produces: `GET /health -> {"status":"ok"}` e configuração tipada `Settings` usada por toda a API.

- [x] **Step 1: Provide the health test** asserting `GET /health` returns `200` and `{"status":"ok"}`. O teste já existia no commit `f60debc`, junto com a API, e foi reaproveitado nesta entrega.
- **Step 2: Encerrado sem execução retroativa (RED inicial).** O plano previa executar `pytest tests/test_health.py -v` antes do scaffold e observar falha de coleta. Como o teste e a API já existiam no commit `f60debc`, essa etapa não foi executada nem comprovada; não representa trabalho pendente.
- [x] **Step 3: Create FastAPI app, typed environment settings, dependency manifests, Compose services and `.env.example` files.** Include health route and no secret defaults.
- [x] **Step 4: Run** `pytest tests/test_health.py -v`; expect PASS.
- [x] **Step 5: Verify** `docker compose -f docker-compose.yml config` succeeds.
- [x] **Step 6: Commit** `chore: scaffold Versal Folha web application`.

**Status em 2026-10-16:** scaffold React/TypeScript/Vite, lockfile, Dockerfiles,
Compose com PostgreSQL e health checks, exemplos de ambiente e `web/README.md`
implementados. Segredo JWT obrigatório (mínimo de 32 caracteres); credenciais de
banco sem padrão na configuração Python. Teste de saúde preexistente ajustado
para `pytest-asyncio`, já listado nas dependências. Novos testes de configuração
observados falhando antes da correção (4 falhas), depois suíte completa com
**6 testes passando**. Build do frontend concluído. Validação sintática YAML
passou. Após instalar Docker, **Step 5 validado** com `docker compose -f
web/docker-compose.yml config --quiet`. Stack construída e iniciada: PostgreSQL
e backend saudáveis, frontend ativo. HTTP do host confirmou `/health` e a página
inicial; `SELECT 1` no PostgreSQL passou. Dentro dos containers: `pytest -q` com
**6 testes passando** e `npm run build` concluído. Stack mantida em execução local.
Credenciais aleatórias em `web/.env` com modo 0600, ignorado pelo Git.
**Task 1 concluída.** O teste de saúde preexistente atende ao Step 1. O RED
inicial do Step 2 foi encerrado sem execução retroativa, sem alegar uma falha
histórica não comprovada; a execução com sucesso está registrada no Step 4.
Entrega registrada na branch `chore/estrutura-inicial-web` com o commit
`chore: scaffold Versal Folha web application`. Apenas a tarefa 1 está no escopo
desta entrega.

### Task 2: Database foundation and migration

**Files:**
- Create: `web/backend/app/core/database.py`, `web/backend/app/models/{base,user,company,payroll,audit}.py`, `web/backend/alembic.ini`, `web/backend/alembic/env.py`, `web/backend/alembic/versions/0001_initial_schema.py`
- Create: `web/backend/tests/test_models.py`

**Interfaces:**
- Produces: SQLAlchemy metadata and `get_db() -> Generator[Session, None, None]`.
- Produces: initial tables `roles`, `users`, `user_companies`, `companies`, `employees`, `rubrics`, `chart_accounts`, `finance_params`, `imports`, `payroll_lines`, `stored_files`, `audit_logs`, `refresh_tokens`.

- [x] **Step 1: Write model tests** for foreign keys, unique role name, unique user email, unique company membership and `Numeric` payroll value.
- [x] **Step 2: Run** `pytest tests/test_models.py -v`; expect imports to fail.
- [x] **Step 3: Implement declarative models, relationships, UTC timestamps, company/competência indexes and Alembic initial revision.** Keep entities focused by module.
- [x] **Step 4: Run** `alembic upgrade head` against disposable PostgreSQL and `pytest tests/test_models.py -v`; expect PASS.
- [x] **Step 5: Commit** `feat: add PostgreSQL schema and Alembic migration`.

**Status em 2026-10-16:** etapa 2 implementada na pasta atual, branch
`feat/database-foundation`. Revisão solicitada pelo usuário após consultar o
código original: as sete tabelas operacionais mantêm seus campos/nomes originais,
IDs/FKs inteiros de 64 bits e competência textual. PKs `IDENTITY BY DEFAULT`
permitem importar IDs sem renumerar. Campos históricos de folha e parâmetros
financeiros/contábeis preservados; tabelas multiusuário adicionadas separadamente.
A migração inicial `0001` foi corrigida enquanto o PR #2 permanecia aberto;
a versão UUID anterior só havia sido aplicada em bancos descartáveis.
Testes usam o DDL SQLite original sem dados reais e registros sintéticos para
verificar cópia, IDs/vínculos preservados e continuidade da sequência.
Verificação final com `bash web/backend/tests/run_postgres.sh`: **31 testes
passando** antes e depois da reversão/reaplicação, `alembic check` sem diferenças
nos dois ciclos. `valor`/`liquido` preservam NUMERIC sem escala fixa, com testes
para mais de duas casas e valores grandes. Revisão independente aprovada sem
apontamentos, comparando a fixture com o código original. Banco da aplicação e
arquivos originais não alterados; nenhuma migração de dados reais executada.

### Task 3: Authentication, roles and audit service

**Files:**
- Create: `web/backend/app/core/security.py`, `web/backend/app/services/auth.py`, `web/backend/app/services/audit.py`, `web/backend/app/schemas/auth.py`, `web/backend/app/api/routes/auth.py`
- Create: `web/backend/tests/test_auth.py`

**Interfaces:**
- Consumes: `User`, `Role`, `RefreshToken`, `get_db()`.
- Produces: `authenticate(email: str, password: str) -> TokenPair`, `rotate_refresh(raw_token: str) -> TokenPair`, `revoke_refresh(raw_token: str) -> None`, `write_audit(...) -> AuditLog`.

- [x] **Step 1: Write failing tests** for Argon2 password verification, login, `/me`, refresh rotation, logout revocation and rejected reuse.
- [x] **Step 2: Run** `pytest tests/test_auth.py -v`; expect failure before routes/services. Executado com `-q` em vez de `-v`; ver evidência abaixo.
- [x] **Step 3: Implement Argon2 hashing, JWT claims, opaque refresh token hashing, cookie attributes, auth router and `/me`.** Do not return refresh tokens in JSON.
- [x] **Step 4: Run** `pytest tests/test_auth.py -v`; expect PASS. Verificado pela suíte completa com `-q` no script PostgreSQL.
- [x] **Step 5: Commit** `feat: add secure authentication and audit service`.

**Status em 2026-10-16 (somente testes):** `tests/test_auth.py` criado com
21 casos, incluindo credenciais inválidas, usuário inativo, JWT vencido/forjado,
cookie HttpOnly/SameSite e Secure em produção, persistência do hash de refresh,
rotação, expiração, revogação, rejeição de reutilização e logout.
Execução final via `bash web/backend/tests/run_postgres.sh` em PostgreSQL
descartável: **21 falhas esperadas e 31 testes existentes passando**, sem skips.
Quatro falhas por ausência de `app.core.security`; as demais por rotas ainda
inexistentes (HTTP 404). O script encerrou no pytest, sem executar os passos
posteriores de reversão/reaplicação. Código de produção não alterado;
Naquele momento, Steps 3–5 permaneciam pendentes.

**Status em 2026-10-16 (implementação):** endpoints de login, refresh, logout e
`/me`, Argon2id, JWT HS256, schemas e serviço de auditoria implementados.
Serviços recebem `Session` explicitamente como primeiro argumento, sem sessão
global. Roteador de autenticação registrado já nesta task para exercitar a API;
CORS, demais roteadores e bootstrap do administrador continuam na Task 6.
Refresh é opaco, persistido somente como SHA-256, com rotação e cookie HttpOnly,
SameSite=Lax e Secure em produção. Bloqueio por usuário serializa rotação/logout;
reutilização revoga a família e confirma a revogação antes de responder `401`.
Usuários inativos não autenticam, renovam ou acessam `/me`. Eventos de sessão
são auditados na mesma transação. Logout preserva a validade dos access tokens
já emitidos até sua expiração.

Três novos testes observados em RED antes da implementação cobrem revogação da
família, usuário inativo e auditoria sem segredos: **24 falhas e 31 passando**.
Revisão independente não identificou bloqueadores na lógica de sessão; indicou
exposição de senha em erro de validação e falta de testes concorrentes.
A exposição foi tratada como relevante e reproduzida por teste de API
(**1 falha e 55 passando**), depois corrigida removendo input/context das
respostas de validação. Testes com sessões concorrentes independentes continuam
como melhoria de cobertura, não como comportamento comprovado pela suíte atual.
Verificação final: `bash web/backend/tests/run_postgres.sh`, **56 testes passando**
antes e depois de downgrade/reaplicação, sem skips, com `alembic check` sem
diferenças nos dois ciclos. Banco operacional e esquema não alterados.
Implementação e testes concluídos; entrega na branch `feat/secure-authentication`
com o commit `feat: add secure authentication and audit service`.

**Cobertura complementar de concorrência em 2026-10-16:** adicionados três
cenários em `tests/test_auth_concurrency.py`: refresh/refresh, refresh/logout e
logout/refresh. Cada requisição usa sessão/conexão própria; uma conexão
observadora confirma via `pg_blocking_pids` que a segunda requisição aguarda a
primeira antes de liberar sua execução. Verificados status HTTP, quantidade de
tokens, revogação de toda a família, auditoria e rejeição dos tokens sucessores.
As contas sintéticas são confirmadas para visibilidade entre conexões e
removidas ao final com filtros por usuário. Esperas e consultas têm limites.

Verificação inicial com PostgreSQL descartável: **59 testes passando** antes e
depois de reversão/reaplicação, sem diferenças no Alembic. Verificação de mutação
em processo separado, substituindo `Select.with_for_update` por uma operação
sem bloqueio: **os três novos casos falharam** por ausência de bloqueio real.
Nenhum arquivo de produção foi alterado para essa verificação. A lacuna de
cobertura de concorrência citada na revisão anterior foi atendida.

### Task 4: Authorization and user/company administration

**Files:**
- Create: `web/backend/app/core/dependencies.py`, `web/backend/app/services/authorization.py`, `web/backend/app/schemas/user.py`, `web/backend/app/api/routes/users.py`, `web/backend/app/api/routes/companies.py`
- Create: `web/backend/tests/test_authorization.py`

**Interfaces:**
- Produces: `require_roles(*names: str)`, `require_company_access(company_id: int, user: User)`, and admin user/company membership endpoints.

- [x] **Step 1: Write failing tests** that an Administrator can create a user and grant company access, while Consulta cannot write and a linked user cannot see a second company.
- [x] **Step 2: Run** `pytest tests/test_authorization.py -v`; expect failure before dependencies/routes.
- [x] **Step 3: Implement authorization dependencies and administrator endpoints.** Every denial returns `403`; every mutation calls `write_audit`.
- [x] **Step 4: Run** `pytest tests/test_authorization.py -v`; expect PASS.
- [x] **Step 5: Commit** `feat: enforce roles and company access`.

**Status em 2026-10-16:** Task 4 implementada na branch
`feat/authorization-administration`, baseada no merge do PR #3 (`708d709`).
Dependências compartilhadas de autenticação, RBAC e vínculo por empresa;
administração de usuários (criar/listar/consultar/alterar/inativar) e vínculos
(listar/conceder/revogar); leitura de empresas limitada ao usuário autenticado.
Administrador também precisa de vínculo explícito para ler dados da empresa,
mas pode administrar os vínculos de qualquer usuário. DELETE de usuário inativa
para preservar histórico. Concessão e revogação são idempotentes e auditam apenas
mudanças efetivas. Toda mutação é confirmada com sua auditoria na mesma transação,
sem senhas/hashes nos metadados. Papéis e vínculos são consultados em cada requisição.
Rotas registradas nesta task para testar os contratos HTTP; escrita de empresas,
CPF/CNPJ e colaboradores seguem na Task 5; bootstrap de papéis/admin na Task 6.
Schema de resposta de empresas antecipado da Task 5, sem alterar modelos/migrações.

RED observado: **21 falhas por HTTP 404 e 60 testes passando** (59 anteriores e
um caso de alvo ausente). Primeiro GREEN: 80 passando e uma falha na preparação
do teste de duplicidade: rollback removia as contas ainda não confirmadas no
savepoint de preparação. Fixture corrigida para confirmar sua preparação dentro
da transação externa descartável. Depois, **81 passando** em ambos os ciclos.
Cobertura ampliada para atualização inválida, permissões alteradas com JWT já
emitido e rollback de cinco operações quando a auditoria falha. Verificação:
`sg docker -c 'bash web/backend/tests/run_postgres.sh'` com **96 testes passando**
antes e depois de reversão/reaplicação, sem skips e com `alembic check` limpo nos
dois ciclos. Steps 2 e 4 executados pela suíte completa com `-q`, em vez do
comando isolado com `-v`. Banco operacional não alterado.

**Revisão independente e correção final:** revisão somente leitura do intervalo
`708d709..f7c615d` confirmou isolamento por empresa, compatibilidade da autenticação
e atomicidade da auditoria. Encontrou um ponto relevante: remoção do acesso do
último administrador ativo. Quatro casos observados em RED (exclusão, inativação,
rebaixamento de papel e concorrência) resultaram em **4 falhas e 99 passando**.
Correção usa bloqueio da linha do papel Administrador antes do bloqueio do usuário
e exige outro administrador ativo antes de remover acesso administrativo. Retorna
`409` sem alteração/auditoria quando não há substituto; administradores inativos
não contam. Três testes positivos preservam alterações quando há substituto.
Teste concorrente usa sessões/conexões independentes e confirma bloqueio real
via `pg_blocking_pids`, resultado `204`/`409` e um único evento de auditoria.
Validação final: **103 testes passando** em ambos os ciclos completos do script
PostgreSQL, sem skips, Alembic sem diferenças. `git diff --check` limpo.
Sem outros apontamentos acionáveis; a correção foi verificada por RED→GREEN,
sem segunda rodada de revisão. Decisões: usuários são inativados e vínculos
idempotentes; o Administrador gere vínculos globalmente mas precisa de vínculo
para dados; rotas e schema de resposta de empresas antecipados para testes HTTP;
alterar senha preserva sessões. Paginação, normalização de e-mail e recuperação
de conta ficam para definição posterior; bootstrap na Task 6 e CRUD operacional
na Task 5. Essas decisões mantêm comparação exata de e-mail, listas sem paginação
e ausência de recuperação autônoma de conta nesta entrega.

### Task 5: Companies and employees CRUD

**Files:**
- Create: `web/backend/app/repositories/{companies,employees}.py`, `web/backend/app/services/{companies,employees}.py`, `web/backend/app/schemas/{company,employee}.py`, `web/backend/app/api/routes/employees.py`
- Modify: `web/backend/app/api/routes/companies.py`
- Create: `web/backend/tests/test_companies.py`, `web/backend/tests/test_employees.py`

**Interfaces:**
- Produces: company list/read/create/update/inactivate endpoints and employee CRUD scoped to an authorized company.

- [x] **Step 1: Write failing tests** for CPF/CNPJ validation, inactive-company behavior, employee CRUD, company-scoped lists and audit events.
- [x] **Step 2: Run** `pytest tests/test_companies.py tests/test_employees.py -v`; expect failure before repositories/services.
- [x] **Step 3: Implement schemas, repository queries that always filter `company_id`, services and routes.** Use soft inactivation for companies with dependent history.
- [x] **Step 4: Run** `pytest tests/test_companies.py tests/test_employees.py -v`; expect PASS.
- [x] **Step 5: Commit** `feat: add companies and employees CRUD`.

**Status em 2026-10-16:** CRUD de empresas e colaboradores implementado.
Empresas: POST/PATCH/DELETE restritos ao Administrador, mantendo vínculo explícito
para leitura e alterações. Criação concede vínculo ao criador na mesma transação.
DELETE inativa sem remover histórico ou vínculos; PATCH permite reativar.
Colaboradores: GET para todos os papéis autorizados; POST/PATCH/DELETE para
Administrador e Operador, sempre sob `/api/v1/companies/{company_id}/employees`.
DELETE de colaborador remove o cadastro; histórico legado de folha permanece
independente, sem FK para colaboradores. Empresa inativa permite consulta, mas
bloqueia escrita de colaboradores com `409`. Bloqueio da linha da empresa
serializa essas escritas com inativação/reativação.

Obrigatoriedade conferida no desktop (`app.py:1440–1444`, `1479–1482`):
empresa exige código Siagri e razão social, ambos não vazios; CNPJ é opcional.
Cadastro de colaboradores não exige nome, CPF ou outros campos de texto.
CPF/CNPJ aceitam ausência, nulo ou vazio; quando preenchidos, aceitam máscara
convencional e são salvos somente com dígitos, validando dígitos verificadores e
rejeitando sequências repetidas. PATCH distingue ausência (preserva) de
nulo/vazio (limpa campos opcionais); bloqueia nulo/vazio para código Siagri e razão
social, nulo para status e campos extras. Modelos e migrações permanecem intactos.
No desktop, centro de custo e correntista/CPF são exigidos condicionalmente na
exportação (`app.py:2164–2179`), fora do escopo do CRUD da Task 5.
Toda escrita confirma auditoria na mesma transação, com metadados limitados aos
nomes dos campos alterados; falha de auditoria reverte todas as seis operações.
Registro do router de colaboradores antecipado da Task 6 para validar HTTP.
Paginação e unicidade documental não foram acrescentadas ao esquema legado.

RED: **21 falhas por HTTP 404/405, 103 passando**. Primeiro GREEN: **124 passando**;
com cobertura adicional de rollback e reativação, **131 passando**. Steps 2 e 4
executados na suíte completa com `-q` em vez de isolados com `-v`.
Revisão independente somente leitura sem problemas críticos/importantes;
recomendação opcional pendente: teste concorrente de inativação versus escrita
de colaborador (a regra de bloqueio está implementada, com cobertura sequencial).
Validação final: `sg docker -c 'bash web/backend/tests/run_postgres.sh'`
com **131 testes passando nos dois ciclos**, sem skips, Alembic sem diferenças
antes/depois de downgrade e reupgrade e verificação de schema vazio após downgrade.
`git diff --check` limpo. Banco operacional não alterado.

**Correção de obrigatoriedade após consulta ao desktop:** testes de regressão
observaram **10 falhas e 127 passando** antes do ajuste. Depois da correção,
`sg docker -c 'bash web/backend/tests/run_postgres.sh'` passou **137 testes nos
dois ciclos**, sem skips; upgrade/check/downgrade/schema vazio/reupgrade/check
concluídos sem diferenças. Revisão independente da correção sem apontamentos.
Código original e banco operacional não alterados.

### Task 6: Seed data, OpenAPI and backend verification

**Files:**
- Create: `web/backend/app/scripts/seed_admin.py`, `web/backend/tests/test_openapi.py`
- Modify: `web/backend/app/main.py`, `web/backend/README.md`

**Interfaces:**
- Produces: explicit development-only bootstrap command and FastAPI OpenAPI at `/docs`.

- [x] **Step 1: Write failing test** asserting documented auth, company and employee paths appear in OpenAPI.
- [x] **Step 2: Verify existing routes and observe RED for missing functionality.** O contrato OpenAPI já passou, pois as rotas foram registradas nas Tasks 3–5. RED comprovado para CORS e bootstrap na suíte completa; não houve falha de registro de rotas.
- [x] **Step 3: Register routers, CORS from settings and a seed command requiring environment-provided first-admin credentials.** Never embed a default password.
- [x] **Step 4: Run** `pytest -q`; expect all backend tests PASS.
- [x] **Step 5: Commit** `feat: document API and development bootstrap`.

**Status em 2026-10-16:** Task 6 implementada na branch `feat/backend-bootstrap`.
Contrato OpenAPI cobre autenticação, usuários/vínculos, empresas e colaboradores,
com Bearer nas operações protegidas e `/docs` acessível. Rotas preexistentes
preservadas. CORS usa `FRONTEND_ORIGINS` separado por vírgulas, credenciais,
métodos da API e Authorization/Content-Type; origens com wildcard ou caminho
são rejeitadas na configuração. Lista vazia desabilita acesso entre origens.

Bootstrap explícito: `python -m app.scripts.seed_admin`, somente com
`ENVIRONMENT=development`, `FIRST_ADMIN_EMAIL` e `FIRST_ADMIN_PASSWORD` no ambiente.
Validação segue cadastro (senha de 12–1024 caracteres); sem senha padrão.
Cria os quatro papéis e primeiro administrador ativo com Argon2id, junto da
auditoria sem credenciais. Advisory lock serializa execuções do comando.
Repetir para o mesmo administrador ativo preserva senha/auditoria; não promove,
reativa ou cria nova conta quando já existem usuários. Sem empresas/vínculos
automáticos, sem execução no startup e sem alteração de modelos/migrações.
Essa restrição exige administração autenticada para contas posteriores e não
oferece recuperação de conta. Guia em `web/backend/README.md`, com comandos
locais/Compose; referências antigas ao bootstrap futuro corrigidas em `web/README.md`.

RED: **15 falhas e 138 passando** (CORS ausente e módulo de bootstrap inexistente);
validação de origens observada separadamente em RED (**3 falhas e 5 passando**).
Verificação final: `sg docker -c 'bash web/backend/tests/run_postgres.sh'`,
**156 testes passando nos dois ciclos**, sem skips; upgrade/check/downgrade/schema
vazio/reupgrade/check concluídos, Alembic sem diferenças. `git diff --check` limpo.
Revisão independente sem problemas críticos/importantes; esclarecimento textual
sobre repetição do bootstrap incorporado. Cobertura concorrente com conexões
independentes fica como melhoria opcional; o bloqueio está implementado, mas
esse comportamento não foi comprovado por teste concorrente nesta entrega.
Banco operacional não alterado ou populado. Somente Task 6 neste escopo.

### Task 7: React application shell and design system

**Files:**
- Create: `web/frontend/src/{main,App}.tsx`, `web/frontend/src/styles/tokens.css`, `web/frontend/src/styles/global.css`
- Create: `web/frontend/src/components/{Sidebar,Header,StatCard,DataTable,FormField,ConfirmModal,Alert,LoadingState}.tsx`
- Create: `web/frontend/src/pages/{Login,Dashboard,Companies,Employees}.tsx`, `web/frontend/src/test/shell.test.tsx`

**Interfaces:**
- Produces: responsive `AppShell` accepting active company, competence and page content; desktop visual tokens and mobile drawer behavior.

- [x] **Step 1: Write failing component tests** for navigation hierarchy, active item, dashboard cards, responsive drawer trigger and horizontally scrollable table wrapper.
- [x] **Step 2: Run** `npm test -- --run`; expect test/setup failure before components.
- [x] **Step 3: Implement design tokens and reusable components.** Use original logo/icon assets and preserve every sidebar item/order from the desktop.
- [x] **Step 4: Build the visual demo with simulated company, competence, dashboard and table data.** Capture desktop/mobile screenshots and write `web/docs/visual-parity.md` mapping each preserved desktop element.
- [x] **Step 5: Run** `npm test -- --run` and `npm run build`; expect PASS.
- [x] **Step 6: Commit** `feat: add responsive Versal design system and shell`.

Execução Task 7 (2026-10-16): shell e oito componentes reutilizáveis,
Dashboard/Empresas/Colaboradores demonstrativos e componente de prévia de Login.
Logo e ícone originais copiados da distribuição desktop, sem alterações.
Mapa de paridade e quatro capturas em `web/docs/visual-parity.md`.
RED inicial: `npm test -- --run` falhou por ausência de Vitest, antes dos
componentes, conforme previsto no Step 2. Testes de navegador revelaram falhas
reais de retorno de foco e de resize com drawer aberto; corrigidas e verificadas.
Verificação final: 8 testes de componentes, 3 testes Playwright/Chrome, build
TypeScript/Vite e `git diff --check` passando. Auditoria após atualização do
Vitest: zero vulnerabilidades. Revisão independente: resize corrigido; mapa de
paridade criado. API, autenticação e CRUD persistente continuam na Task 8.
Ruling: usar branch própria no checkout atual, sem criar worktree adicional;
o escopo pedido é somente Task 7. Os seletores de contexto ficam somente leitura
nesta demonstração; a seleção integrada pertence à Task 8.

### Task 8: Frontend session, protected routes and CRUD screens

**Files:**
- Create: `web/frontend/src/api/client.ts`, `web/frontend/src/auth/{AuthProvider,ProtectedRoute}.tsx`, `web/frontend/src/api/{auth,companies,employees}.ts`
- Modify: `web/frontend/src/pages/{Login,Companies,Employees}.tsx`, `web/frontend/src/App.tsx`
- Create: `web/frontend/src/test/{auth,authorization,companies,employees}.test.tsx`

**Interfaces:**
- Consumes: API from Tasks 3–5.
- Produces: in-memory session context, refresh-on-start flow, protected routes, company selector and screens with loading/error/forbidden states.

- [x] **Step 1: Write failing tests** for login redirect, unauthenticated-route redirect, `403` message, company selector and Companies/Employees loading/error/success states.
- [x] **Step 2: Run** `npm test -- --run`; expect failure before client/session/screens.
- [x] **Step 3: Implement API client with `credentials: 'include'`, memory-only access token, one refresh retry, routes and forms.** Do not put access or refresh tokens in localStorage/sessionStorage.
- [x] **Step 4: Run** `npm test -- --run` and `npm run build`; expect PASS.
- [x] **Step 5: Commit** `feat: add protected session and initial operation screens`.

**Status em 2026-10-16:** Task 8 implementada na branch
`feat/frontend-session-crud`. Sessão em memória, refresh inicial e renovação
compartilhada com um reenvio, login/logout, rotas protegidas, seletor de empresa
e CRUDs integrados aos contratos existentes. RBAC visual e bloqueio de escrita
em empresa inativa, confirmação de exclusão/inativação, validação do servidor
preservando formulário e descarte de respostas de empresas anteriores.
RED inicial: dois testes de login/seletor falharam antes da implementação;
quatro testes adicionais de cadastros também falharam antes das telas integradas.
Ajustados testes visuais antigos para testar o shell isoladamente e removido o
teste de login desabilitado, substituído por testes do fluxo autenticado.
Revisão independente encontrou reenvio de operação antiga com sessão nova;
regressão observada em RED e corrigida com identidade de sessão por requisição.
Cobertura adicional confirma que resposta antiga não invalida nova sessão.

Decisões: seguir precedente da Task 7 de branch no checkout atual; usar History
API para as três rotas sem dependência adicional; competência local editável
pois a API não oferece listagem; dashboard real apresenta orientação, sem os
indicadores simulados. Custo: novas rotas exigem extensão do mapa e hospedagem
com fallback SPA; competências e indicadores aguardam seus endpoints.
Confirmação de remoção usa seção acessível na página, preservando os componentes
visuais existentes. Documentação em `web/docs/frontend-session.md`.
Validação final: **26 testes Vitest e 3 Playwright passando**, build TypeScript/Vite
e `git diff --check` limpos; testes usam dados sintéticos,
sem alteração de backend, esquema ou banco operacional. Task 9 fora do escopo.

### Task 9: Compose integration, documentation and migration contract

**Files:**
- Modify: `web/docker-compose.yml`, `web/README.md`
- Create: `web/docs/parser-equivalence-strategy.md`, `web/backend/tests/fixtures/README.md`

**Interfaces:**
- Produces: one-command local stack documentation and a parser/export equivalence protocol.

- [ ] **Step 1: Write a failing smoke test/script** that waits for Compose health and calls `/health`.
- [ ] **Step 2: Run** the smoke script; expect failure before final service wiring.
- [ ] **Step 3: Finish Compose networking, health checks and README instructions for environment, migrations, tests, Docker and operational limitations.** Write fixture anonymization and comparison criteria for parsers/TXT.
- [ ] **Step 4: Run** backend tests, frontend tests/build, `docker compose up --build`, smoke test and `docker compose down`; expect PASS.
- [ ] **Step 5: Commit** `docs: add local setup and parser equivalence strategy`.

## Plan self-review

- **Spec coverage:** Tasks 1–2 cover stack and schema; 3–6 security/API/audit; 7–8 visual UI/session/screens; 9 Docker, README and parser-equivalence strategy.
- **Type consistency:** authorization uses the `User` and `company_id` models defined in Task 2; routes in Tasks 4–5 consume the shared `get_db`, `require_roles` and `require_company_access` interfaces.
- **Review Focus coverage:** company isolation is Task 4; revoked refresh reuse Task 3; soft deletion/audit Task 5; responsive constraints Task 7; malformed values Task 5.
- **Deliberate exclusion:** parser and TXT implementation remain explicitly outside this plan; Task 9 only establishes their safety contract.
