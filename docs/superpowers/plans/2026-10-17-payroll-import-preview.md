# Upload e prévia de Extrato Mensal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the existing inline execution preference. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Disponibilizar upload e conferência temporária de Extrato Mensal PDF/XLS/XLSX, comparando empresa e competência sem persistir dados.

**Architecture:** Uma rota autorizada recebe multipart limitado, valida o arquivo e executa o parser em subprocesso com prazo e concorrência limitados. Serviços puros calculam resumo e divergências; a tela mantém a resposta somente em memória e pagina localmente. Reutilizar autenticação, parsers e componentes atuais.

**Tech Stack:** Python 3.12+, FastAPI, python-multipart, asyncio subprocess, Decimal, PostgreSQL 16 descartável, React/TypeScript/Vite, pytest, Vitest e Playwright.

**Spec:** `docs/superpowers/specs/2026-10-17-payroll-import-preview-design.md`, aprovada pelo usuário.

## Global Constraints

- Trabalhar na branch `feat/payroll-import-preview`, baseada na main `0280615`; preservar o checkout e a instância operacional.
- Sem INSERT/UPDATE/DELETE, auditoria de importação, stored_files ou migrations. Sem confirmação de importação ou TXT.
- Administrador, Contador e Operador com vínculo podem enviar; Consulta recebe 403; empresa inativa recebe 409.
- Arquivo até 10 MiB; XLSX até 50 MiB declarados descompactados, sem entradas criptografadas; somente PDF/XLS/XLSX com assinatura coerente.
- Processo de leitura: 30 segundos, duas execuções simultâneas por processo da API; encerrar e aguardar processos antes de remover temporários.
- Resultado até 2.000 colaboradores e 10.000 rubricas; exceder retorna 413, sem truncar.
- Decimais textuais no JSON e na interface; preservar regras do parser e corpus congelado.
- Revalidar usuário, papel, vínculo e atividade antes da resposta; descartar respostas fora do contexto na interface.
- Dados/documentos reais, logs com conteúdo e credenciais ficam fora do Git. Testes somente sintéticos e PostgreSQL descartável.

## Review Focus

- Content-Length ausente ou falso não pode permitir leitura ilimitada do corpo multipart (Task 3).
- Subprocesso com saída maior que o buffer do pipe deve concluir sem deadlock; timeout/cancelamento libera vaga e temporários (Task 2).
- Revogação de acesso durante parsing não pode retornar resultado usando objetos antigos do SQLAlchemy (Task 3).
- Somar números grandes e fracionários não pode arredondar pelo contexto Decimal padrão nem multiplicar líquido por rubrica (Task 1).
- Refresh após 401 e troca de contexto durante POST não podem enviar JSON ou mostrar resultado antigo (Tasks 4/5).

## Preparação

- [ ] Ler spec e plano; confirmar branch, status e dependências. Registrar baseline backend/frontend no ledger ignorado da execução. Em caso de bloqueio de sandbox, repetir a verificação necessária com escalonamento, sem atribuir o bloqueio ao produto.
- [ ] Conferir interfaces entre tarefas e registrar decisões no ledger; manter execução direta nesta sessão. Revisão própria ao final, sem delegação não solicitada.

### Task 1: Contrato da resposta, resumo exato e divergências

**Files:** criar `web/backend/app/schemas/payroll_preview.py`, `web/backend/app/services/payroll_preview.py` e `web/backend/tests/test_payroll_preview_summary.py`.

**Interfaces:** schemas `PreviewIssue(code, severity, message)`, `PreviewSummary(employees, rubrics, totals_by_type, net_total)` e `PayrollPreviewResponse(company_id, requested_competence, filename, size_bytes, sha256, status, issues, summary, statement)`. `totals_by_type` possui chaves P/D/E e valores textuais, inclusive zero; `statement` possui os campos do ParsedStatement, com valores monetários textuais. Serviços `summarize(statement: ParsedStatement) -> PreviewSummary` e `build_preview(statement, *, company_id: int, company_cnpj: str | None, competence: str, filename: str, size_bytes: int, sha256: str, extension: str) -> PayrollPreviewResponse`.

