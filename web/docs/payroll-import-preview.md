# Upload e prévia de Extrato Mensal

Em **Importação Folha** (`/importacao-folha`), selecione a empresa e a competência
no cabeçalho, escolha um PDF, XLS ou XLSX e clique em **Gerar prévia**.
Administrador, Contador e Operador precisam de vínculo com a empresa, que deve
estar ativa. Consulta não pode enviar documentos.

A prévia mostra a empresa e a competência detectadas, colaboradores, rubricas,
contagens e totais. Clique no nome de um colaborador para ver suas rubricas.
As duas listas têm paginação local de 25, 50 ou 100 registros. O resumo sempre
considera todo o resultado, não somente a página visível. No celular, as tabelas
rolam horizontalmente dentro da página.

## Correspondência e avisos

O CNPJ do arquivo deve coincidir com o da empresa selecionada após retirar
pontuação; ambos precisam ter 14 dígitos. A competência detectada deve estar no
formato MM/AAAA válido e coincidir com a selecionada. Ausência/divergência desses
campos, de colaboradores ou de rubricas produz **prévia bloqueada**. A aplicação
não procura outra empresa nem muda os seletores com base no documento.

**Prévia pronta para conferência** significa que essas verificações passaram;
não significa importação, homologação ou aprovação dos valores. Mesmo bloqueada,
a prévia permite conferir os dados lidos do arquivo que o próprio usuário enviou.

Os parsers mantêm os comportamentos do desktop: PDF tem limitações conhecidas
de acentos e captura de CC como código; Excel lê somente a primeira aba e suprime
zeros/duplicatas conforme o legado. Não há OCR. Documento sem movimentos não é
automaticamente considerado válido ou digitalizado. A homologação funcional e
Windows permanece pendente. Veja o [guia dos parsers](desktop-input-formats.md).

Valores e líquidos são texto decimal na API e interface. Os totais são somados
com Decimal sem perda adicional de precisão. O líquido informado é somado uma
vez por colaborador, sem recalcular proventos menos descontos. A prévia preserva
a ordem e a multiplicidade que o parser devolveu.

## Temporários e limites

Arquivo de até 10 MiB, não vazio e com assinatura coerente com a extensão.
O Content-Type do navegador não é usado como comprovação de formato. XLSX deve
ter workbook e declarar até 50 MiB descompactados, sem entradas criptografadas.
Provisões reconhecidas são rejeitadas; esta entrega aceita Extrato Mensal.

A recepção conta bytes efetivos, inclusive sem Content-Length correto. O envelope
multipart tem teto de 10 MiB + 64 KiB. O parser executa em subprocesso por até
30 segundos; há duas vagas de leitura por processo da API, sem fila adicional.
O resultado aceita até 2.000 colaboradores e 10.000 rubricas, sem truncamento.
Esses limites não homologam todos os layouts ou documentos complexos.

O servidor elimina o arquivo temporário ao terminar, em erro, timeout ou
cancelamento. Processos são encerrados e aguardados antes da limpeza. Não são
gravados imports, payroll_lines, colaboradores, rubricas, stored_files ou auditoria
de importação. A prévia fica somente na memória da tela, sem localStorage ou
sessionStorage. Troca de arquivo/empresa/competência, mudança de permissão/status,
logout e saída da tela descartam o contexto e as respostas atrasadas.

## API

`POST /api/v1/companies/{company_id}/payroll-import-preview`, com Bearer token
e multipart com exatamente um `file` e uma `competence` em MM/YYYY. O navegador
deve definir o Content-Type multipart com seu boundary; não enviar como JSON.
A renovação de sessão pode reenviar o FormData, pois a operação não persiste dados.

A resposta 200 contém `company_id`, `requested_competence`, `filename`,
`size_bytes`, `sha256`, `status` (`ready`/`blocked`), `issues`, `summary` e
`statement`. Cada issue tem `code`, `severity` e `message`. O resumo tem
`employees`, `rubrics`, `totals_by_type` (P/D/E) e `net_total`. Statement segue
a saída dos parsers com todos os campos, mas valores monetários textuais.
As respostas de prévia usam `Cache-Control: no-store`.

| HTTP | Significado |
| --- | --- |
| 400 | Arquivo vazio, corrompido ou ilegível |
| 401 / 403 | Sessão inválida ou sem papel/vínculo autorizado |
| 409 | Empresa inativa |
| 413 | Limite de envio, XLSX ou resultado excedido |
| 415 | Extensão, assinatura ou família não suportada |
| 422 | Multipart/competência ausentes, repetidos, extras ou inválidos |
| 503 | Duas leituras em andamento; tentar novamente |
| 504 | Leitura excedeu 30 segundos |

O acesso é revalidado antes da resposta para observar revogações durante a
leitura. Erros públicos não incluem caminhos, stack traces ou mensagens internas
dos leitores. Dados/documentos não são escritos em logs pela implementação.

## Verificação

Dependência adicional de execução: `python-multipart>=0.0.20,<1`. Sem alteração
de esquema. Os testes usam somente fixtures sintéticas e PostgreSQL descartável.

```bash
# Raiz: migrações, regressão, reversão/reaplicação e Alembic check
sg docker -c 'bash web/backend/tests/run_postgres.sh'

# Em web/frontend/
npm test -- --run
npm run build
npm run test:e2e
```

Testes cobrem soma exata, contexto, quatro papéis, revogações em conexão
independente, snapshots de todas as tabelas, limites, subprocessos, cancelamento
e temporários. A interface verifica FormData/refresh, respostas fora de ordem,
paginação e decimais textuais. Playwright usa API simulada e documentos sintéticos.
Capturas: [desktop](screenshots/payroll-preview-desktop.png) e
[mobile](screenshots/payroll-preview-mobile.png).

Validação final em 2026-10-17: 348 testes de backend passaram nas duas execuções
com PostgreSQL 16 descartável; migrações e Alembic check passaram. Frontend:
69 testes, build e todos os 16 testes Playwright passaram. `pip check` e
`git diff --check` passaram. Corpus congelado e capturas anteriores preservados.
As capturas novas foram inspecionadas; a revisão final foi feita pelo autor.

Importação definitiva, substituição de competências, sincronização de cadastros,
histórico persistido de arquivos e exportação TXT exigem uma entrega posterior.
