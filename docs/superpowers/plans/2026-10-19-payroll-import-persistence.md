# Persistência da importação de folha Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir confirmar uma prévia de folha e persistir importação, linhas, metadados e auditoria atomicamente, além de consultar histórico paginado por empresa.

**Architecture:** Reaproveitar parsing isolado e validações da prévia. Criar serviço de persistência que recebe statement já parseado, revalida usuário/empresa dentro da transação, bloqueia a empresa para serializar duplicatas e grava tudo com auditoria. Adicionar contrato HTTP dedicado e conectar confirmação/histórico à tela existente. Arquivo original permanece temporário e é descartado.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, React/TypeScript, Vitest.

**Spec:** [docs/superpowers/specs/2026-10-19-payroll-import-persistence-design.md](../specs/2026-10-19-payroll-import-persistence-design.md)

## Global Constraints

- Nunca persistir bytes do arquivo nem criar `StoredFile`; manter `stored_file_id` nulo.
- Preservar schema legado e adicionar somente as quatro colunas nullable descritas na spec.
- Não alterar `employees`, `rubrics`, contas ou parâmetros contábeis.
- A rota deve revalidar papel, vínculo e status da empresa; consultas sempre limitadas à empresa da rota.
- Bloquear empresa somente depois do parsing e dentro da transação curta de gravação.
- Dinheiro continua Decimal; cada rubrica cria uma linha preservando ordem e multiplicidade.
- `PayrollLine.liquido` repete o líquido do colaborador em cada rubrica conforme a spec; consumidores não devem somar líquido por linha.
- Não atualizar os artefatos congelados do corpus nem seus resultados esperados.
- Usar somente banco PostgreSQL descartável nos testes de integração.

## Review Focus

- Migração reversível e compatível com registros legados nulos.
- Hash SHA-256, empresa/CNPJ e competência revalidados contra o arquivo parseado; prévia bloqueada não confirmável.
- Duplicidade e confirmações concorrentes serializadas por empresa; erro em qualquer insert reverte import, linhas e auditoria.
- Auditoria e histórico sem CPF, nomes, valores, conteúdo do arquivo ou caminho local.
- Autorização de escrita igual a Administrador, Contador e Operador; Consulta apenas lê histórico.
- Troca de arquivo, competência, empresa ou saída invalida respostas assíncronas e limpa estado de prévia.
- Nenhuma afirmação de homologação Windows; permanece pendente conforme a spec.

---

### Task 1: Persistência e contrato dos metadados

**Files:** `web/backend/app/models/payroll.py`, nova revisão `web/backend/alembic/versions/0002_payroll_import_metadata.py`, `web/backend/tests/test_models.py`, novo `web/backend/tests/test_payroll_import_persistence.py`.

- [ ] **Step 1: Escrever testes de falha para os metadados do modelo.** Verificar os quatro campos nullable e ausência de mudanças nos campos legados; cobrir serialização e constraints relevantes sem assumir que registros antigos tenham metadados.
- [ ] **Step 2: Rodar teste focado e confirmar RED.** De `web/backend/`: `.venv/bin/python -m pytest tests/test_payroll_import_persistence.py -q`; esperado antes da implementação: falha porque o contrato novo ainda não existe.
- [ ] **Step 3: Adicionar colunas ao modelo e migração.** `arquivo_sha256` (String(64)), `arquivo_bytes`, `quantidade_colaboradores`, `quantidade_rubricas` como anuláveis; upgrade adiciona e downgrade remove somente essas colunas.
- [ ] **Step 4: Rodar teste focado e inspeção de migração.** Esperado: testes do modelo passam; migration script contém somente quatro colunas nullable.

### Task 2: Serviço transacional de confirmação

**Files:** novo `web/backend/app/services/payroll_import.py`, schemas novos em `web/backend/app/schemas/payroll_import.py`, `web/backend/app/services/audit.py` somente se assinatura existente exigir ajuste, `web/backend/tests/test_payroll_import_persistence.py`.

- [ ] **Step 1: Adicionar testes de domínio antes da implementação.** Cobrir mapeamento de statement em import/linhas, ordem e repetição de rubricas, Decimal exato, horário ISO UTC comum com auditoria, `stored_file_id=None`, contagens e ausência de PII nos detalhes de auditoria.
- [ ] **Step 2: Rodar os casos novos e confirmar RED.** `.venv/bin/python -m pytest tests/test_payroll_import_persistence.py -q`; esperado: falhas por serviço/contrato ausente.
- [ ] **Step 3: Implementar schemas de resposta e serviço.** O serviço recebe sessão, ator, empresa, metadados do arquivo e statement parseado; inicia transação, bloqueia a linha de `companies`, revalida usuário/papel/vínculo/status, verifica qualquer importação da competência, insere `PayrollImport`, cria `PayrollLine` por rubrica e chama `write_audit` antes do commit. Falhas propagam para rollback integral.
- [ ] **Step 4: Testar rollback provocado.** Injetar falha durante criação de linhas e durante auditoria; confirmar que nenhum import, linha ou evento de auditoria persiste.
- [ ] **Step 5: Rodar testes focados.** Esperado: todos os testes de serviço passam no PostgreSQL descartável usado pelo harness do projeto.

