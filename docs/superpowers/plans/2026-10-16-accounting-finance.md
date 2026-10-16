# Parametrizações contábil e financeira — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Disponibilizar a conferência contábil dos movimentos convertidos e o cadastro financeiro com as regras do desktop.

**Architecture:** Duas entregas independentes, financeira primeiro e conferência depois, na mesma branch isolada baseada na main após PR #11. Reutilizar autorização, auditoria, paginação e componentes atuais. Calcular a conferência no servidor, somente em leitura, sem materializar resultados nem alterar os cadastros.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, Pydantic, PostgreSQL 16, React/TypeScript/Vite, Node.js 24, pytest, Vitest e Playwright.

**Spec:** `docs/superpowers/specs/2026-10-16-accounting-finance-design.md`, aprovada pelo usuário.

## Global Constraints

- Não requerem migração do banco.
- Usuários vinculados podem consultar. Administrador e Contador podem criar parâmetros financeiros; empresa inativa bloqueia criação.
- Banco, arquivos e credenciais reais continuam fora do Git.
- Usar somente PostgreSQL descartável para testes.
- Não criar cadastros nem corrigir registros ao consultar.
- Sem edição, exclusão ou inativação de parâmetros financeiros nesta entrega.
- Não implementar importação de arquivos nem exportação TXT.

## Review Focus

- Empresa ou competência muda durante uma consulta: respostas antigas não reaparecem (Tasks 2 e 4).
- Decimal grande ou fracionário: resposta textual não perde precisão nem arredonda (Task 3).
- Duplicatas de rubrica/colaborador/conta: menor ID vence sem multiplicar movimentos (Task 3).
- Registros legados nulos ou flags fora de 0/1: leitura determinística e sem gravação (Task 3).
- Criação financeira concorrente com inativação: bloqueio de empresa impede gravar após inativação confirmada (Task 1).

## Preparação da execução

- [ ] Criar worktree `feat/accounting-finance` a partir da main atual, preservando documentos aprovados e a instância `versal-conversao`.
- [ ] Ler spec e plano, conferir dependências instaladas e iniciar PostgreSQL descartável com porta/volume distintos do operacional. Registrar comandos e resultados no ledger ignorado da execução.

### Task 1: API de parâmetros financeiros

**Files:** criar `web/backend/app/{schemas,repositories,services}/finance_params.py`, `web/backend/app/api/routes/finance_params.py` e `web/backend/tests/test_finance_params.py`; modificar `web/backend/app/main.py` e `web/backend/tests/test_openapi.py`.

**Interfaces:** `FinanceParamCreate` contém oito campos: `tipo`, `documento_id`, `parceiro_cpf_cnpj`, `codigo_parceiro_siagri`, `conta_contrapartida`, `centro_custo`, `vencimento_dia`, `historico`. Textos padrão `''`; dia inteiro estrito 1..31, padrão 1; extras proibidos. `FinanceParamResponse` expõe ID, empresa, os oito campos anuláveis legados e `ativo`. `repository.list_for_company(db, company_id, *, offset=0, limit=50) -> Page[FinanceParamResponse]`; `service.create(db, company_id, payload, actor, ip) -> FinanceParam`.

- [ ] **Step 1 — testes RED:** escrever `test_finance_create_preserves_desktop_fields`: tipo `' INSS '` retorna `'INSS'`, conta `' 001.23 '` e documento `'0007'` permanecem literais; dia 1; ativo 1. `test_finance_allows_repeated_and_empty_types`: duas criações iguais e tipo vazio são aceitos. `test_finance_scope_roles_legacy_and_validation`: paginação 50 padrão/100 máximo, ordenação tipo com nulos primeiro e ID, nulos preservados, Consulta/Operador POST 403, empresa sem vínculo 403, inativa 409, dia 0/32/bool/string/nulo 422, campos extras 422; ausência de PATCH/DELETE. `test_finance_audit_rollback_and_inactivation_lock`: auditoria sem valores, falha de auditoria desfaz criação, transações independentes exercitam bloqueio de empresa durante inativação.
- [ ] **Step 2 — executar RED:** `.venv/bin/python -m pytest tests/test_finance_params.py tests/test_openapi.py -q` com `TEST_DATABASE_URL` exclusivamente descartável; falhas devem decorrer de rotas ausentes, não de infraestrutura.
- [ ] **Step 3 — implementar:** GET/POST `/api/v1/companies/{company_id}/finance-params`, `AuthorizedCompany`, `Writer`, `require_active` e `save` existentes. Somente tipo recebe trim. INSERT e auditoria atômicos; listar todos os registros, inclusive `ativo=0`/nulo. Nenhuma unicidade nova.
- [ ] **Step 4 — verificar GREEN:** repetir suíte focada e verificar OpenAPI e testes existentes de autorização.
- [ ] **Step 5 — commit:** `feat: add scoped financial parameter API`.

