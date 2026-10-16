# SQLite para PostgreSQL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution, or superpowers:subagent-driven-development if the user chooses delegation. Track steps with checkboxes.

**Goal:** Entregar um comando de migração única com simulação, aplicação atômica e conferência integral.

**Architecture:** Separar fotografia/validação SQLite, transferência/conferência PostgreSQL e interface CLI. Usar SQLAlchemy Core e sqlite3; aproveitar os modelos e a configuração existentes, sem mudanças de esquema.

**Tech Stack:** Python 3.12+, sqlite3, Decimal, SQLAlchemy 2, psycopg, PostgreSQL 16, pytest.

**Spec:** `docs/superpowers/specs/2026-10-16-sqlite-postgres-migration-design.md` (aprovada).

## Global Constraints

- Simulação por padrão; escrita apenas com `--apply`.
- Exigir as sete tabelas operacionais vazias; nunca mesclar ou apagar dados.
- Não versionar banco real, WAL, SHM, cópias nem relatórios reais.
- Preservar campos legados, IDs, nulos, vínculos e decimais, sem correções silenciosas.
- Usar somente PostgreSQL descartável nos testes; nenhuma carga real nesta execução.
- Não criar usuários/vínculos nem migrar arquivos originais.

## Review Focus

- WAL com transação confirmada deve entrar na fotografia; origem e arquivos auxiliares permanecem intactos (Task 1).
- SQLite aceita valores com tipos inesperados: recusar incompatibilidades, inclusive NUL em texto, antes de gravar (Task 1).
- Falha após ajuste do gerador de IDs deve desfazer linhas e reinício da identidade (Task 2).
- Duas aplicações simultâneas devem resultar em apenas uma carga, sem duplicação (Task 2).
- Erro no relatório após commit deve indicar carga confirmada, sem expor parâmetros SQL ou credenciais (Task 3).

## Estrutura de arquivos

- `app/migration/__init__.py`: fronteira do módulo.
- `app/migration/source.py`: contrato legado explícito, fotografia, leitura tipada e validação da origem.
- `app/migration/transfer.py`: preflight PostgreSQL, transação, cópia e conferência.
- `app/scripts/migrate_sqlite.py`: argumentos, configuração, mensagens e relatório.
- `tests/test_migration_source.py`: SQLite sintético e WAL.
- `tests/test_migration_transfer.py`: integração PostgreSQL descartável.
- `tests/test_migrate_sqlite.py`: CLI e relatórios.
- Atualizar `.gitignore`, `web/backend/README.md` e `web/docs/legacy-schema-compatibility.md`.

Todos os caminhos `app/` e `tests/` desta seção são relativos a `web/backend/`.

### Task 1: Fotografia e validação da origem

**Interfaces:** `snapshot(source: Path) -> AbstractContextManager[sqlite3.Connection]`;
`validate_source(db: sqlite3.Connection) -> dict`;
`iter_rows(db: sqlite3.Connection, table: str) -> Iterator[dict]`.
Exportar `TABLE_COLUMNS: dict[str, tuple[str, ...]]` na ordem de carga e
`MigrationError(Exception)` com mensagens sem conteúdo pessoal.
O resumo usa apenas tipos JSON, IDs de diagnóstico e decimais como strings.

- [x] Escrever `tests/test_migration_source.py` com esquema da fixture legado e registros sintéticos: preservar nulo, duplicatas e texto formatado; ler `0.1` como `Decimal('0.1')`; incluir INSERT confirmado em WAL ainda aberto e conferir hashes da origem/WAL/SHM antes e depois. Testar arquivo ausente/inválido, colunas faltantes/extras, tabelas adicionais informadas, órfãos e empresa divergente, NUL, inteiro fora do domínio, tipos monetários inválidos e ID máximo sem sucessor.
- [x] Executar `.venv/bin/python -m pytest tests/test_migration_source.py -q` e confirmar falha por módulo ausente.
- [x] Implementar `source.py`: URI somente leitura com caminho escapado; backup em pasta temporária; `quick_check`; contrato explícito de colunas/tipos; validação de referências conforme semântica nula das FKs. NUMERIC via `CAST(... AS TEXT)` e Decimal finito; nenhum float intermediário. Não usar `immutable`; encerrar conexões e remover temporários em sucesso/falha. Incluir contagens e totais por empresa/competência no resumo.
- [x] Reexecutar a suíte específica e confirmar aprovação sem acesso ao banco real.
- [x] Revisar o diff e registrar apenas código e fixtures sintéticas: `feat: validate legacy SQLite migration source`.

### Task 2: Transferência e conferência PostgreSQL

**Interfaces:** consumir Task 1; produzir
`migrate(source: Path, engine: Engine, *, apply: bool = False) -> dict`.
Retornar modo, versão do comando, contagens/totais, tabelas fora de escopo e
`committed: bool`. Não retornar linhas ou URL de conexão.

