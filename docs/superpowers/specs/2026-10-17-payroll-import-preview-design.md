# Upload e prévia de Extrato Mensal

Status: proposta para revisão. Branch `feat/payroll-import-preview`, baseada
na main `0280615`, após integração do PR #14.

## Objetivo e escopo

Permitir ao usuário enviar um Extrato Mensal PDF/XLS/XLSX e conferir empresa,
competência, colaboradores, rubricas e valores antes de uma futura importação.
Reutilizar os parsers extraídos do desktop, sem alterar suas regras ou referências.
Esta entrega não grava movimentos, colaboradores, rubricas, importações ou
metadados de arquivos. Não oferece confirmação de importação nem exportação TXT.

O usuário aprovou avançar com upload e conferência sem gravação definitiva.
Os limites e interfaces abaixo são decisões propostas para esta entrega.

## Abordagem

Escolha proposta: requisição multipart que produz uma prévia temporária,
mantida apenas na memória da tela. Arquivo temporário no servidor é eliminado
ao terminar, inclusive em erro. Troca de contexto ou saída da tela elimina a prévia.

Alternativas: persistir uma sessão de prévia permitiria retomar e paginar no
servidor, mas exigiria expiração e autorização de artefatos; implementar já a
gravação definitiva exigiria decisões adicionais de duplicidade, substituição,
sincronização de cadastros e homologação. Ficam para outra entrega.

## API e acesso

Adicionar `POST /api/v1/companies/{company_id}/payroll-import-preview`.
Recebe multipart com exatamente um `file` e `competence` no formato MM/YYYY,
com mês 01..12 e ano de quatro dígitos. Não aceitar empresa no corpo: o ID da
rota, autorizado no servidor, define o contexto. Campos extras e arquivos
adicionais são rejeitados. A aplicação requer `python-multipart`.

Administrador, Contador e Operador podem gerar prévias em empresas vinculadas;
Consulta não pode enviar documentos. Empresa inativa bloqueia a operação com
409. Ausência de sessão válida retorna 401; falta de papel ou vínculo retorna
403, sem distinguir empresa inexistente de empresa não autorizada.

Consultar usuário, vínculo e atividade da empresa antes de executar o parser.
Revalidar acesso e atividade antes de devolver dados, pois podem mudar durante
o processamento; não manter bloqueio de empresa durante a leitura do arquivo.
Não criar auditoria de importação: esta operação não importa nem persiste dados.

## Recepção e execução

Aceitar extensões `.pdf`, `.xls` e `.xlsx`, sem distinção de maiúsculas.
Limite do arquivo: 10 MiB, verificado pelos bytes efetivamente recebidos, sem
confiar apenas em Content-Length. Arquivo de zero bytes é inválido.
Validar assinatura PDF, contêiner OLE/XLS ou ZIP/XLSX coerente com a extensão;
Content-Type do navegador é informativo, não comprovação do formato.
XLSX deve conter a estrutura de workbook e não pode declarar mais de 50 MiB
de conteúdo descompactado nem entradas criptografadas. Não extrair ZIP no disco.

Usar nome temporário gerado pelo servidor e sufixo validado, sem usar caminhos
do nome original. Não registrar nome, conteúdo, CPF, salários ou mensagens
internas das bibliotecas em logs/respostas de erro. O nome exibido é somente
o basename, limitado a 255 caracteres, renderizado como texto.

Executar o parser em processo separado com prazo de 30 segundos; ao exceder,
terminar o processo e aguardar seu encerramento antes de remover temporários.
Limitar a duas leituras simultâneas por processo da API; sem vaga, responder
503 com orientação para tentar novamente, sem iniciar leitura concorrente extra.
Desconexão do cliente não pode deixar arquivos ou processos órfãos.

O limite da prévia é 2.000 colaboradores e 10.000 rubricas. Excedê-lo retorna
413; não truncar silenciosamente. Os limites são por requisição, não alegação
de suporte a todos os layouts ou proteção absoluta contra documentos complexos.

## Resultado e comparação de contexto

Resposta 200 contém `company_id`, `requested_competence`, `filename`,
`size_bytes`, `sha256`, `status` (`ready` ou `blocked`), `issues`, `summary`
e `statement`. `statement` preserva a estrutura `ParsedStatement` do parser;
`valor` e `liquido` são texto decimal na resposta, sem conversão para float.

`summary`: número de colaboradores, número de rubricas, totais por tipo P/D/E
e soma dos líquidos informados. Somar Decimal sem perda adicional de precisão,
incluindo números negativos. Não recalcular líquido a partir de P menos D nem
somar o líquido uma vez por rubrica. Preservar ordem e multiplicidade devolvidas
pelo parser; não aplicar uma segunda deduplicação.

