# Extração dos parsers de Extrato Mensal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, or superpowers:subagent-driven-development only if the user selects delegation. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Ler Extratos Mensais PDF/XLS/XLSX no backend com equivalência integral aos sete casos congelados do desktop.

**Architecture:** Extrair funções independentes de Qt e banco, separando conversão e identificação, parsing de texto/linhas e leitores de arquivos. Expor os dois leitores pelo pacote `app.parsers`; retornar dicionários tipados com Decimal, preservando a referência.

**Tech Stack:** Python 3.12+, pytest, TypedDict, Decimal, pdfplumber 0.11.10, python-calamine 0.9.0, PyMuPDF, pandas, openpyxl e xlrd.

**Spec:** `docs/superpowers/specs/2026-10-17-monthly-statement-parsers-design.md`, aprovada pelo usuário.

## Global Constraints

- Fonte somente leitura: `/home/gabriel/Downloads/versal_folha_txt_v2_18/app.py`; SHA-256 `ab2203e8b0e56550dfcd1baa84e4c6a89618809b06fa9b420d722ea8fc6905c2`.
- Não importar o módulo desktop na aplicação nem depender dele para executar os parsers.
- Sem upload HTTP, interface, persistência, criação de cadastros ou exportação TXT.
- `liquido` e `valor` são Decimal em memória. Preservar conversões e arredondamentos do desktop; não acrescentar conversões monetárias para float.
- Não alterar entradas, esperados ou manifestos congelados para ajustar testes.
- Preservar divergências conhecidas; homologação funcional e Windows permanece pendente.
- Planilha legível sem cabeçalho mantém resultado vazio. Não há OCR.
- Somente PostgreSQL descartável nos testes de integração; nenhum acesso ao banco operacional.

## Review Focus

- EXTRATO MENSAL acompanhado de menção a 13º deve continuar como Extrato (Task 3).
- PDF sem texto não deve acionar fallback por estar vazio (Task 2).
- Falha em ambos os leitores deve propagar erro, sem resultado parcial (Tasks 2/3).
- Segunda aba não deve acrescentar colaboradores à saída (Task 3).
- Importar o pacote não deve carregar Qt ou inicializar banco/configuração (Task 4).

## Preparação

- [x] Confirmar branch e árvore limpas. Usar `feat/proxima-etapa`, já criada pelo usuário a partir da main; não descartar trabalho local nem criar nova branch com o nome de entrega anterior.
- [x] Conferir hash da fonte e ler spec/plano. Executar `.venv/bin/python -m pytest -q` em `web/backend/` para registrar baseline; skips PostgreSQL não equivalem a integração validada.

### Task 1: Parsing puro e contrato tipado

**Files:** criar `web/backend/app/parsers/{__init__,types,common,extrato}.py` e `web/backend/tests/test_extrato_parsing.py`.

**Interfaces:** `types.py` define `ParsedCompany`, `ParsedRubric`, `ParsedEmployee`, `ParsedStatement` como TypedDict com todos os campos da spec. `common.py` expõe `br_to_decimal(value: object) -> Decimal`, `parse_company_from_text(text: str) -> ParsedCompany` e auxiliares de células. `extrato.py` expõe `parse_extrato_text(text: str) -> ParsedStatement` e `parse_extrato_rows(rows: list[list[object]]) -> ParsedStatement`.

