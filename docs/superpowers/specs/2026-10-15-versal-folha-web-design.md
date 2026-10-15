# Versal Folha TXT Web — Design da Fase 1

## Objetivo

Criar a fundação web multiusuário do Versal Folha TXT sem alterar o desktop em `C:\Folhas2_18\versal_folha_txt_v2_18`. A fase 1 entrega acesso autenticado, isolamento por empresa, cadastros iniciais, auditoria, interface visualmente fiel ao PySide6 e ambiente local reproduzível.

## Decisões e restrições

- Frontend: React, TypeScript e Vite.
- Backend: Python e FastAPI, com API versionada em `/api/v1`.
- Persistência: PostgreSQL, SQLAlchemy 2.x e Alembic.
- Senhas: hash Argon2; nunca armazenar senha, refresh token ou segredo JWT em texto puro.
- Sessão: access token JWT de curta duração em memória; refresh token rotativo em cookie `HttpOnly`, `SameSite=Lax`, `Secure` em produção, com hash e revogação no banco.
- Dados operacionais devem permanecer segregados por empresa e competência. O servidor valida o vínculo do usuário em toda rota com `company_id`.
- Valores monetários usam `NUMERIC`; não usar `float`.
- O desktop e seu SQLite permanecem em produção durante toda a migração.

## Arquitetura

`frontend` consome `backend`; o backend aplica autenticação, RBAC e autorização por empresa antes de chamar serviços e repositórios SQLAlchemy. PostgreSQL é o único banco da nova aplicação. Armazenamento físico de arquivos é uma abstração configurável e os metadados ficam em `stored_files`.

O backend será organizado em `api`, `core`, `models`, `schemas`, `services`, `repositories` e `parsers`. Os parsers permanecem fora da fase 1: a pasta `parsers` estabelece a fronteira para extrações futuras de `app.py`.

## Modelo de dados inicial

| Entidade | Responsabilidade |
| --- | --- |
| `roles`, `users`, `refresh_tokens` | identidade, papel e ciclo de sessão revogável |
| `companies`, `user_companies` | empresas e escopo de cada usuário |
| `employees` | colaboradores por empresa |
| `rubrics`, `chart_accounts`, `finance_params` | parâmetros contábeis e financeiros por empresa |
| `imports`, `payroll_lines`, `stored_files` | base para histórico de importações e movimentos |
| `audit_logs` | rastreabilidade de mutações, importações e exportações |

As tabelas operacionais possuem chaves estrangeiras para empresa, timestamps UTC e índices para empresa/competência. Empresas são inativadas em vez de removidas quando houver histórico.

## Papéis

- **Administrador:** usuários, papéis, empresas, permissões e backup.
- **Contador:** rubricas, plano de contas, validações e exportações.
- **Operador:** importação e colaboradores.
- **Consulta:** leitura apenas.

Um papel define o que pode ser feito; `user_companies` define em quais empresas pode ser feito.

## API da fase 1

- `GET /health`
- `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`
- CRUD administrativo de usuários e seus vínculos com empresas
- CRUD de empresas dentro do escopo permitido
- CRUD de colaboradores dentro da empresa autorizada
- listagem das empresas autorizadas e competências disponíveis

Criações, atualizações e exclusões geram auditoria com ator, empresa, ação, entidade, identificador, metadados permitidos, IP e data. Futuras importações/exportações usarão a mesma trilha.

## Interface

A web mantém a identidade desktop observada em `app.py`: logo e ícone existentes, verde escuro `#315f2f`, verde claro `#89bf21`, fundo `#f7faf5`, borda `#cfdccc`, controles compactos e tabelas operacionais.

O shell contém sidebar fixa com Dashboard, Empresas, Colaboradores, Importação Folha, Plano de Contas, Rubricas, Encargos da Empresa, Parametrização Contábil, Parametrização Financeira, Exportação TXT e Backup; cabeçalho com empresa e competência; e área de conteúdo rolável. Componentes reutilizáveis: `Sidebar`, `Header`, `StatCard`, `DataTable`, `FormField`, `ConfirmModal`, `Alert` e `LoadingState`.

No celular, um botão de menu abre a sidebar como drawer sobre o conteúdo, com fechamento por item, botão próprio ou clique fora. Em telas médias, a sidebar pode recolher a ícones. Tabelas preservam todas as colunas com rolagem horizontal.

## Testes e qualidade

Testes de backend cobrem login, refresh, logout, `/me`, hash de senha, RBAC, acesso autorizado e bloqueio entre empresas. Testes de frontend cobrem rota protegida, estados de carregamento/erro/sem permissão e renderização inicial dos cadastros. O Compose deve subir frontend, API e PostgreSQL.

## Migração de regras do desktop

Antes de transportar qualquer parser ou exportador, criar fixtures anonimizadas de PDF/XLS/XLSX e saídas TXT. Os testes de equivalência devem comparar empresa, competência, colaboradores, rubricas, valores e o TXT em layout fixo quando aplicável. A extração começa por funções puras do `app.py`; a operação web entra em modo de conferência antes de substituir qualquer fluxo do desktop.

## Fora de escopo da fase 1

Não migrar nem reescrever parsers PDF/XLS/XLSX, importações completas, validação contábil completa, exportação Siagri/Aliare, backup/restauração operacional nem migrar automaticamente o SQLite existente. A fase 1 prepara suas interfaces e documentação de equivalência.
