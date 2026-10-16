# Cadastros contábeis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for direct execution in this session, preserving the execution method used in the preceding delivery. Track steps with checkboxes.

**Goal:** Disponibilizar plano de contas e rubricas por empresa com consulta, criação e edição, mantendo a regra de salvamento CC/COR do desktop.

**Architecture:** Estender os padrões existentes de schemas, repositories, services e rotas FastAPI, usando os modelos legados sem migrations. Duas telas React especializadas compartilham paginação e seleção de contas; a API decide as flags efetivamente persistidas. Testes usam PostgreSQL descartável e dados sintéticos.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2, PostgreSQL 16, pytest, React/TypeScript/Vite, Vitest e Playwright, sem dependências novas.

**Spec:** `docs/superpowers/specs/2026-10-16-accounting-catalogs-design.md`, aprovada pelo usuário. Preservar a diferença desktop entre salvar cadastro e futura conferência/exportação.

## Global Constraints

- Não alterar o esquema, renumerar IDs, remigrar o SQLite ou modificar cadastros automaticamente ao abrir uma tela.
- Todos os perfis vinculados podem consultar; somente Administrador e Contador vinculados podem escrever.
- Empresa inativa permite consulta e bloqueia escrita com 409.
- Conta cadastrada prevalece sobre marcações manuais CC/COR ao salvar rubrica, nos dois lados, inclusive ao alterar somente descrição/status.
- Sem conta correspondente, preservar opções manuais e valores omitidos no PATCH; novas rubricas começam com quatro opções Sim.
- Preservar nulos, textos e repetições legados nas leituras; não deduplicar nem sincronizar rubricas em massa.
- Não implementar exclusão, importação de planilhas, conferência financeira ou TXT.
- Não executar testes de mutação no banco da aplicação; preservar a instância `versal-conversao` em execução.
- Não incluir banco, relatórios, senhas, tokens ou dados reais no Git.

## Review Focus

- Conta cadastrada com flag nula/inválida deve ser legível; salvar uma rubrica que dependa dela deve falhar com 409 sem alteração parcial, exigindo correção explícita do cadastro (Task 2).
- Códigos repetidos e zeros à esquerda não podem escolher outra empresa nem perder identidade; lookup usa o menor ID da mesma empresa (Tasks 1–2).
- Resposta ou salvamento tardio após troca de empresa/sessão não pode preencher, fechar ou recarregar a tela de outro contexto (Tasks 3–4).
- Pesquisa com `%`, `_`, acentos e paginação além da última página deve ter resultado e contagem coerentes, sem tratar entrada como SQL ou wildcard implícito (Tasks 1–2).
- Playwright não pode reutilizar o frontend real na porta 5174 nem enviar mutações à API da instância convertida (Task 5).

## Estrutura de arquivos e interfaces comuns

Caminhos de backend são relativos a `web/backend/`; frontend a `web/frontend/`.

- Backend: `app/schemas/accounting.py` para paginação, normalização `normalize_account(value: str) -> str`, `normalize_history(value: str) -> str` e validação comum; módulos `chart_accounts.py` e `rubrics.py` em `schemas/`, `repositories/`, `services/` e `api/routes/` para cada recurso. Registrar routers em `app/main.py`.
- Frontend: `src/api/accounting.ts` para `Page<T> = {items: T[]; total: number; offset: number; limit: number}` e `ListQuery = {q: string; offset: number; limit: number}`; clientes `chartAccounts.ts` e `rubrics.ts`; `CatalogPagination.tsx` e `AccountPicker.tsx`; páginas `ChartAccounts.tsx` e `Rubrics.tsx`. Registrar rotas em `src/App.tsx`; ajustar estilos em `src/styles/global.css` somente quando necessário.
- Testes: `tests/test_chart_accounts.py`, `tests/test_rubrics.py`, `tests/test_accounting_concurrency.py`; frontend `src/test/chartAccounts.test.tsx`, `src/test/rubrics.test.tsx`, `src/test/accountPicker.test.tsx` e `e2e/accounting.spec.ts`.
- Guia `web/docs/accounting-catalogs.md` e capturas sintéticas em `web/docs/screenshots/`.

Listagens usam `q`, `offset` >= 0 e `limit` 1–100 (padrão 50). O frontend oferece 25/50/100. Buscas são substring literal sem distinção de caixa; ordenação textual por código e ID. GET nunca grava. Acrescentar ao plano de contas o filtro opcional `conta`, de igualdade textual exata, para resolver o código digitado sem percorrer páginas de resultados parciais; ele compõe com `q`. Não é um novo endpoint nem altera o comportamento das consultas existentes.