- [x] **Step 1 — RED:** criar casos sintéticos em memória para competência, CNPJ/código/razão, zeros à esquerda, negativos e Decimal. `test_rows_preserve_duplicate_and_zero_behavior` fixa supressão de mesmo código/valor e de zero, preservando mesmo código com valor diferente. `test_text_preserves_known_accent_and_cc_discrepancies` fixa SALÁRIO omitido e CC capturado como código na estrutura documentada; comparar campos, não apenas totais. `test_empty_text_and_rows_keep_desktop_shape` fixa campos vazios e `tipo_importacao == 'Extrato'`.
- [x] **Step 2 — executar RED:** `.venv/bin/python -m pytest tests/test_extrato_parsing.py -q`; confirmar falha por ausência dos módulos.
- [x] **Step 3 — implementar:** copiar somente as funções selecionadas e seus auxiliares transitivos do desktop, adicionando tipos/imports explícitos e documentação de procedência/hash. Manter ordem, flags, regex, arredondamento e decisão de empresa exatamente como referência. Não reescrever regras com base nas fixtures.
- [x] **Step 4 — GREEN:** repetir testes focados e `tests/test_parser_corpus.py`; todos devem passar sem mudar corpus.
- [x] **Step 5 — commit:** `feat: extract pure monthly statement parsing`.

### Task 2: Leitor PDF e equivalência de arquivos

**Files:** criar `web/backend/app/parsers/pdf.py`, `web/backend/tests/test_extrato_pdf.py`; modificar `web/backend/requirements.txt` e `web/backend/app/parsers/__init__.py`.

**Interfaces:** `pdf.parse_pdf(path: str | Path) -> ParsedStatement`; reexportar pelo pacote. Consome `extrato.parse_extrato_text`. Dependências: `pdfplumber==0.11.10` e `PyMuPDF>=1.24.10,<2`.

- [x] **Step 1 — RED:** `test_pdf_matches_frozen_reference` parametrizado com `extrato_pdf`, `extrato_pdf_accent`, `extrato_pdf_empty`: serializar exclusivamente Decimal como texto e comparar JSON integral ordenado; afirmar tipos Decimal na saída não vazia. `test_pdf_fallback_reads_when_primary_fails` provoca falha de pdfplumber e verifica leitura real com PyMuPDF e parsing do texto produzido por ele. `test_empty_pdf_text_does_not_trigger_fallback` simula páginas sem texto e verifica ausência de chamada ao fallback. `test_pdf_propagates_failure_when_both_readers_fail` verifica exceção final e nenhum resultado parcial.
- [x] **Step 2 — executar RED:** instalar dependências declaradas na venv e executar `.venv/bin/python -m pytest tests/test_extrato_pdf.py -q`; confirmar falha por leitor ausente, distinguindo erro de instalação.
- [x] **Step 3 — implementar:** mesmo fluxo de exceções e parâmetros `extract_text(x_tolerance=1, y_tolerance=3)` da referência. Fechar documentos de ambos os leitores, inclusive em erro. Não acionar fallback por string vazia nem acrescentar OCR.
- [x] **Step 4 — GREEN:** executar testes PDF e parsing puro; exigir igualdade integral dos três esperados PDF e comportamento dos fallbacks.
- [x] **Step 5 — commit:** `feat: add desktop-compatible monthly PDF reader`.

### Task 3: Leitor XLS/XLSX limitado ao Extrato

**Files:** criar `web/backend/app/parsers/excel.py`, `web/backend/app/parsers/errors.py`, `web/backend/tests/test_extrato_excel.py`; modificar `web/backend/requirements.txt` e `web/backend/app/parsers/__init__.py`.

**Interfaces:** `excel.parse_excel(path: str | Path) -> ParsedStatement`; `errors.UnsupportedLayoutError(ValueError)` para provisões. Reexportar leitor e erro pelo pacote. Consome `extrato.parse_extrato_rows` e auxiliares da Task 1. Dependências: `python-calamine==0.9.0`, `pandas>=2.2.3,<3`, `openpyxl>=3.1.5,<4`, `xlrd>=2.0.1,<3`.

