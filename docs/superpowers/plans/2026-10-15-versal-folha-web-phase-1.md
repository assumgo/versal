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

- [ ] **Step 1: Write the failing health test** asserting `GET /health` returns `200` and `{"status":"ok"}`.
- [ ] **Step 2: Run it** with `pytest tests/test_health.py -v`; expect collection failure before scaffold.
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
Os passos iniciais de RED do health são históricos e não foram refeitos.
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

- [ ] **Step 1: Write model tests** for foreign keys, unique role name, unique user email, unique company membership and `Numeric` payroll value.
- [ ] **Step 2: Run** `pytest tests/test_models.py -v`; expect imports to fail.
- [ ] **Step 3: Implement declarative models, relationships, UTC timestamps, company/competência indexes and Alembic initial revision.** Keep entities focused by module.
- [ ] **Step 4: Run** `alembic upgrade head` against disposable PostgreSQL and `pytest tests/test_models.py -v`; expect PASS.
- [ ] **Step 5: Commit** `feat: add PostgreSQL schema and Alembic migration`.

### Task 3: Authentication, roles and audit service

**Files:**
- Create: `web/backend/app/core/security.py`, `web/backend/app/services/auth.py`, `web/backend/app/services/audit.py`, `web/backend/app/schemas/auth.py`, `web/backend/app/api/routes/auth.py`
- Create: `web/backend/tests/test_auth.py`

**Interfaces:**
- Consumes: `User`, `Role`, `RefreshToken`, `get_db()`.
- Produces: `authenticate(email: str, password: str) -> TokenPair`, `rotate_refresh(raw_token: str) -> TokenPair`, `revoke_refresh(raw_token: str) -> None`, `write_audit(...) -> AuditLog`.

- [ ] **Step 1: Write failing tests** for Argon2 password verification, login, `/me`, refresh rotation, logout revocation and rejected reuse.
- [ ] **Step 2: Run** `pytest tests/test_auth.py -v`; expect failure before routes/services.
- [ ] **Step 3: Implement Argon2 hashing, JWT claims, opaque refresh token hashing, cookie attributes, auth router and `/me`.** Do not return refresh tokens in JSON.
- [ ] **Step 4: Run** `pytest tests/test_auth.py -v`; expect PASS.
- [ ] **Step 5: Commit** `feat: add secure authentication and audit service`.

### Task 4: Authorization and user/company administration

**Files:**
- Create: `web/backend/app/core/dependencies.py`, `web/backend/app/services/authorization.py`, `web/backend/app/schemas/user.py`, `web/backend/app/api/routes/users.py`, `web/backend/app/api/routes/companies.py`
- Create: `web/backend/tests/test_authorization.py`

**Interfaces:**
- Produces: `require_roles(*names: str)`, `require_company_access(company_id: UUID, user: User)`, and admin user/company membership endpoints.

- [ ] **Step 1: Write failing tests** that an Administrator can create a user and grant company access, while Consulta cannot write and a linked user cannot see a second company.
- [ ] **Step 2: Run** `pytest tests/test_authorization.py -v`; expect failure before dependencies/routes.
- [ ] **Step 3: Implement authorization dependencies and administrator endpoints.** Every denial returns `403`; every mutation calls `write_audit`.
- [ ] **Step 4: Run** `pytest tests/test_authorization.py -v`; expect PASS.
- [ ] **Step 5: Commit** `feat: enforce roles and company access`.

### Task 5: Companies and employees CRUD

**Files:**
- Create: `web/backend/app/repositories/{companies,employees}.py`, `web/backend/app/services/{companies,employees}.py`, `web/backend/app/schemas/{company,employee}.py`, `web/backend/app/api/routes/employees.py`
- Modify: `web/backend/app/api/routes/companies.py`
- Create: `web/backend/tests/test_companies.py`, `web/backend/tests/test_employees.py`

**Interfaces:**
- Produces: company list/read/create/update/inactivate endpoints and employee CRUD scoped to an authorized company.