### Task 2: Tela financeira utilizável

**Files:** criar `web/frontend/src/api/financeParams.ts`, `web/frontend/src/pages/FinanceParams.tsx`, `web/frontend/src/test/financeParams.test.tsx`; modificar `web/frontend/src/App.tsx`.

**Interfaces:** `financeParams.list(company: number, query: {offset?: number; limit?: number}) -> Promise<Page<FinanceParam>>`, `create(company: number, input: FinanceParamInput) -> Promise<FinanceParam>`. `FinanceParams({company: Company|null, canWrite: boolean})`. Rota `/parametrizacao-financeira` no menu existente.

- [ ] **Step 1 — testes RED:** `creates_financial_parameter_without_normalizing_text` preenche os oito campos e verifica payload literal e registro retornado; `lists_legacy_values_and_pages` verifica nulos, vencimento e offsets; `limits_writes_by_role_and_company_status` cobre quatro papéis, empresa inativa e ausência de empresa; `discards_late_results_after_company_switch` cobre lista e POST atrasados; `keeps_form_on_error_and_prevents_double_submit` cobre 409/422 e submissão pendente.
- [ ] **Step 2 — executar RED:** `npm test -- --run src/test/financeParams.test.tsx`; confirmar ausência da funcionalidade.
- [ ] **Step 3 — implementar:** formulário com rótulos desktop e sugestões livres para tipo, dia inicial 1, tabela de oito colunas, paginação 25/50/100, estados loading/erro/vazio. Não exigir textos preenchidos nem oferecer editar/excluir. Chavear contexto por empresa/status/permissão; repetir padrões de descarte assíncrono dos catálogos. Reutilizar componentes e CSS existentes.
- [ ] **Step 4 — verificar GREEN:** suíte focada, `npm run build` e testes de App/navegação.
- [ ] **Step 5 — commit:** `feat: add financial parameter screen`.

### Task 3: API de conferência contábil

**Files:** criar `web/backend/app/schemas/accounting_review.py`, `web/backend/app/repositories/accounting_review.py`, `web/backend/app/services/accounting_review.py`, `web/backend/app/api/routes/accounting_review.py`, `web/backend/tests/test_accounting_review.py`; modificar `web/backend/app/main.py` e `web/backend/tests/test_openapi.py`.

**Interfaces:** GET `/api/v1/companies/{company_id}/competences` retorna `list[str]`, competências distintas não vazias da empresa, mais recentes primeiro (MM/YYYY válidas primeiro; demais textos legados depois por texto). GET `accounting-review` exige `competence` válido MM/YYYY e devolve `Page[AccountingReviewRow]`. Campos: `id`, `competencia`, `cpf`, `nome`, `codigo_verba`, `verba`, `valor` (texto decimal ou nulo), `conta_debito`, `debito_gera_cc`, `debito_gera_cor`, `conta_credito`, `credito_gera_cc`, `credito_gera_cor`, `historico_id`, `historico`, `centro_custo`, `correntista`, `fonte`. Flags efetivas booleanas. `list_for_company(db, company_id, *, competence, offset=0, limit=50)` e `list_competences(db, company_id)` no repositório; regras puras `effective_cc(plan_flag, rubric_flag) -> bool`, `effective_cor(account, plan_flag, rubric_flag, employee_linked) -> bool` no serviço.

- [ ] **Step 1 — testes RED:** criar fixtures sintéticas com referências calculadas manualmente a partir das funções desktop. `test_review_combines_sources_without_mutation` retorna todas as fontes e preserva contagens/campos antes/depois. `test_review_matches_desktop_cc_cor_and_history` fixa OR para CC, OR para COR, exceções `4211020001`/`4211010001` somente com colaborador, sem rubrica COR falso, histórico normalizado e CPF como correntista. `test_review_employee_matching_and_duplicate_precedence` fixa CPF exato sem fallback ao nome quando informado, nome case insensitive quando CPF ausente, colaborador inativo permitido e menor ID em cada duplicata. `test_review_preserves_decimal_nulls_and_line_multiplicity` fixa `'12345678901234567890.123456789'`, valor nulo, flags nulas/desconhecidas sem alteração e movimentos repetidos. `test_review_scope_competences_pagination_and_invalid_input` cobre duas empresas, duas competências, nulos/vazios, ordenação estável, limites 1..100 e mês 00/13 ou formato incorreto 422. Conferir ausência de auditoria de mutação e RBAC de leitura para os quatro papéis.
- [ ] **Step 2 — executar RED:** `.venv/bin/python -m pytest tests/test_accounting_review.py tests/test_openapi.py -q` no banco descartável; confirmar rotas ausentes.
- [ ] **Step 3 — implementar:** paginar movimentos por competência/nome/código/ID com nulos primeiro como SQLite; contar movimentos, sem multiplicação por joins. Resolver cadastros em lotes da página, sempre filtrados pela empresa, menor ID por chave. Plano usa busca pelo código armazenado igual à conta normalizada, como desktop. Flags inteiras de plano seguem truthiness para CC; COR segue a conversão inteira do plano e truthiness do máximo entre plano, rubrica e compatibilidade (nulo de plano tratado como zero para a leitura legada); flags da rubrica seguem `flag_enabled` desktop. Preservar nulos dos campos existentes e usar vazio apenas quando vínculo não existe. Importações devem pertencer à mesma empresa. Nenhum INSERT/UPDATE ou sincronização ao consultar.
- [ ] **Step 4 — verificar GREEN:** repetir suíte focada e regressões dos catálogos. Verificar que consultas não crescem por movimento (sem N+1), inclusive com página de 100 registros.
- [ ] **Step 5 — commit:** `feat: add desktop-compatible accounting review API`.