- [x] **Step 1 — RED:** `test_excel_matches_frozen_reference` cobre `extrato_xls`, `extrato_xlsx`, `extrato_xlsx_edge`, `extrato_xlsx_empty` com comparação integral e Decimal. `test_excel_fallback_matches_reference` força falha calamine para XLS e XLSX reais e compara resultado com esperado congelado. `test_excel_propagates_failure_when_both_readers_fail` fixa ausência de saída parcial. Gerar planilhas sintéticas temporárias para `test_excel_uses_first_sheet_only`, `test_extrato_title_takes_precedence_over_thirteenth_salary` e `test_provision_layouts_are_rejected` (13º/férias e variantes de título previstas no desktop).
- [x] **Step 2 — executar RED:** instalar dependências declaradas e executar `.venv/bin/python -m pytest tests/test_extrato_excel.py -q`; falha deve indicar ausência da interface ou comportamento.
- [x] **Step 3 — implementar:** calamine primeira aba, fallback pandas `header=None, dtype=object` com `fillna('')`, mesmas primeiras 120 linhas para identificação e prioridade original de títulos. Onde o desktop chamaria provisões, lançar `UnsupportedLayoutError`; manter fallback ao parsing de Extrato para planilha legível sem título. Não capturar o erro de layout como erro do leitor. Fechar workbooks quando o leitor disponibilizar fechamento.
- [x] **Step 4 — GREEN:** executar suíte dos três módulos e integridade do corpus; sete casos devem passar com igualdade integral. Confirmar fallbacks sem alterar decisões de parsing.
- [x] **Step 5 — commit:** `feat: add monthly Excel reader with explicit layout limits`.

### Task 4: Independência, documentação e regressões

**Files:** criar `web/backend/tests/test_parser_isolation.py`; modificar `web/docs/desktop-input-formats.md`, `web/backend/tests/fixtures/README.md` e `web/README.md`.

**Interfaces:** interface pública final: `from app.parsers import parse_pdf, parse_excel, UnsupportedLayoutError`; saída `ParsedStatement` da Task 1.

- [x] **Step 1 — RED:** `test_parsers_run_without_desktop_qt_or_database` usa subprocesso Python com bloqueio explícito de imports PySide6, app.core e sqlalchemy; importar pacote e ler uma fixture PDF e XLSX sem importar fonte externa. Verificar Decimal e nenhuma dependência desktop na execução. `test_parsers_do_not_modify_input_files` compara hashes antes/depois da leitura de PDF/XLS/XLSX temporários.
- [x] **Step 2 — executar RED:** executar teste de isolamento e verificar que o teste detecta dependência indevida se existir; se já passar, registrar verificação arquitetural sem fabricar regressão no código.
- [x] **Step 3 — documentar:** descrever API Python, campos/Decimal, bibliotecas instaladas e comandos reproduzíveis. Atualizar afirmações de que ainda não existe parser web, mantendo explícitas ausência de upload/persistência/TXT e homologação pendente. Não modificar manifesto de aprovação.
- [x] **Step 4 — verificar:** executar `.venv/bin/python -m pytest -q` e `bash web/backend/tests/run_postgres.sh` (da raiz, banco descartável) para regressão completa. Registrar contagens, skips, versões dos sete leitores e resultado dos sete casos. Executar `git diff --check`, verificar ausência de mudanças nos binários/esperados/manifestos e revisar a branch contra a spec. Não alterar stack operacional ou frontend.
- [x] **Step 5 — commit:** `docs: document monthly parser API and verification`.

## Autorrevisão do plano

Contrato e conversões: Task 1. Leitores, fallbacks e arquivos reais sintéticos:
Tasks 2/3. Limites de provisão/abas: Task 3. Independência, imutabilidade e guias:
Task 4. Casos do Review Focus têm testes explícitos nas tarefas indicadas.
Assinaturas e Decimal permanecem iguais nas quatro tarefas. Não há migração,
mudança de endpoint ou alteração de referência prevista.

## Entrega

Concluir com commits locais e relatório dos resultados/limites. Publicação de
branch/PR pode ser feita se solicitada; nenhuma atualização operacional é
necessária para esta extração sem endpoints. Revisão com agente separado
somente se o usuário escolher ou autorizar delegação.