- [ ] **Step 1 — RED:** `test_summary_counts_each_net_once_and_preserves_multiplicity` fixa duas pessoas, três rubricas incluindo duplicata, P=20.00, D=-1.25, E=0, líquido=18.75. `test_summary_preserves_large_fractional_decimals` fixa soma de `123456789012345678901234567890.123456789` com `0.000000001` igual a `123456789012345678901234567890.123456790`. `test_preview_context_issues` cobre CNPJ formatado igual, ausente/incompleto/divergente e competência igual/ausente/inválida/divergente. `test_empty_result_is_blocked_and_warnings_are_format_specific` verifica bloqueio vazio, aviso de homologação sempre e avisos próprios de PDF/Excel, sem corrigir o statement.
- [ ] **Step 2 — executar RED:** em `web/backend/`, `.venv/bin/python -m pytest tests/test_payroll_preview_summary.py -q`; confirmar ausência da funcionalidade.
- [ ] **Step 3 — implementar:** somar usando contexto Decimal dimensionado pelos expoentes/dígitos e quantidade de termos, sem perda adicional. Emitir códigos estáveis: `company_cnpj_missing`, `company_cnpj_mismatch`, `competence_missing`, `competence_invalid`, `competence_mismatch`, `no_employees`, `no_rubrics`, `homologation_pending`, `pdf_known_limitations`, `excel_known_limitations`. `company_cnpj_missing` também cobre cadastro incompleto. Mensagens não revelam outro cadastro. Qualquer blocking define blocked; caso contrário ready.
- [ ] **Step 4 — GREEN:** repetir suíte focada e integridade do corpus; comparar statement antes/depois para confirmar ausência de mutação e Decimal no objeto original.
- [ ] **Step 5 — commit:** `feat: define payroll preview results and exact totals`.

### Task 2: Arquivos temporários e parser em subprocesso

**Files:** criar `web/backend/app/services/payroll_preview_files.py`, `web/backend/app/services/payroll_preview_runner.py`, `web/backend/app/services/payroll_preview_worker.py`, `web/backend/tests/test_payroll_preview_files.py` e `web/backend/tests/test_payroll_preview_runner.py`.

**Interfaces:** `PreviewInputError(status_code: int, message: str)` em files; `validate_document(path: Path, extension: str) -> None`; `safe_filename(original: str | None) -> str` (basename Unix/Windows, máximo 255). `PreviewRunner.run(path: Path, extension: str) -> ParsedStatement` é async; instância única por processo usa limite de duas execuções. Worker CLI `python -m app.services.payroll_preview_worker <path> <extension>` escreve somente um envelope JSON no stdout: sucesso com statement, ou erro com categoria pública. Converte Decimal em texto na saída e reconstrói Decimal no runner. Não carregar app.main/configuração/banco no worker.

- [ ] **Step 1 — RED:** files testa assinaturas reais do corpus, extensão maiúscula, extensão incoerente, zero bytes, XLSX sem workbook, ZIP criptografado e soma declarada acima de 50 MiB. Runner testa os três formatos reais; saída maior que 64 KiB; erro de layout, arquivo corrompido, limite de 2.000/10.000, timeout e cancelamento. Fixture de processo controlado para testes de prazo/concorrência não altera código de parsing; dois workers ocupados fazem terceiro retornar 503; após timeout/cancelamento, PID termina e nova execução é aceita.
- [ ] **Step 2 — executar RED:** `.venv/bin/python -m pytest tests/test_payroll_preview_files.py tests/test_payroll_preview_runner.py -q`; falhas devem indicar interfaces ausentes, não dependências do corpus.
- [ ] **Step 3 — implementar arquivos:** validar assinatura PDF (`%PDF-`), OLE XLS e ZIP/XLSX com workbook XML/conteúdo esperado. Inspecionar diretório ZIP sem extrair. Validar bytes/tamanho, gerar nomes temporários próprios e erros públicos sem mensagens originais dos leitores. O chamador é dono da pasta temporária; runner aguarda processo antes de retornar/propagar cancelamento.
- [ ] **Step 4 — implementar runner/worker:** usar executable da venv e processo sem shell; consumir stdout enquanto aguarda encerramento (`communicate`), stderr descartado, sem log de conteúdo. Worker valida limites antes de serializar resposta. Prazo total de 30 s inclui leitura e comunicação; timeout retorna 504. Em finally, terminar processo se vivo, aguardar e liberar vaga; não enfileirar além das duas execuções. Tratar queda/saída inválida com erro público 400, sem stack trace. `UnsupportedLayoutError` vira 415.
- [ ] **Step 5 — GREEN:** repetir arquivos/runner e todos os testes dos parsers; exigir encerramento efetivo dos processos, liberação das vagas e corpus intacto.
- [ ] **Step 6 — commit:** `feat: run preview parsing with bounded worker lifecycle`.