- [x] Escrever `tests/test_migration_transfer.py` usando exclusivamente `TEST_DATABASE_URL`, com limpeza/transações isoladas que não interfiram nos demais testes. Exercitar todas as sete tabelas e campos, incluindo negativos, nulos e precisão monetária; simulação deixa tabelas e identidades intactas; aplicação confere cada campo; inserir sem ID depois da carga gera sucessor correto.
- [x] Adicionar testes de destino não PostgreSQL, revisão Alembic desatualizada, destino ocupado e repetição; erro injetado após reinício da identidade reverte dados e gerador; divergência injetada de campo/totais impede commit. Duas conexões reais devem comprovar bloqueio: segunda aplicação espera e depois recusa destino ocupado. Usuários/vínculos existentes permanecem intactos.
- [x] Executar a suíte nova em banco descartável e confirmar falha pela implementação ausente.
- [x] Implementar `transfer.py`: verificar Alembic via ScriptDirectory e revisão atual; inspecionar colunas/tipos/FKs do destino. Simulação usa transação somente leitura. Aplicação bloqueia tabelas em ordem fixa com `SHARE ROW EXCLUSIVE`, verifica vazio sob lock, insere lotes de até 1000 linhas com Core e compara campos em ordem de ID sem carregar todo o banco em memória. Recalcular contagens/totais no destino com Decimal. Ajustar identidade com `ALTER TABLE ... ALTER COLUMN id RESTART WITH`, usando identificadores exclusivamente da lista constante e inteiro validado; confirmar tudo numa transação. Rollback em qualquer falha.
- [x] Executar `bash web/backend/tests/run_postgres.sh` na raiz e confirmar testes, downgrade/reupgrade e `alembic check` sem diferenças.
- [x] Revisar o diff e registrar `feat: migrate legacy payroll data atomically`.

### Task 3: CLI, relatório e instruções

**Interfaces:** consumir `migrate`; produzir `main(argv: list[str] | None = None) -> int`
em `app/scripts/migrate_sqlite.py`. Opções `--source` obrigatório, `--apply` e
`--report`; configuração via `get_settings()` e `get_engine()` existentes.

- [x] Escrever `tests/test_migrate_sqlite.py`: aplicação nunca é padrão; flags inválidas retornam 2; configuração ou validação inválida retornam 1; sucesso retorna 0. Relatório existente, caminho dentro do repositório, coincidência com origem/WAL/SHM e diretório inválido são recusados antes da carga. Mensagens de SQLAlchemy não revelam senha, CPF ou parâmetros. Falha de escrita após commit retorna 1 e imprime explicitamente `Carga confirmada; falha ao salvar relatório`. Erro anterior a commit informa ausência de carga confirmada.
- [x] Executar `.venv/bin/python -m pytest tests/test_migrate_sqlite.py -q` e confirmar falha inicial.
- [x] Implementar CLI e serialização JSON: reservar arquivo de relatório sem sobrescrita antes da carga, permissão 0600, concluir escrita com status explícito. Remover reserva vazia se houver falha anterior à execução; falhas posteriores conservam diagnóstico sanitizado. `committed` verdadeiro só após retorno bem-sucedido do commit; erro de conexão durante commit informa resultado indeterminado e exige conferência antes de repetir. Imprimir resumo sem dados pessoais. Nunca capturar KeyboardInterrupt como sucesso.
- [x] Adicionar ignores `*.sqlite`, `*.sqlite3`, `*.db-wal`, `*.db-shm`, `*.sqlite-wal`, `*.sqlite-shm`, `*.sqlite3-wal`, `*.sqlite3-shm`. Documentar fechamento do desktop, backup consistente, destino preparado/vazio, comandos de simulação/aplicação/relatório, ausência de migração de arquivos e concessão posterior de vínculos por empresa. Atualizar contrato que hoje declara ausência de importador.
- [x] Executar suíte unitária e `bash web/backend/tests/run_postgres.sh`; conferir `--help` e `git diff --check`. Inspecionar arquivos staged para impedir inclusão de dados reais. Não aplicar a migração no banco da aplicação.
- [x] Revisar o conjunto e registrar `feat: expose one-time SQLite migration command`.

## Revisão do plano

Cobertura: fotografia, esquema/tipos e diagnósticos na Task 1; atomicidade,
concorrência, valores e identidades na Task 2; CLI, relatórios, privacidade e guia
na Task 3. Interfaces usam somente conexão SQLite, Engine, Path e dicionários
serializáveis; Decimal permanece interno e vira string nos relatórios.
Nenhuma dependência nova ou alteração dos modelos é necessária.

## Registro de execução

Implementação em `feat/sqlite-postgres-migration`, worktree
`/tmp/versal-sqlite-migration`. Testes de regressão: 49 aprovados em PostgreSQL
descartável. Revisão independente encontrou quatro problemas importantes, todos
reproduzidos com testes falhando antes das correções: precisão REAL/texto, colunas
geradas, IDs fora do esquema rowid e falha de saída após commit. Nenhuma pendência
de revisão foi adiada. A origem real passou pela validação somente leitura, sem
carga no destino e sem inclusão no repositório.

A fotografia foi refinada para copiar e verificar DB/WAL/SHM antes de abrir
SQLite, evitando qualquer atualização de SHM na origem. Relatórios de falha são
preservados com diagnóstico sanitizado. REAL sem roundtrip textual é recusado
para impedir perda adicional. Commits das três tarefas são feitos após validação
do conjunto.