## Task 1: API do plano de contas

**Files:** criar `app/schemas/accounting.py`, `app/schemas/chart_accounts.py`, `app/repositories/chart_accounts.py`, `app/services/chart_accounts.py`, `app/api/routes/chart_accounts.py` e `tests/test_chart_accounts.py`; modificar `app/main.py` e `tests/test_openapi.py`.

**Interfaces:**
- `ChartAccountCreate`: conta/descricao obrigatórios, `utiliza_cc` inteiro estrito 0/1 (padrão 0), `tipo_correntista` texto (padrão `9-Nenhum`); `gera_cor` calculado pelo servidor.
- `ChartAccountUpdate`: somente descricao/utiliza_cc/tipo_correntista; campos extras, nulos explícitos, conta e corpo vazio retornam 422. Resposta aceita nulos legados em todos os campos pertinentes.
- Repository `list_for_company(db: Session, company_id: int, *, q: str, offset: int, limit: int, conta: str | None = None) -> dict`, `find(db, company_id, account_id) -> ChartAccount` e `find_by_code(db, company_id, code) -> ChartAccount | None`, este último ordenando por ID.
- Services `create(db, company_id, payload, actor, ip) -> ChartAccount` e `update(db, company_id, account_id, payload, actor, ip) -> ChartAccount`.
- Rotas GET/POST `/api/v1/companies/{company_id}/chart-accounts` e GET/PATCH `/{account_id}`; POST retorna 201, PATCH 200.

- [ ] **Step 1 — escrever testes antes da implementação.** Reutilizar fixtures de `test_authorization.py` sem duplicar credenciais. `test_chart_accounts_are_scoped_paginated_and_audited`: criação `4.211.020.001` normaliza para `4211020001`; `00123` conserva zeros; tipo `2-Parceiro` resulta em COR=1; editar só descrição conserva COR legado divergente; alterar tipo para `9-Nenhum` resulta em COR=0; rubricas relacionadas permanecem intactas. Testar GET por ID e eventos de auditoria sem valores de formulário.
- [ ] **Step 2 — cobrir limites e permissões.** `test_chart_account_permissions` parametriza os quatro papéis, falta de vínculo, empresa inativa, usuário inativo e ID de outra empresa. `test_chart_account_legacy_rows_remain_readable` cobre campos nulos/repetições e lookup exato por menor ID. `test_chart_account_query_is_literal_and_stable` cobre `%`, `_`, acento, `offset` além do total, limites 0/101 e `conta=00123`. `test_chart_account_invalid_changes_do_not_write` cobre código vazio após normalização, flags -1/2/true, PATCH vazio, company_id, alteração da conta e duplicata nova com 409.
- [ ] **Step 3 — executar RED.** `.venv/bin/python -m pytest tests/test_chart_accounts.py -q`; em PostgreSQL descartável, esperar falhas por rotas/contratos ainda ausentes. Não aceitar casos pulados como prova de RED.
- [ ] **Step 4 — implementar.** `normalize_account` reproduz trim, remoção de `.0` final e caracteres não numéricos; não converte para inteiro. Schemas usam `extra='forbid'` e inteiros estritos. Tipo fornecido é trimado e COR calculado por `startswith('2')`; atualização sem tipo mantém COR. Consultas sempre filtram empresa e escapam `%`/`_` para busca literal. Escritas bloqueiam a empresa, revalidam ativa e duplicata, persistem e auditam numa transação. Registrar rotas e contrato OpenAPI; nenhum DELETE.
- [ ] **Step 5 — verificar GREEN e commit.** Executar testes específicos e OpenAPI em PostgreSQL descartável; esperar aprovação. Executar a suíte backend antes de registrar `feat: add company chart accounts API` com somente arquivos desta tarefa.

## Task 2: API das rubricas e regra desktop

**Files:** criar `app/schemas/rubrics.py`, `app/repositories/rubrics.py`, `app/services/rubrics.py`, `app/api/routes/rubrics.py`, `tests/test_rubrics.py` e `tests/test_accounting_concurrency.py`; modificar `app/main.py`, `tests/test_openapi.py` e normalização comum da Task 1.