### Task 3: Rota multipart autorizada sem persistência

**Files:** criar `web/backend/app/api/routes/payroll_preview.py` e `web/backend/tests/test_payroll_preview_api.py`; modificar `web/backend/app/main.py`, `web/backend/requirements.txt` e `web/backend/tests/test_openapi.py`.

**Interfaces:** POST `/api/v1/companies/{company_id}/payroll-import-preview`, corpo multipart `file` + `competence`, resposta PayrollPreviewResponse. Consome os serviços das Tasks 1/2. Declarar `python-multipart>=0.0.20,<1`. Documentar multipart/erros no OpenAPI mesmo usando leitura controlada do Request.

- [ ] **Step 1 — RED:** integração cobre três papéis permitidos, Consulta 403, não autenticado 401, duas empresas/vínculos, inativa 409, campos repetidos/extras/ausentes e competência inválida 422. Enviar corpus PDF/XLS/XLSX e conferir 200 ready com contexto sintético correspondente; divergências e vazio legível produzem 200 blocked. Arquivo vazio/corrompido 400, extensão/assinatura/layout 415, bytes/resultados excessivos 413, busy 503, prazo 504. Testar Content-Length falso/ausente em corpo fragmentado; upload nunca deve consumir bytes ilimitados. Snapshot das tabelas operacionais, stored_files e audit_logs permanece igual.
- [ ] **Step 2 — executar RED:** PostgreSQL exclusivamente descartável; `.venv/bin/python -m pytest tests/test_payroll_preview_api.py tests/test_openapi.py -q`; confirmar rota ausente.
- [ ] **Step 3 — implementar recepção:** autorizar antes de iniciar parser; ler `request.stream()` com teto de 10 MiB + 64 KiB para envelope multipart. Content-Length pode antecipar rejeição, nunca substituir contagem. Ao exceder teto, abortar com 413. Parsear o corpo limitado via Starlette/python-multipart; validar exatamente uma ocorrência de cada campo, um arquivo e nenhum extra. Normalizar falhas de estrutura/campos para 422 e conferir limite real de 10 MiB do arquivo. Fechar form/uploads e pasta temporária em finally. Não instalar dependências geradoras do corpus.
- [ ] **Step 4 — implementar serviço da rota:** executar runner sem prender event loop nem manter lock de empresa. Observar desconexão e cancelar runner; aguardar cleanup antes de sair. Após processamento, desfazer a transação somente de leitura/expirar identidade, consultar novamente usuário, papel, vínculo e empresa, aplicando 401/403/409 atuais. Não confiar nos objetos carregados antes do subprocesso. Montar resposta com `Cache-Control: no-store`; nenhum commit/save/auditoria.
- [ ] **Step 5 — verificar concorrência e cleanup:** teste com parsing suspenso altera vínculo, papel, atividade de usuário ou empresa em conexão independente; conclusão deve negar conforme estado novo. Injetar erros em recepção, validação, leitura e resposta; pasta temporária e subprocessos devem terminar, inclusive na desconexão. Repetir integração, OpenAPI e regressões de autorização.
- [ ] **Step 6 — commit:** `feat: expose authorized payroll upload preview endpoint`.

### Task 4: FormData com sessão e tela de conferência

**Files:** criar `web/frontend/src/api/payrollPreview.ts`, `web/frontend/src/pages/PayrollImportPreview.tsx`, `web/frontend/src/components/PayrollPreviewResult.tsx`, `web/frontend/src/test/payrollPreview.test.tsx` e `web/frontend/src/test/payrollPreviewApi.test.ts`; modificar `web/frontend/src/api/client.ts` e `web/frontend/src/App.tsx`; CSS existente apenas se necessário.

**Interfaces:** `payrollPreview.generate(company: number, file: File, competence: string, options?: {signal?: AbortSignal}) -> Promise<PayrollPreviewResponse>`; tipos TS iguais à API, valores monetários string. `PayrollImportPreview({company: Company|null, competence: string, canPreview: boolean})`; competence é YYYY-MM do cabeçalho. Rota `/importacao-folha`; canPreview para Administrador/Contador/Operador. `PayrollPreviewResult({preview})` mantém paginação e seleção de colaborador somente na resposta atual.