- [ ] **Step 1: Write failing tests** for CPF/CNPJ validation, inactive-company behavior, employee CRUD, company-scoped lists and audit events.
- [ ] **Step 2: Run** `pytest tests/test_companies.py tests/test_employees.py -v`; expect failure before repositories/services.
- [ ] **Step 3: Implement schemas, repository queries that always filter `company_id`, services and routes.** Use soft inactivation for companies with dependent history.
- [ ] **Step 4: Run** `pytest tests/test_companies.py tests/test_employees.py -v`; expect PASS.
- [ ] **Step 5: Commit** `feat: add companies and employees CRUD`.

### Task 6: Seed data, OpenAPI and backend verification

**Files:**
- Create: `web/backend/app/scripts/seed_admin.py`, `web/backend/tests/test_openapi.py`
- Modify: `web/backend/app/main.py`, `web/backend/README.md`

**Interfaces:**
- Produces: explicit development-only bootstrap command and FastAPI OpenAPI at `/docs`.

- [ ] **Step 1: Write failing test** asserting documented auth, company and employee paths appear in OpenAPI.
- [ ] **Step 2: Run** `pytest tests/test_openapi.py -v`; expect failure before route registration.
- [ ] **Step 3: Register routers, CORS from settings and a seed command requiring environment-provided first-admin credentials.** Never embed a default password.
- [ ] **Step 4: Run** `pytest -q`; expect all backend tests PASS.
- [ ] **Step 5: Commit** `feat: document API and development bootstrap`.

### Task 7: React application shell and design system

**Files:**
- Create: `web/frontend/src/{main,App}.tsx`, `web/frontend/src/styles/tokens.css`, `web/frontend/src/styles/global.css`
- Create: `web/frontend/src/components/{Sidebar,Header,StatCard,DataTable,FormField,ConfirmModal,Alert,LoadingState}.tsx`
- Create: `web/frontend/src/pages/{Login,Dashboard,Companies,Employees}.tsx`, `web/frontend/src/test/shell.test.tsx`

**Interfaces:**
- Produces: responsive `AppShell` accepting active company, competence and page content; desktop visual tokens and mobile drawer behavior.

- [ ] **Step 1: Write failing component tests** for navigation hierarchy, active item, dashboard cards, responsive drawer trigger and horizontally scrollable table wrapper.
- [ ] **Step 2: Run** `npm test -- --run`; expect test/setup failure before components.
- [ ] **Step 3: Implement design tokens and reusable components.** Use original logo/icon assets and preserve every sidebar item/order from the desktop.
- [ ] **Step 4: Build the visual demo with simulated company, competence, dashboard and table data.** Capture desktop/mobile screenshots and write `web/docs/visual-parity.md` mapping each preserved desktop element.
- [ ] **Step 5: Run** `npm test -- --run` and `npm run build`; expect PASS.
- [ ] **Step 6: Commit** `feat: add responsive Versal design system and shell`.

### Task 8: Frontend session, protected routes and CRUD screens

**Files:**
- Create: `web/frontend/src/api/client.ts`, `web/frontend/src/auth/{AuthProvider,ProtectedRoute}.tsx`, `web/frontend/src/api/{auth,companies,employees}.ts`
- Modify: `web/frontend/src/pages/{Login,Companies,Employees}.tsx`, `web/frontend/src/App.tsx`
- Create: `web/frontend/src/test/{auth,authorization,companies,employees}.test.tsx`

**Interfaces:**
- Consumes: API from Tasks 3–5.
- Produces: in-memory session context, refresh-on-start flow, protected routes, company selector and screens with loading/error/forbidden states.

- [ ] **Step 1: Write failing tests** for login redirect, unauthenticated-route redirect, `403` message, company selector and Companies/Employees loading/error/success states.
- [ ] **Step 2: Run** `npm test -- --run`; expect failure before client/session/screens.
- [ ] **Step 3: Implement API client with `credentials: 'include'`, memory-only access token, one refresh retry, routes and forms.** Do not put access or refresh tokens in localStorage/sessionStorage.
- [ ] **Step 4: Run** `npm test -- --run` and `npm run build`; expect PASS.
- [ ] **Step 5: Commit** `feat: add protected session and initial operation screens`.

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
