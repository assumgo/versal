# Parametrizações contábil e financeira — proposta

## Objetivo e referência

Disponibilizar as duas telas na web com as regras do desktop, aproveitando os
dados já convertidos. Referência somente leitura: `app.py` do desktop v2.18,
funções `page_param_contabil`, `refresh_param_contabil`, `active_import_ids`,
`account_requires_cor_compat`, `page_finance` e `save_finance`.

São módulos novos de API e interface, com modelos existentes. Não requerem
migração do banco. A proposta aguarda revisão antes da implementação.

## Abordagem

Implementar as telas sobre os serviços, autorização e componentes existentes.
Reutilizar os cadastros de contas, rubricas e colaboradores; não duplicar seus
formulários. Fazer a conferência no servidor com paginação, evitando carregar
toda a folha no navegador. Alternativas de cálculo no navegador ou de tabela
materializada acrescentam, respectivamente, transferência integral dos dados
ou sincronização desnecessária.

## Parametrização contábil

Consulta sem gravação, por empresa e competência. Listar competências importadas
e selecionar inicialmente a mais recente, como no desktop. Sem importações,
exibir estado vazio. Incluir todas as fontes da competência: extrato, encargos
e provisões, sem excluir movimentos repetidos ou rubricas inativas.

Exibir as 17 colunas do desktop: competência, CPF, colaborador, verba, descrição,
valor, débito, D CC, D COR, crédito, C CC, C COR, histórico ID, histórico,
centro de custo, correntista e fonte. Preservar valores decimais via texto na API.
Ordenar por competência, nome, código de verba e ID para paginação estável.

Rubrica é localizada pelo código na mesma empresa. Colaborador é localizado
pelo CPF exato quando o movimento tem CPF; na ausência dele, pelo nome sem
distinção de maiúsculas. Sem correspondência por CPF, não tentar nome, conforme
a conferência desktop. Não restringir a colaboradores ativos. Em duplicatas,
usar o menor ID para tornar explícita a escolha da primeira linha legada.

As contas são resolvidas pela normalização existente e busca do código no plano
da mesma empresa. CC efetivo é a combinação por OU do plano e da rubrica.
COR efetivo combina plano, rubrica e compatibilidade: contas `4211020001` e
`4211010001` exigem COR quando há colaborador correspondente. Sem rubrica,
COR é Não, como na função desktop. Histórico ID usa a normalização de nove
dígitos; correntista exibido é o CPF do colaborador somente com dígitos,
conforme desktop, mesmo havendo outro código no cadastro.

Sem vínculos correspondentes, mostrar campos vazios e flags Não quando
aplicável; não criar cadastros nem corrigir registros ao consultar. Nulos e
flags legadas precisam de casos de equivalência explícitos, sem converter
dados persistidos durante a leitura.

## Parametrização financeira

Listagem paginada e criação com os oito campos do desktop: tipo, ID tipo
documento, CPF/CNPJ parceiro, código parceiro Siagri, conta contrapartida,
centro de custo guia, dia de vencimento e histórico. Ordenar por tipo e ID.

O desktop somente insere registros: esta entrega também não oferece edição,
exclusão ou inativação. Permitir tipos livres, inclusive repetidos e vazios;
os exemplos LIQUIDO_FOLHA, INSS, FGTS, IRRF e OUTROS são sugestões.
Aplicar trim somente ao tipo. Manter os outros textos como informados,
sem normalizar documento, parceiro ou conta, preservando zeros e pontuação.
Dia aceita inteiro estrito de 1 a 31, inicialmente 1. Não calcular datas nem
executar lançamentos financeiros. `ativo` permanece com padrão 1 na criação;
a listagem preserva registros legados e seus valores nulos.

## API, acesso e interface

Rotas sob `/api/v1/companies/{company_id}`: GET `competences`, GET
`accounting-review?competence=MM/YYYY&offset=0&limit=50` e GET/POST
`finance-params`. Paginação permite 1 a 100 registros e devolve total.
Competência explícita inválida recebe 422; competência válida sem movimentos
devolve lista vazia. Cada consulta e relacionamento restringe a empresa.

Usuários vinculados podem consultar. Administrador e Contador podem criar
parâmetros financeiros; empresa inativa bloqueia criação. Usar bloqueio de
empresa e auditoria na mesma transação, como nos cadastros existentes.
Não registrar valores de formulário na auditoria. As telas respeitam troca de
empresa, descartando respostas antigas e reiniciando formulário e paginação.

Manter navegação e estilo atuais, com seletor de competência na conferência,
botão Atualizar e tabelas com rolagem horizontal no celular. Não depender do
campo demonstrativo de competência do cabeçalho para consultar dados reais.

## Verificação e entrega

Testar equivalência das regras de leitura com casos sintéticos independentes
do desktop: duas empresas e competências, fontes diferentes, duplicatas,
ausência de vínculos, CPF versus nome, CC/COR divergentes, contas de
compatibilidade, históricos e precisão decimal. Conferir ausência de mutações
na consulta. Testar permissões, empresa inativa, auditoria e rollback na criação
financeira, vencimento e preservação literal dos campos.

Testes de interface cobrem seleção de competência, paginação, estados vazios,
criação, erros e troca de contexto; navegador cobre os dois módulos e celular.
Usar somente PostgreSQL descartável para testes. Capturas e fixtures são
sintéticas. Banco, arquivos e credenciais reais continuam fora do Git.

Após validação, abrir PR e atualizar a instância local solicitada pelo usuário,
com backup e conferência dos registros. Importação de arquivos, exportação TXT,
encargos, alterações de cadastros existentes e indicadores ficam para etapas
seguintes.
