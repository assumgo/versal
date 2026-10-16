# API Versal Folha TXT

Python 3.12+, FastAPI e PostgreSQL 16. Execute os comandos abaixo em `web/backend/`.
O [guia da stack](../README.md) descreve instalação, Docker e migrações.

## Configurar e iniciar

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Configure `DATABASE_URL` e `JWT_SECRET_KEY` (pelo menos 32 caracteres, diferente
da senha do banco) em `.env`. Não versione esse arquivo.

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://localhost:8000/docs. Contrato: http://localhost:8000/openapi.json.
Em `/docs`, faça login com `POST /api/v1/auth/login`, copie `access_token` e use
**Authorize** para informar o Bearer token. Refresh e logout usam cookie HttpOnly;
o refresh token não aparece no JSON. O banco não é criado nem populado ao iniciar a API.

## Primeiro administrador de desenvolvimento

Aplique as migrações antes. O comando exige `ENVIRONMENT=development`, cria os
papéis Administrador, Contador, Operador e Consulta e uma conta ativa com senha
Argon2id. Recebe as credenciais exclusivamente de `FIRST_ADMIN_EMAIL` e
`FIRST_ADMIN_PASSWORD` no ambiente do processo; não há senha padrão.
O e-mail segue a validação do cadastro de usuários e a senha exige 12–1024 caracteres.

Para fornecer os valores no Bash sem gravar a senha no histórico:

```bash
read -r -p 'E-mail do primeiro administrador: ' FIRST_ADMIN_EMAIL
read -r -s -p 'Senha do primeiro administrador: ' FIRST_ADMIN_PASSWORD
export FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD
.venv/bin/python -m app.scripts.seed_admin
unset FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD
```

Configure `ENVIRONMENT=development` em `.env` ou no ambiente. Em produção,
staging ou outro valor o comando retorna código 1 antes de acessar o banco.
Código 0 indica criação ou repetição sem alterações. A repetição para o mesmo
administrador ativo preserva sua senha e não duplica eventos de auditoria.
A criação de uma nova conta é recusada se já houver qualquer usuário. Também
há recusa se o e-mail pertencer a uma conta inativa ou de outro papel. A repetição
para o mesmo administrador ativo continua sem alterações mesmo havendo outros usuários. Não serve para recuperar contas,
reativar usuários ou redefinir senhas; use a administração autenticada.
Papéis, conta e auditoria são confirmados na mesma transação; falhas revertem
as alterações. Execuções simultâneas do bootstrap são serializadas no PostgreSQL.
O evento `user.bootstrap` tem ator nulo por ocorrer antes da primeira sessão.
Nenhuma empresa ou vínculo é criado: o administrador cria empresas pela API e
recebe vínculo ao criá-las, ou concede vínculos explicitamente.

Com Docker, execute na pasta `web/`, após reconstruir a imagem e migrar o banco.
Leia e exporte as duas variáveis acima no shell e use:

```bash
docker compose run --rm -e FIRST_ADMIN_EMAIL -e FIRST_ADMIN_PASSWORD backend python -m app.scripts.seed_admin
unset FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD
```

O Compose configura `ENVIRONMENT=development`. As credenciais não precisam ser
adicionadas ao Compose nem aos arquivos `.env`.

## CORS e autenticação

`FRONTEND_ORIGINS` recebe origens explícitas separadas por vírgula, por exemplo
`http://localhost:5173,http://127.0.0.1:5173`. Cada origem contém protocolo,
host e porta quando necessária, sem caminho, barra final, query ou fragmento.
O padrão é `http://localhost:5173`; valor vazio desabilita acesso entre origens.
Wildcards são rejeitados. CORS permite credenciais, os métodos usados pela API
e os cabeçalhos `Authorization` e `Content-Type`, somente para as origens configuradas.
O frontend deve usar `credentials: 'include'` e access token em memória.
CORS não concede permissão: papel e vínculo por empresa continuam validados no servidor.

## Verificar

```bash
.venv/bin/python -m pytest -q
```

Sem `TEST_DATABASE_URL`, testes PostgreSQL são pulados. Para a verificação
completa, da raiz do repositório:

```bash
bash web/backend/tests/run_postgres.sh
```

O script usa PostgreSQL descartável, verifica upgrade, suíte completa, drift,
downgrade com schema vazio e reaplicação. Nunca use o banco operacional para testes.
O bootstrap não é executado contra a stack por esses testes.

## Migração única dos dados do desktop

O comando `app.scripts.migrate_sqlite` transfere as sete tabelas legadas para um
PostgreSQL já migrado: empresas, colaboradores, rubricas, contas, parâmetros
financeiros, importações e linhas de folha. Não mescla bancos nem substitui dados.
As sete tabelas operacionais do destino devem estar vazias; usuários e papéis web
podem existir. A repetição depois de uma carga é recusada.

