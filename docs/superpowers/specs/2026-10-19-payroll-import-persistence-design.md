# Persistência da importação de folha

Status: proposta para revisão do usuário, 2026-10-19.

## Objetivo

Permitir que um usuário autorizado confirme uma prévia pronta de Extrato Mensal
e grave os movimentos da folha por empresa e competência. A gravação cria um
registro em `imports`, linhas em `payroll_lines`, metadados de origem e uma
entrada de auditoria na mesma transação. A operação não atualiza os cadastros
de colaboradores ou rubricas.

Esta etapa não substitui o desktop nem certifica equivalência funcional. A
homologação Windows e funcional continua necessária antes de importar dados de
produção.

## Fluxo

1. O usuário seleciona arquivo, empresa e competência e gera a prévia existente.
2. Se a prévia estiver pronta, a tela mantém o objeto `File` somente em memória
   até a confirmação ou descarte.
3. Ao confirmar, o navegador envia novamente o arquivo, empresa/competência pela
   rota e o SHA-256 da prévia apresentada.
4. A API recebe e valida o arquivo com os mesmos limites da prévia, calcula o
   SHA-256, executa o parser novamente e confirma que o hash, empresa detectada
   e competência detectada correspondem à prévia pronta.
5. Depois do parsing, a API revalida usuário, vínculo e empresa ativa. Em uma
   transação curta, bloqueia a linha da empresa, consulta duplicidade e grava
   importação, linhas, metadados e auditoria.
6. Só depois do commit a API responde sucesso. A tela descarta arquivo e prévia
   e mostra a importação persistida.

Não há token de prévia nem arquivo guardado entre as requisições. Uma resposta
atrasada ou alteração do arquivo/contexto não pode confirmar conteúdo diferente
do que foi exibido.

## Regras de negócio

- Administrador, Contador e Operador podem importar em empresa ativa à qual
  tenham vínculo. Consulta não pode importar.
- A empresa e a competência detectadas devem corresponder às selecionadas. Uma
  prévia bloqueada nunca pode ser confirmada.
- Se já existir qualquer registro de importação para a mesma empresa e
  competência, a confirmação retorna 409. Não substituir, apagar ou mesclar
  movimentos existentes. Substituição exige uma ação explícita em entrega
  posterior.
- O bloqueio transacional da empresa serializa confirmações simultâneas para a
  mesma empresa. A consulta de duplicidade ocorre depois do lock e dentro da
  transação que cria os registros.
- Cada rubrica retornada pelo parser cria uma linha em `payroll_lines`, mantendo
  ordem, multiplicidade, textos e valores Decimal sem arredondamento adicional.
  Não deduplicar novamente.
- Cada linha recebe `cpf`, `nome`, `cargo`, `codigo_verba`, `verba`, `referencia`,
  `valor`, `tipo` e o `liquido` informado para seu colaborador. O campo
  `liquido` repete o valor por linha, conforme a estrutura atual de
  `payroll_lines`; consumidores que totalizam líquido devem fazê-lo por
  colaborador, não somando todas as linhas. **Assunção a confirmar na revisão
  funcional e na comparação Windows:** esse é o comportamento da referência
  desktop para múltiplas rubricas do mesmo colaborador.
- O registro `imports` usa `competencia` MM/YYYY, nome seguro do arquivo,
  `data_hora` UTC e estado `Concluída`. O ator fica em `created_by_id`.
- A folha importada é um snapshot histórico. Esta etapa não cria, atualiza nem
  inativa linhas de `employees` ou `rubrics`; mapeamentos contábeis continuam
  sob manutenção explícita nos cadastros existentes.
- Nenhum byte do documento é mantido após a requisição. Persistem apenas nome,
  extensão, tamanho e SHA-256 junto à importação. `stored_file_id` permanece
  nulo nesta etapa. A retenção do original exige uma decisão e implementação
  próprias de armazenamento, acesso e expurgo.

## API