- [ ] **Step 1 — RED:** API verifica FormData com exatamente file/competence, Authorization, cookie, ausência de Content-Type definido pela aplicação; 401 seguido de refresh reenvia documento/campos e token atual. JSON existente continua com Content-Type JSON; AbortSignal propaga. Tela cobre quatro papéis, sem empresa, inativa, competência inválida, extensões/tamanho, envio único, erro/tentar novamente, ready/blocked com issues e resumo retornado. Decimal `123456789012345678901234567890.123456789` aparece literalmente. Duas tabelas paginam 25/50/100; totais não mudam ao paginar e linhas repetidas aparecem separadas.
- [ ] **Step 2 — executar RED:** `npm test -- --run src/test/payrollPreviewApi.test.ts src/test/payrollPreview.test.tsx`; confirmar ausência do fluxo.
- [ ] **Step 3 — implementar cliente:** construir Headers preservando opções existentes; aplicar JSON padrão somente quando body não for FormData e não houver Content-Type explícito. Preservar geração de sessão, refresh compartilhado e erros existentes. FormData pode ser reenviado após refresh porque a prévia não grava.
- [ ] **Step 4 — implementar tela:** reaproveitar estilos/componentes; exibir contexto consultado, empresa/competência detectadas, contagens, totais P/D/E e líquidos, estado bloqueado/avisos. Escolha de colaborador abre suas rubricas. Chaves de linha usam índice na resposta para não eliminar duplicatas. Sem botão de importação definitiva, edição ou armazenamento no navegador. Reiniciar offsets ao mudar limite/seleção/resposta.
- [ ] **Step 5 — verificar contexto:** respostas POST atrasadas após trocar empresa, competência, arquivo, status ou permissão não aparecem; logout/desmontagem cancela e descarta. Seleção de novo arquivo limpa resultado imediatamente. Testar cancelamento sem mensagem de erro no contexto novo. Executar suíte focada, testes existentes de sessão/App e `npm run build`.
- [ ] **Step 6 — commit:** `feat: add temporary payroll preview screen with session upload`.

### Task 5: Navegador, documentação e regressão da entrega

**Files:** criar `web/frontend/e2e/payroll-import-preview.spec.ts` e `web/docs/payroll-import-preview.md`; modificar `web/README.md`, spec para marcar aprovação e plano para registrar conclusão. Capturas novas `web/docs/screenshots/payroll-preview-desktop.png` e `payroll-preview-mobile.png`.

- [ ] **Step 1 — RED:** Playwright com API simulada cobre login, menu Importação Folha, envio de arquivo sintético, resumo e rubricas, contexto divergente, erro seguido de nova tentativa e troca de empresa/competência pendente. Capturar FormData enviado e confirmar MM/YYYY. Mobile 390×844 mantém página dentro da viewport e tabelas com rolagem. Não substituir capturas de módulos anteriores.
- [ ] **Step 2 — executar navegador:** `npm run test:e2e -- e2e/payroll-import-preview.spec.ts` com servidor de teste em porta exclusiva, diferente da instância operacional 5174. Corrigir falhas com teste de regressão correspondente; inspecionar as duas capturas.
- [ ] **Step 3 — documentar:** explicar papéis, comparação de CNPJ/competência, ready versus blocked, limites e erros, descarte de arquivos/prévias, ausência de persistência e homologação pendente. Registrar comandos/resultados e dependência multipart. A API e os testes não devem registrar conteúdo nos erros.
- [ ] **Step 4 — validação final:** backend completo com `sg docker -c 'bash web/backend/tests/run_postgres.sh'` em PostgreSQL descartável; frontend `npm test -- --run`, `npm run build` e Playwright. `pip check`, `git diff --check`, corpus intacto e ausência de migrations. Revisar branch contra a spec e todos os itens de Review Focus; registrar limitações/revisão própria no ledger.
- [ ] **Step 5 — commit:** `test: verify and document payroll upload preview`.

## Autorrevisão e entrega

Contrato/resumo/contexto: Task 1. Arquivos, assinaturas, subprocessos, prazo e
limites: Task 2. Autorização multipart, revalidação e ausência de gravação:
Task 3. Sessão, FormData e contexto visual: Task 4. Uso real no navegador,
capturas e documentação: Task 5. Todos os itens de Review Focus têm testes
nas tarefas indicadas. Mesmos nomes e tipos são usados nas interfaces produtoras
e consumidoras; diferenças entre Decimal interno e string HTTP são explícitas.

Concluir com commits locais e relato dos resultados. Abrir PR quando solicitado,
sem merge automático nem atualização da stack operacional.