### Task 4: Conferência na interface e validação da entrega

**Files:** criar `web/frontend/src/api/accountingReview.ts`, `web/frontend/src/pages/AccountingReview.tsx`, `web/frontend/src/test/accountingReview.test.tsx`, `web/frontend/e2e/accounting-finance.spec.ts`, `web/docs/accounting-finance.md`; modificar `web/frontend/src/App.tsx` e `web/README.md`. Capturas sintéticas em `web/docs/screenshots/`.

**Interfaces:** `accountingReview.competences(company: number) -> Promise<string[]>`, `list(company: number, query: {competence: string; offset?: number; limit?: number}) -> Promise<Page<AccountingReviewRow>>`. `AccountingReview({company: Company|null})`, rota `/parametrizacao-contabil`. Campos e tipos seguem Task 3.

- [ ] **Step 1 — testes RED:** `selects_latest_valid_competence_and_lists_all_columns`, `changes_competence_resets_offset_and_refreshes`, `shows_empty_invalid_legacy_competence_and_retry_states`, `discards_old_company_and_competence_responses`. Mostrar competência legada inválida sem chamar endpoint inválido e orientar seleção de competência válida; não converter ou corrigir banco. Conferir exibição do decimal grande sem converter para Number, flags Sim/Não e nenhuma ação de gravação. Navegador cobre login/navegação, criação financeira literal, conferência das 17 colunas e uso móvel sem overflow da página.
- [ ] **Step 2 — executar RED:** Vitest focado e Playwright com APIs simuladas; confirmar falhas funcionais esperadas.
- [ ] **Step 3 — implementar:** selecionar mais recente válida da lista, filtrar consulta pelo seletor local e indicar competência consultada. O campo de cabeçalho existente permanece independente, conforme spec; não trocar silenciosamente a competência da consulta. Botão Atualizar recarrega competências e movimentos, preservando seleção válida. Paginação 25/50/100, rolagem horizontal e estados loading/erro/vazio. Requisições antigas não podem substituir contexto novo. Documentar regras desktop e limites.
- [ ] **Step 4 — verificar:** backend completo com PostgreSQL descartável, Alembic check (sem drift), frontend completo, build e Playwright com porta exclusiva diferente de 5174. Inspecionar screenshots sintéticas desktop/mobile e `git diff --check`. Uma revisão independente da branch ao final, corrigindo problemas encontrados com regressões.
- [ ] **Step 5 — commit:** `feat: add accounting review and document financial workflows`.

## Publicação e instância local

- [ ] Publicar branch e abrir PR com comportamento, compatibilidade, comandos/resultados e screenshots. Não efetuar merge automaticamente.
- [ ] Fazer backup privado do PostgreSQL operacional e registrar contagens/hashes dos nove conjuntos já usados na atualização anterior. Atualizar somente backend/frontend do projeto `versal-conversao`, mantendo volume, credenciais e portas 5174/8001. Não executar conversão novamente nem seeds.
- [ ] Conferir saúde, login e consultas das novas rotas; comparar hashes antes/depois sem gravar parâmetros financeiros no banco real como teste. Registrar resultados privados fora do Git e informar URL/PR ao usuário.

## Autorrevisão do plano

Spec coberta: financeira Tasks 1–2; competências, regras e leitura contábil Tasks 3–4; permissões/auditoria Task 1; isolamento Tasks 1/3; contexto e móvel Tasks 2/4; entrega e preservação operacional na seção final. Interfaces mantêm nomes consistentes entre API e clientes; não há novos modelos, migrations ou dependências previstos.
