# Instância local para conversão e conferência

Execute os blocos no mesmo terminal Bash, na pasta `web/` de um checkout que
contenha `app.scripts.migrate_sqlite`. Requer Docker Engine com Compose v2 e
Python 3 no host. O projeto Compose `versal-conversao` tem volume próprio e usa
as portas 8001 e 5174. Os dados persistem em `versal-conversao_postgres_data`.
Não use esse procedimento para mesclar ou substituir um banco já populado.

## Preparar a configuração e o esquema

```bash
dc() { docker compose -p versal-conversao "$@"; }

python3 - <<'PY'
from pathlib import Path
import secrets

path = Path('.env')
if not path.exists():
    with path.open('x') as file:
        file.write(
            'POSTGRES_DB=versal_folha\n'
            'POSTGRES_USER=versal\n'
            f'POSTGRES_PASSWORD={secrets.token_hex(32)}\n'
            f'JWT_SECRET_KEY={secrets.token_hex(32)}\n'
            'BACKEND_PORT=8001\n'
            'FRONTEND_PORT=5174\n'
        )
    path.chmod(0o600)
PY

export BACKEND_PORT=8001 FRONTEND_PORT=5174
dc config --quiet
dc build backend migrate frontend
dc up -d --wait db
dc run --rm migrate
```

O script preserva um `.env` existente; nele, `POSTGRES_PASSWORD` e
`JWT_SECRET_KEY` precisam estar preenchidos e ser distintos. A chave JWT exige
pelo menos 32 caracteres. Não altere a senha de um volume PostgreSQL já inicializado
apenas editando `.env`. As variáveis exportadas fixam as portas nesta sessão;
em outro terminal, exporte-as novamente ou mantenha esses valores no `.env`.
A API e o frontend ainda não são iniciados: a carga acontece antes de liberar a
aplicação para escrita.

## Copiar a origem com o desktop fechado

Feche o desktop e mantenha-o fechado até terminar a cópia. Ajuste o caminho da
origem se necessário. Preserve DB/WAL/SHM juntos; não copie somente o `.db` se
houver WAL. Guarde também um backup verificado em local durável antes de qualquer
substituição do desktop; a pasta temporária abaixo é uma cópia de trabalho.

```bash
backup_dir=$(mktemp -d "${TMPDIR:-/tmp}/versal-origem.XXXXXX")
cp -a /home/gabriel/Downloads/VersalFolhaTXT "$backup_dir/"
reports_dir=$(mktemp -d "${TMPDIR:-/tmp}/versal-relatorios.XXXXXX")
```

## Simular e depois aplicar

A função abaixo preserva o código de saída do migrador. Mensagens vão para stderr;
o JSON é criado dentro do container e recuperado por stdout. O redirecionamento
no host usa permissão privada e recusa sobrescrever um arquivo existente. Assim
o relatório é legível pelo usuário do host mesmo se Docker usar outro UID.
A origem inteira é montada somente para leitura.

```bash
migration_report() {
  dc run --rm --no-deps -T \
    -v "$backup_dir/VersalFolhaTXT:/migration:ro" \
    backend sh -c '
      python -m app.scripts.migrate_sqlite \
        --source /migration/versal_folha.db --report /tmp/report.json "$@" >&2
      result=$?
      if [ -f /tmp/report.json ]; then
        cat /tmp/report.json || exit 1
      else
        exit 1
      fi
      exit "$result"
    ' sh "$@"
}

(umask 077; set -C; migration_report > "$reports_dir/simulacao.json")
cat "$reports_dir/simulacao.json"
```

Prossiga somente se a simulação terminar com código 0 e as contagens/totais
estiverem corretos. A simulação não grava no destino.

```bash
(umask 077; set -C; migration_report --apply > "$reports_dir/aplicacao.json")
cat "$reports_dir/aplicacao.json"
```

Sucesso na carga exige `status: "ok"` e `committed: true`. A conferência compara
cada campo legado, contagens e totais, e o ajuste dos geradores de IDs é
transacional. Se aparecer `commit_unknown`, confira o destino antes de repetir.
Se o relatório ou o terminal falhar após confirmação, não repita a carga.
Uma nova execução com tabelas populadas é recusada.

Se já houver um relatório num volume com proprietário diferente, leia-o dentro
do container com `cat /caminho/do/relatorio.json` usando o mesmo volume e usuário
que o criou; redirecione a saída para um arquivo novo no host com `umask 077`.
Não use `chmod 644` para expor os arquivos nem adicione relatórios ao Git.

## Criar o administrador e iniciar a aplicação

Se já houver usuários, preserve suas credenciais e pule o bootstrap. Para um
banco sem usuários, forneça e-mail e senha de pelo menos 12 caracteres:

```bash
read -r -p 'E-mail do administrador: ' FIRST_ADMIN_EMAIL
read -r -s -p 'Senha: ' FIRST_ADMIN_PASSWORD
export FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD

dc run --rm --no-deps \
  -e FIRST_ADMIN_EMAIL -e FIRST_ADMIN_PASSWORD \
  backend python -m app.scripts.seed_admin

unset FIRST_ADMIN_EMAIL FIRST_ADMIN_PASSWORD

dc up -d --wait --wait-timeout 180
dc ps -a
```

Acesse `http://localhost:5174` e `http://localhost:8001/docs`. Banco, API e
frontend devem estar saudáveis; o serviço `migrate` terminar com código 0 é esperado.

O administrador também precisa de vínculo explícito com a empresa importada.
Em `/docs`, execute `POST /api/v1/auth/login`, use o access token no botão
**Authorize**, consulte seu ID em `GET /api/v1/auth/me` e conceda o vínculo com
`PUT /api/v1/users/{user_id}/companies/{company_id}`. Para consultar somente os
IDs das empresas, sem expor nomes/documentos no terminal:

```bash
dc exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id FROM companies ORDER BY id;"'
```

Depois, `GET /api/v1/companies` deve retornar a empresa e a tela web deve permitir
selecioná-la. Tokens, senhas e credenciais ficam fora do repositório.

## Retomar e diagnosticar

Em outro terminal, entre no mesmo checkout/pasta `web/`, defina `dc` e as portas
como no primeiro bloco. Para retomar, verificar e consultar falhas:

```bash
dc up -d --wait --wait-timeout 180
dc ps -a
dc logs --tail=80 migrate backend frontend
```

Revise logs localmente antes de compartilhá-los, pois requisições podem conter
informações do ambiente. Para parar preservando o volume do PostgreSQL:

```bash
dc down
```

Não use `down -v` na instância com dados migrados. Atualizações de frontend/API
exigem reconstruir as imagens; não exigem repetir a conversão do SQLite.