**Interfaces:**
- `RubricCreate`: codigo/descricao obrigatórios, tipo P/D/E padrão P, status Ativa/Inativa padrão Ativa; contas opcionais; quatro flags estritas 0/1 padrão 1; historico_id padrão `001000182`, historico limitado a 200 caracteres quando fornecido.
- `RubricUpdate`: campos opcionais, rejeita PATCH vazio, extras, flags/nulos explícitos inválidos e código/descrição/tipo/status esvaziados. Conta vazia é permitida. Campos omitidos mantêm valor, exceto as quatro flags reaplicadas pela regra desktop.
- Repository `list_for_company(db, company_id, *, q, offset, limit, status: str | None = None) -> dict` e `find(db, company_id, rubric_id) -> Rubric`.
- Services `create(db, company_id, payload, actor, ip) -> Rubric` e `update(db, company_id, rubric_id, payload, actor, ip) -> Rubric`.
- Rotas GET/POST `/api/v1/companies/{company_id}/rubrics` e GET/PATCH `/{rubric_id}`; listagem usa `Page` da Task 1. Respostas incluem os campos legados, sem converter nulos em defaults.

- [ ] **Step 1 — escrever os testes desktop.** `test_rubric_save_uses_plan_flags` parametriza débito/crédito e CC/COR: conta Não/manual Sim → Não; conta Sim/manual Não → Sim; conta ausente → manual; alteração somente de descrição/status reaplica ambos os lados. Conta repetida usa menor ID; conta de outra empresa nunca participa. `test_rubric_reads_do_not_synchronize` comprova que GET não grava. `test_incomplete_legacy_account_blocks_save_atomically` cobre flags da conta nulas ou fora de 0/1 e resultado 409 com rubrica/auditoria intactas.
- [ ] **Step 2 — escrever os demais contratos.** CRUD sem DELETE, defaults e PATCH parcial; rubrica de tipo E não vira P; código FGTS é válido; `182` vira `000000182`, `1000182` vira `001000182`, mais de nove dígitos usa os nove finais, vazio explícito usa padrão e omissão preserva legado. Histórico explícito é trimado e cortado em 200 como desktop; GET preserva texto legado maior. Cobrir nulos e repetições, inativação/reativação sem exclusão, novas duplicatas, validações, filtros, RBAC, isolamento e rollback de auditoria.
- [ ] **Step 3 — escrever testes de concorrência real.** Em `test_accounting_concurrency.py`, usar conexões independentes e observar locks PostgreSQL como nos testes de autenticação existentes: criar mesmo código simultaneamente produz um 201 e um 409; escrita concorrente com inativação é serializada pela empresa e uma escrita posterior à inativação retorna 409; repetir para cada recurso. Nenhum teste usa o banco da aplicação.
- [ ] **Step 4 — executar RED.** `.venv/bin/python -m pytest tests/test_rubrics.py tests/test_accounting_concurrency.py -q`; esperar falhas por implementação ausente em banco descartável.
- [ ] **Step 5 — implementar.** Sob lock da empresa, carregar a rubrica pelo par empresa/ID, aplicar campos fornecidos e normalizar contas fornecidas. Resolver os códigos atuais dos dois lados pelo lookup da Task 1 e copiar exatamente as flags válidas da conta; sem correspondência, preservar as marcações manuais. Flag de conta não utilizável retorna 409 antes de confirmar. Não usar OR, exceções de salários/pró-labore ou sincronização em massa. Registrar na auditoria nomes dos campos efetivamente alterados, incluindo flags derivadas, sem valores pessoais.
- [ ] **Step 6 — verificar GREEN e commit.** Executar testes das duas APIs, concorrência e OpenAPI; depois `bash web/backend/tests/run_postgres.sh`, esperando suíte aprovada, downgrade/reupgrade e Alembic sem diferenças. Registrar `feat: add rubric API with desktop accounting rules`.

## Task 3: Tela do plano de contas

**Files:** criar `src/api/accounting.ts`, `src/api/chartAccounts.ts`, `src/components/CatalogPagination.tsx`, `src/pages/ChartAccounts.tsx` e `src/test/chartAccounts.test.tsx`; modificar `src/App.tsx` e estilos se necessário.

**Interfaces:** `ChartAccount` contém os campos do modelo com flags/tipo/textos legados anuláveis; `ChartAccountInput` representa somente campos de escrita da Task 1. Cliente `chartAccounts.list(company: number, query: ListQuery & {conta?: string}) -> Promise<Page<ChartAccount>>`, `read(company, id)`, `create(company, input)` e `update(company, id, input)`. `CatalogPagination({total, offset, limit, busy, onOffsetChange, onLimitChange})` oferece anterior/próxima e 25/50/100. `ChartAccounts({company: Company | null, canWrite: boolean})` recebe contexto do shell.

