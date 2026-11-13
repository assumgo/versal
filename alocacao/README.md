# Alocação de Recursos

Sistema da Versal Agro Contabilidade para controle de estoque de equipamentos:
entrada por nota fiscal ou avulsa, alocação a colaboradores e emissão de TRE
(Termo de Responsabilidade de Equipamento) na entrega e na devolução.

## Stack

- Frontend: React 19 + TypeScript + Vite (porta `5174`)
- Backend: FastAPI (porta `8001`)
- Autenticação: Microsoft Entra ID / Azure AD (MSAL)
- Temas: claro e escuro

## Estrutura

```
alocacao/
  frontend/   # UI (login, dashboard, menus)
  backend/    # API inicial
  docs/       # referências visuais e logos fonte
```

## Menus

- Cadastros
- Configurações
- Notas Fiscais
- TREs
- Alocações
- Equipamentos

## Frontend

```bash
cd alocacao/frontend
cp .env.example .env
yarn install
yarn dev
```

> Prefer `yarn` neste projeto. Em alguns ambientes o `npm install` falha na
> resolução de peers do Vitest.

Abra `http://localhost:5174`.

### Azure AD / Microsoft 365

Preencha no `.env` do frontend:

- `VITE_AZURE_CLIENT_ID`
- `VITE_AZURE_TENANT_ID`
- `VITE_AZURE_REDIRECT_URI` (ex.: `http://localhost:5174`)

No Entra ID, registre um app SPA com redirect URI igual ao acima e permissão
delegada `User.Read`.

Enquanto o Azure não estiver configurado, `VITE_ALLOW_DEV_LOGIN=true` permite
entrar localmente para validar a UI.

## Backend

```bash
cd alocacao/backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --reload --port 8001
```

- Health: `GET /health`
- Meta: `GET /api/meta`
- Resumo: `GET /api/dashboard/summary`

## Logos

- `frontend/public/logo1.png` — logo completa (sidebar/login)
- `frontend/public/logo2.png` — marca reduzida
- `frontend/public/favicon.png` — favicon

## Cadastros (submenus)

- `/cadastros/categorias` — CRUD de categorias (seed: Notebook, Monitor, Periféricos, Rede, Desktop, Servidor)
- `/cadastros/colaboradores` — CRUD (Nome, E-mail pessoal, CPF, Data nascimento, Celular)
- `/cadastros/fornecedores` — CRUD (Razão social, Nome fantasia, CNPJ/CPF)

APIs: `/api/categorias`, `/api/colaboradores`, `/api/fornecedores`  
Persistência local SQLite em `backend/data/alocacao.db`.

## Próximos passos

1. Persistência PostgreSQL (equipamentos, NFs, alocações, TREs)
2. Validação de token Entra ID no backend
3. Fluxos completos de entrada, alocação e emissão de TRE