`issues` são objetos com `code`, `severity` (`warning` ou `blocking`) e `message`.
As mensagens não incluem identificadores de outra empresa. Regras:

- Comparar CNPJ detectado e cadastrado após remover somente caracteres não
  numéricos. Igualdade de 14 dígitos identifica correspondência; não exigir
  dígitos verificadores, pois o corpus sintético usa documentos fictícios.
- CNPJ ausente, cadastrado incompleto ou divergente gera issue bloqueante;
  não buscar outra empresa nem mudar automaticamente a seleção. Não usar nome
  ou código Siagri como substituto de CNPJ.
- Competência detectada ausente, inválida ou diferente da solicitada bloqueia.
  Não preencher silenciosamente a competência detectada com a selecionada.
- Ausência de colaboradores ou de rubricas bloqueia. Não afirmar que um
  documento sem texto é necessariamente digitalizado ou que layout vazio é válido.
- Toda prévia informa que a homologação funcional/Windows está pendente.
  PDF acrescenta aviso sobre as limitações conhecidas de acentos e captura de CC.
  Excel informa a leitura somente da primeira aba e a supressão legada de
  zeros/duplicatas. São avisos, não correções dos resultados do parser.

Qualquer issue bloqueante define `status=blocked`. O conteúdo lido permanece
disponível para conferência mesmo se houver divergência de empresa/competência:
é o arquivo fornecido pelo próprio usuário, não consulta a dados de outra empresa.
`ready` significa apenas que as verificações desta prévia passaram; não significa
homologação nem importação realizada.

## Erros

400 para arquivo vazio, corrompido ou ilegível; 413 para limite de bytes,
conteúdo XLSX declarado ou resultado; 415 para extensão/assinatura incoerente
ou família reconhecida não suportada (`UnsupportedLayoutError`);
422 para campos multipart ausentes, extras, repetidos ou competência inválida;
504 para leitura excedendo prazo. Mensagens públicas orientam ação sem revelar
stack trace ou caminhos do servidor. Divergências de contexto são resultado
200 bloqueado, não erro de transporte. Temp files são removidos em todos os casos.

## Interface

Ativar o item existente Importação Folha em `/importacao-folha`. Usar empresa
e competência do cabeçalho como contexto, convertendo YYYY-MM para MM/YYYY
somente para a requisição. Exibir o contexto consultado junto à prévia.
Não mudar seletores com base no resultado do parser.

Formulário com arquivo, formatos/tamanho aceitos e botão Gerar prévia. Mostrar
estados sem empresa, sem permissão, empresa inativa, envio, erro e resultado.
Impedir envio repetido enquanto pendente. Erro permite tentar novamente.
Selecionar outro arquivo elimina o resultado anterior. Não guardar documento
ou resposta em localStorage/sessionStorage.

Exibir empresa e competência detectadas, divergências, contagens e totais.
Tabela de colaboradores com matrícula, nome, CPF, situação, cargo, centro de
custo, líquido e quantidade de rubricas. Selecionar colaborador mostra suas
rubricas com código, descrição, referência, valor e tipo. Paginação local
25/50/100 em ambas as listas, sem limitar os totais ao trecho exibido.
Valores decimais permanecem texto; não usar Number para totalizar ou formatar.
Reutilizar Alert, DataTable, paginação, estilos e navegação existentes.

Troca de empresa, competência, status ou permissão elimina resultado/arquivo e
descarta respostas atrasadas. Logout e desmontagem também descartam o contexto.
Cliente API deve enviar FormData sem definir Content-Type JSON, preservando
autenticação e renovação de sessão existentes; cobrir a repetição após 401.
No celular, tabelas têm rolagem horizontal sem overflow da página.

## Verificação e entrega

Testes de API cobrem quatro papéis, duas empresas, inativa, ausência/revogação
de vínculo, competência e CNPJ ausentes/divergentes, arquivos vazios/corrompidos,
limites, fallbacks já existentes, prazo, concorrência e remoção de temporários.
Conferir ausência de mudanças nas tabelas operacionais, stored_files e auditoria.
Usar o corpus congelado intacto e fixtures sintéticas adicionais independentes.

Testes de resumo fixam decimais, negativos, rubricas repetidas e líquido por
colaborador; sem tolerância monetária. Testes de interface cobrem FormData,
renovação de sessão, paginação, erros, permissões e respostas fora de ordem.
Playwright cobre fluxo completo com API simulada e capturas desktop/mobile.

Executar backend com PostgreSQL descartável, Alembic check, suíte frontend,
build e testes de navegador; revisar capturas sintéticas. Não atualizar a
instância operacional nem reenviar documentos reais como teste desta entrega.
Documentar limites e abrir PR quando solicitado; não efetuar merge automático.