### Task 3: Endpoint de confirmação e histórico

**Files:** novo `web/backend/app/api/routes/payroll_imports.py`, `web/backend/app/main.py`, novos `web/backend/app/schemas/payroll_import.py`, `web/backend/tests/test_payroll_import_api.py`, possivelmente fixture utilitária em `web/backend/tests/conftest.py`.

- [ ] **Step 1: Escrever testes HTTP de contrato.** Cobrir multipart estrito, papéis, vínculo, empresa inativa, hash divergente, competência/CNPJ divergentes, arquivo inválido, conflito por competência repetida, sucesso 201 e histórico com paginação/isolamento/sem campos sensíveis.
- [ ] **Step 2: Cobrir concorrência e atomicidade no PostgreSQL.** Duas confirmações simultâneas da mesma empresa/competência devem resultar em uma criação e um 409; rollback de falha interna não deixa dados parciais.
- [ ] **Step 3: Executar testes focados para confirmar RED.** `.venv/bin/python -m pytest tests/test_payroll_import_api.py -q`; esperado: rota ainda não registrada.
- [ ] **Step 4: Implementar POST reaproveitando helpers da prévia.** Aceitar exatamente `file`, `competence`, `preview_sha256`; usar os limites, validação e runner isolado existentes; não manter arquivo fora do TemporaryDirectory. Comparar hash, status ready, CNPJ e competência contra a prévia recalculada antes de chamar o serviço transacional.
- [ ] **Step 5: Implementar GET de histórico.** `offset >= 0`, `limit` default 50 e máximo 100; ordenar por data_hora desc e ID desc; retornar apenas metadados e contagens, sempre filtrados por empresa autorizada.
- [ ] **Step 6: Registrar router e validar OpenAPI.** Respostas 201/409 e esquemas sem statement, CPF, nomes de colaboradores ou valores no histórico.
- [ ] **Step 7: Rodar testes HTTP e concorrência.** Esperado: casos de contrato, isolamento e atomicidade passam no PostgreSQL descartável.

### Task 4: Cliente frontend e histórico paginado

**Files:** `web/frontend/src/api/payrollPreview.ts` ou novo `web/frontend/src/api/payrollImports.ts`, `web/frontend/src/pages/PayrollImportPreview.tsx`, novos componentes de histórico se necessário, `web/frontend/src/test/payrollPreview.test.tsx`, novos `web/frontend/src/test/payrollImportsApi.test.tsx`.

- [ ] **Step 1: Escrever testes de interface para os estados.** Testar confirmar apenas prévia ready e role autorizado, envio do mesmo File/hash/competência, proteção contra duplo envio, sucesso limpando contexto, 409 mantendo prévia e explicando duplicidade, erro transitório permitindo retry, paginação do histórico e invalidação ao trocar contexto.
- [ ] **Step 2: Rodar testes focados e confirmar RED.** Na raiz `web/frontend/`: `npm test -- --run src/test/payrollPreview.test.tsx`; esperado: comportamento de confirmação/histórico ainda ausente.
- [ ] **Step 3: Implementar chamadas API tipadas.** POST multipart envia novamente arquivo, competência e SHA-256; GET aceita offset/limit e desserializa apenas metadados.
- [ ] **Step 4: Conectar confirmação à prévia.** Renderizar botão apenas quando ready; busy impede repetição; sucesso mostra ID e resumo persistidos e limpa File/prévia; duplicidade preserva o resultado; outros erros permitem nova tentativa com mesmo arquivo.
- [ ] **Step 5: Adicionar histórico paginado.** Mostrar competência, nome seguro, data, estado e contagens; sem PII ou valores. Respeitar autorização para leitura e limpar respostas atrasadas na troca de empresa/competência ou desmontagem.
- [ ] **Step 6: Rodar testes frontend focados.** Esperado: testes novos e existentes da tela passam.

### Task 5: Verificação integrada e revisão final

**Files:** ajustar somente arquivos descobertos por falhas de integração; atualizar `web/docs/` se o contrato público precisar de documentação além da OpenAPI.

- [ ] **Step 1: Rodar suíte PostgreSQL descartável.** De acordo com o repositório, `sg docker -c 'bash web/backend/tests/run_postgres.sh'`; esperado: migrações, suíte backend e `alembic check` concluem sem falha.
- [ ] **Step 2: Rodar suíte e build frontend.** Em `web/frontend/`, executar comando de teste definido em `package.json` e `npm run build`; esperado: testes passam e build TypeScript/Vite completa.
- [ ] **Step 3: Revisar diff de segurança e compatibilidade.** Confirmar ausência de bytes/StoredFile, PII nos logs/auditoria/histórico, mudanças em cadastros e alterações nos fixtures congelados.
- [ ] **Step 4: Executar `git diff --check` e revisar OpenAPI/diff final.** Resolver qualquer whitespace ou inconsistência antes de solicitar code review.
- [ ] **Step 5: Registrar limitações restantes.** Homologação Windows e confirmação funcional da regra de `liquido` permanecem pendentes antes do uso operacional.