- [ ] **Step 1 — escrever testes de uso.** Usar API falsa no limite de fetch, sem simular a própria página: primeira carga pede 50; pesquisa zera offset; página seguinte e tamanho enviam parâmetros corretos; mostra nulos como não informado. Criação calcula preview COR e usa resposta salva; edição bloqueia conta e envia somente campos alterados, preservando COR se tipo não mudou. Sem empresa, perfil de consulta e empresa inativa não oferecem escrita. Erros 409/422 mantêm o formulário para correção; botões impedem submissão duplicada.
- [ ] **Step 2 — escrever testes de contexto.** Requisição atrasada da empresa A após trocar para B é ignorada; formulário e paginação são reiniciados. Salvamento concluído após desmontagem não mostra sucesso nem modifica B. Expiração/troca de sessão não reenvia a operação antiga com credenciais novas, usando o cliente existente.
- [ ] **Step 3 — executar RED.** `npm test -- --run src/test/chartAccounts.test.tsx`; esperar falha por página ausente.
- [ ] **Step 4 — implementar.** Registrar `/plano-de-contas` no History API existente e sidebar. Reutilizar DataTable/FormField/Alert/LoadingState; formulário especializado sem status/exclusão. Controlar requisições com guardas de contexto/efeito e respostas do servidor, sem cache compartilhado entre empresas. Formulário de edição mantém valores originais e envia apenas o diff; campos nulos não viram valores padrão silenciosamente. Explicar que o cadastro é da empresa e não da competência.
- [ ] **Step 5 — verificar GREEN e commit.** `npm test -- --run` e `npm run build`; esperar toda a suíte frontend aprovada e build sem erro. Registrar `feat: add chart accounts management screen`.

## Task 4: Tela de rubricas e seleção de contas

**Files:** criar `src/api/rubrics.ts`, `src/components/AccountPicker.tsx`, `src/pages/Rubrics.tsx`, `src/test/rubrics.test.tsx` e `src/test/accountPicker.test.tsx`; modificar `src/App.tsx` e estilos necessários.

**Interfaces:** `Rubric` representa a resposta anulável da Task 2; `RubricInput` usa inteiros 0/1, sem company_id. Cliente `rubrics.list(company: number, query: ListQuery & {status?: string}) -> Promise<Page<Rubric>>`, `read`, `create`, `update`. `AccountPicker({companyId, value, onChange, onResolved, disabled})` emite código e conta resolvida; usa pesquisa paginada e filtro exato `conta` da Task 1. `Rubrics({company, canWrite})` usa paginação da Task 3.

- [ ] **Step 1 — escrever testes do seletor.** Buscar por código/descrição sem carregar todo o plano; digitação direta normaliza código e resolve igualdade exata; conta inexistente permite valor manual; repetidas resolvem menor ID; respostas atrasadas de código/empresa anteriores são ignoradas. Não gerar requisição ou gravação a cada render. Código inválido é apresentado como erro e não vira uma conta selecionada por aproximação.
- [ ] **Step 2 — escrever testes da tela.** Mostrar todos os campos, pesquisa, paginação e filtro status; criar com defaults, editar sem alterar tipo legado, inativar/reativar por PATCH. Abertura exibe flags salvas e aviso de divergência sem salvar. Selecionar conta mostra flags que prevalecerão; conta ausente libera Sim/Não manual; conta inválida mostra necessidade de corrigir o plano. Alterar somente descrição conserva os demais dados no payload e a tela adota as flags retornadas pela API. Cobrir os quatro papéis, empresa inativa, erro, ausência de empresa e troca de contexto durante consulta/mutação.
- [ ] **Step 3 — executar RED.** `npm test -- --run src/test/rubrics.test.tsx src/test/accountPicker.test.tsx`; esperar falhas por componentes ausentes.
- [ ] **Step 4 — implementar.** Registrar `/rubricas`. Separar dados gerais, débito e crédito em formulário responsivo. Expor P/D/E sem redefinir valores legados; histórico limitado a 200 para alterações explícitas e código de histórico com orientação de nove posições. Salvar somente diff no PATCH, inclusive para não truncar históricos legados não editados. Não permitir PATCH vazio; em conta conhecida os controles CC/COR são informativos, em conta ausente são editáveis. Toda gravação depende da resposta da API; não reproduzir regra de exportação no frontend.
- [ ] **Step 5 — verificar GREEN e commit.** Executar toda a suíte frontend e build; esperar aprovação. Registrar `feat: add rubric management with account rule previews`.