Feche o desktop e mantenha-o fechado durante a leitura. Faça e verifique um backup
consistente do SQLite antes de executar. Havendo WAL, preserve o conjunto `.db`,
`.db-wal` e `.db-shm`: copiar somente o `.db` pode perder transações confirmadas.
O comando copia esse conjunto para uma pasta temporária privada, confere hashes
antes/depois e usa o backup SQLite sobre a cópia. Não abre o original com SQLite
nem executa checkpoint nele. Alteração durante a cópia e presença de rollback
journal causam recusa; nesses casos, obtenha uma cópia consistente com o desktop
fechado. O backup da origem continua sendo responsabilidade do operador.

Suspenda escritas na aplicação web durante a carga e configure `DATABASE_URL`
para o destino correto, além de `JWT_SECRET_KEY`, conforme a configuração normal.
Não coloque senha nos argumentos. Em `web/backend/`, primeiro simule:

```bash
.venv/bin/python -m app.scripts.migrate_sqlite \
  --source /home/gabriel/Downloads/VersalFolhaTXT/versal_folha.db \
  --report /tmp/versal-migracao-simulacao.json
```

A simulação verifica a estrutura, os registros e o destino, sem inserir linhas
ou alterar identidades no PostgreSQL. Ela não comprova que uma carga foi realizada.
Revise as contagens, totais e diagnósticos do JSON. Cada relatório deve ter nome
novo, diretório existente e ficar fora de qualquer repositório Git; é criado com
permissão 0600 e nunca sobrescrito. O relatório não contém registros completos,
nomes, documentos ou credenciais. Ainda assim, mantenha-o fora do Git.

Depois de conferir a simulação, efetive a carga:

```bash
.venv/bin/python -m app.scripts.migrate_sqlite \
  --source /home/gabriel/Downloads/VersalFolhaTXT/versal_folha.db \
  --apply --report /tmp/versal-migracao-aplicacao.json
```

Com Docker, na pasta `web/`, reconstrua a imagem e confira as migrações. Monte a
pasta da origem inteira como somente leitura para incluir WAL/SHM:

```bash
docker compose build backend
docker compose run --rm migrate
docker compose run --rm \
  -v /home/gabriel/Downloads/VersalFolhaTXT:/migration:ro \
  backend python -m app.scripts.migrate_sqlite --source /migration/versal_folha.db
```

Para gravar, repita o último comando adicionando `--apply`. Para salvar o relatório
no host, crie antes uma pasta privada fora do repositório e acrescente um volume
`-v /caminho/relatorios:/reports` e `--report /reports/nome-novo.json`.
A configuração de banco do Compose já usa o hostname interno `db`; uma execução
Python no host precisa de um endereço PostgreSQL acessível pelo host.

A aplicação bloqueia escritas nas tabelas de destino, preserva IDs e todos os campos
legados, compara cada campo, contagens e totais por empresa/competência e ajusta
as identidades. Dados e ajustes são confirmados na mesma transação; qualquer
falha anterior ao commit desfaz a carga. Não corrige órfãos ou divergências entre
empresas automaticamente: esses problemas bloqueiam a migração e aparecem por
tabela/ID, sem dados pessoais nas mensagens.

Valores monetários são lidos como texto do SQLite e tratados com `Decimal`, sem
float intermediário nem arredondamento novo. Isso preserva o valor disponível na
origem, mas não recupera precisão já perdida pelo armazenamento REAL do SQLite.
Se converter um REAL para texto perder mais dígitos (sem round-trip idêntico),
a carga é bloqueada em vez de arredondar silenciosamente.
Tabelas adicionais são informadas no relatório e ficam fora do escopo.

Código 0 indica sucesso da simulação ou carga; 1 indica falha; 2 indica argumentos
inválidos. `committed: true` no JSON identifica carga confirmada. Se houver falha
na conexão durante o commit, o resultado será **indeterminado**: confira o destino
antes de repetir. Se apenas o relatório falhar após o commit, a mensagem dirá
**Carga confirmada; falha ao salvar relatório**; não repita a carga.

Não são criados usuários nem vínculos com empresas automaticamente. Conceda
acesso às empresas importadas pela administração existente, inclusive para o
administrador. Nomes históricos de arquivos são mantidos, mas PDFs/planilhas
originais não são enviados ao armazenamento web. Parsers e exportação TXT ficam
fora desta ferramenta.

Os testes usam somente SQLite sintético e PostgreSQL descartável. Nunca adicione
banco real, WAL/SHM, cópias ou relatórios reais ao repositório.