- `POST /api/v1/companies/{company_id}/payroll-imports` recebe multipart estrito
  com um `file`, `competence` MM/YYYY e `preview_sha256` hexadecimal de 64
  caracteres.
- Resposta 201 contém `import_id`, empresa, competência, nome, tamanho, hash,
  horário, contagens de colaboradores/rubricas e totais decimais da prévia.
- `409` cobre empresa inativa, prévia/hash divergente e competência já importada.
  `400`, `413`, `415`, `422`, `503` e `504` mantêm os significados e limites
  documentados pela API de prévia.
- `GET /api/v1/companies/{company_id}/payroll-imports` lista o histórico com
  `offset` e `limit` de 50 (máximo 100), ordenado por `data_hora` decrescente e
  ID decrescente. A resposta contém metadados da importação e contagens, sem
  CPF, nome de colaborador, valores, bytes do arquivo ou caminho de armazenamento.
- Ambos os endpoints validam papel, vínculo e status da empresa no servidor.
  Todas as consultas são limitadas à empresa da rota.

## Persistência e auditoria

Adicionar à tabela legada `imports` colunas anuláveis `arquivo_sha256`,
`arquivo_bytes`, `quantidade_colaboradores` e `quantidade_rubricas`, sem alterar
nomes, precisão, nullability ou conteúdo de campos legados. Registros migrados
mantêm esses campos nulos. `arquivo` continua sendo o nome exibido; o caminho do
cliente nunca é armazenado. `data_hora` registra o mesmo instante UTC da auditoria
em formato ISO 8601.

Inserir o registro de importação, as linhas da folha e a auditoria em uma única
transação. Falha em qualquer insert ou na auditoria reverte tudo. A auditoria
registra ator, empresa, ID da importação, hash, contagens e horário; não registra
arquivo, CPF, nomes ou valores de folha. Não gravar evento quando a confirmação
falhar.

O bloqueio de empresa não fica aberto durante recepção ou parsing. Após parsear,
o serviço inicia a transação, bloqueia a empresa, revalida seu status e o acesso
do ator, verifica duplicidade e grava. Arquivo temporário e subprocesso seguem o
cleanup existente da prévia em sucesso, erro, timeout e desconexão.

## Interface

Reutilizar a tela Importação Folha e o resultado da prévia. Exibir botão de
confirmação somente para `ready` e autorizações de escrita. Durante a confirmação,
impedir repetição. Em 409 por duplicidade, preservar o resultado para consulta
e explicar que a competência já possui importação. Em erro transitório, permitir
nova tentativa com o mesmo arquivo. Em sucesso, limpar o contexto e mostrar o
identificador e resumo persistidos.

Adicionar histórico paginado com competência, arquivo, data, estado e contagens.
Troca de empresa, competência, arquivo, logout ou saída da tela descarta a
prévia e impede que respostas atrasadas apareçam em novo contexto.

## Verificação

- Testar correspondência hash/contexto, papel/vínculo, empresa ativa, duplicidade
  e duas confirmações concorrentes na mesma empresa.
- Usar PostgreSQL descartável para garantir que falha ao inserir linhas ou
  auditoria não deixa importação parcial, movimentos, metadados ou auditoria.
- Conferir que importações não alteram empregados, rubricas, contas, parâmetros
  ou arquivos existentes; conferir a preservação da ordem, multiplicidade e
  Decimal dos movimentos.
- Testar listagem paginada e isolamento entre empresas, sem expor dados pessoais
  ou valores no histórico.
- Testar confirmação e estados da interface com arquivos sintéticos; limpar o
  `File` e respostas atrasadas ao trocar o contexto.
- Rodar PostgreSQL descartável, `alembic check`, suíte frontend, build e
  Playwright. Não testar contra banco operacional ou com documentos reais.

## Fora de escopo

Substituição de competência, exclusão de importações, armazenamento ou download
do arquivo original, sincronização de empregados/rubricas, exportação TXT,
provisões e encargos. A homologação Windows permanece uma condição para uso
operacional, não uma entrega implementada por este recurso.