## Task 5: Validação completa, capturas e entrega

**Files:** criar `e2e/accounting.spec.ts` e `web/docs/accounting-catalogs.md`; modificar `web/frontend/playwright.config.ts`, e2e existente se necessário e guias backend/frontend. Capturas sintéticas em `web/docs/screenshots/accounting-*.png`.

- [ ] **Step 1 — tornar o E2E isolado antes de abrir navegador.** Configurar `E2E_PORT` com padrão 5175, manter CHROME_PATH existente e `reuseExistingServer: false`. Reutilizar a porta escolhida no baseURL/comando do Vite. Testar execução em servidor próprio: nenhuma navegação para 5174, nenhum backend real. Não matar servidores ou containers em conflito; escolher outra porta com `E2E_PORT`.
- [ ] **Step 2 — escrever testes dos fluxos completos.** Mockar todos os endpoints `/api/v1/**` no navegador com dados sintéticos e persistência em memória: login, empresa, plano, pesquisa e criação/edição; rubrica com conta cadastrada prevalecendo e conta ausente manual; permissões de consulta; troca de empresa; telas desktop e 390px. Request não mockado deve falhar, nunca escapar para API real. Como as telas já existem após as Tasks 3–4, estes testes de integração podem passar na primeira execução; não fabricar um RED. Confirmar que falhariam ao remover comportamento de autorização, roteamento ou atualização das flags.
- [ ] **Step 3 — executar e registrar GREEN.** Na raiz, `bash web/backend/tests/run_postgres.sh` com venv preparada; esperar suíte completa aprovada e Alembic sem drift antes/depois de reaplicar. No frontend, `npm test -- --run`, `npm run build` e `npm run test:e2e`; esperar todas aprovadas. Revisar capturas mostrando tabelas completas com rolagem horizontal no celular e formulários utilizáveis.
- [ ] **Step 4 — documentar e revisar.** Guia explica papéis, conta imutável, paginação, histórico e regra CC/COR com exemplo Não/Sim → Não ao salvar; cita que exportação futura tem regra distinta. Registrar decisões sobre duplicatas/nulos, resultados e capturas. Revisão independente do conjunto conforme fluxo de execução direta; corrigir problemas importantes com regressões RED→GREEN. Não publicar dados reais.
- [ ] **Step 5 — commit e integração.** `git diff --check` e inspeção dos arquivos staged; registrar `test: verify accounting catalogs and document desktop parity`. Publicar em branch própria, sem acrescentar funcionalidades ao PR de migração já existente. Verificar o estado do PR #10/base antes de criar branch/PR; se ainda aberto, evitar misturar commits da migração na descrição desta entrega. Não fazer merge automaticamente.
- [ ] **Step 6 — atualização local após aprovação da implementação.** Recriar somente as imagens/serviços da aplicação da instância `versal-conversao`, preservando o nome do projeto, `.env`, volume PostgreSQL e vínculos. Não executar migrador SQLite, não recriar administrador nem usar `down -v`. Verificar saúde, login e consultas do plano/rubricas; não gravar registros de teste na base convertida. Criar backup e registrar contagens antes/depois da atualização.

## Revisão do plano e decisões de implementação

- Cobertura: plano de contas/normalização/permissões na Task 1; regra desktop, históricos, compatibilidade e concorrência na Task 2; contexto e navegação nas Tasks 3–4; isolamento E2E, capturas e entrega na Task 5.
- O filtro opcional `conta` resolve lookup exato sem baixar milhares de registros; não normaliza códigos legados na leitura.
- Conta legada com flags inutilizáveis pode ser consultada e corrigida explicitamente, mas não pode produzir gravação parcial de rubrica; erro 409 é preferível a inventar um Sim/Não que o desktop não definiu.
- APIs mantêm IDs inteiros e escopo por empresa do sistema existente. Nenhuma nova dependência, constraint, migration ou exclusão é necessária.
- Guardas de contexto e payloads contendo somente diferenças impedem que troca de empresa, tipo legado ou histórico longo sejam alterados como efeito colateral.
- Operação local permanece separada dos testes. Capturas e fixtures nunca usam o banco convertido.
