# Parametrizações contábil e financeira

As telas usam a empresa selecionada na sessão. Todos os usuários vinculados podem
consultar. Administrador e Contador podem inserir parâmetros financeiros em empresa
ativa. A consulta contábil nunca grava ou sincroniza cadastros.

## Financeira

Acesse **Parametrização Financeira** ou `/parametrizacao-financeira`. Clique em
**Novo parâmetro**, preencha os campos e escolha **Salvar parâmetro financeiro**.
O dia do vencimento vai de 1 a 31 e começa em 1. Os textos são livres; somente o
Tipo recebe remoção de espaços nas pontas. Não há validação de dígitos de CPF/CNPJ
nem normalização de conta: zeros, espaços e pontuação são preservados como no
desktop. Exemplos de tipo: LIQUIDO_FOLHA, INSS, FGTS, IRRF, OUTROS.

Cada salvamento insere um parâmetro, inclusive se já existir outro com o mesmo
tipo. Como no desktop v2.18, esta entrega oferece inclusão e consulta; não há
edição, exclusão ou inativação. A listagem inclui parâmetros legados nulos ou
inativos sem alterá-los e tem páginas de 25, 50 ou 100 registros.

A API oferece GET/POST `/api/v1/companies/{company_id}/finance-params`, com
`offset` a partir de 0 e `limit` entre 1 e 100 (padrão 50). Campos de criação:
`tipo`, `documento_id`, `parceiro_cpf_cnpj`, `codigo_parceiro_siagri`,
`conta_contrapartida`, `centro_custo`, `vencimento_dia`, `historico`.
Textos omitidos são vazios, dia omitido é 1. Extras e nulos explícitos são
rejeitados. Não calcula datas nem gera lançamentos.

## Contábil

Acesse **Parametrização Contábil** ou `/parametrizacao-contabil`. O seletor
**Competência da conferência** apresenta as competências importadas da empresa e
começa na mais recente válida. Ele define a consulta desta tela, independente do
campo de competência no cabeçalho. **Atualizar conferência** recarrega as opções
e os movimentos, preservando a seleção quando ainda disponível e válida.
Competências legadas fora do formato MM/AAAA são exibidas, sem alteração no banco;
para consultá-las é necessário tratar a origem em etapa futura.

A tabela apresenta as 17 colunas do desktop. Inclui extrato, encargos e provisões
existentes na competência, com paginação e rolagem horizontal no celular.
Valores são textos decimais para preservar integralmente a precisão armazenada.
Rubricas e colaboradores inativos ainda participam da conferência, como no desktop.

As regras são específicas de leitura e diferem das regras de salvamento de rubrica:

- Movimento encontra rubrica pelo código na mesma empresa.
- Colaborador é localizado por CPF exato quando informado; sem CPF, por nome sem
  distinção de maiúsculas. CPF sem correspondência não tenta nome como alternativa.
- Duplicatas usam o menor ID em cada cadastro e não multiplicam movimentos.
- Conta do plano é procurada pelo código armazenado igual à conta normalizada da
  rubrica. CC efetivo é Sim quando plano ou rubrica habilitam CC.
- COR combina plano, rubrica e a compatibilidade das contas `4211020001` e
  `4211010001` quando há colaborador. Sem rubrica, COR é Não.
- Correntista exibido é o CPF do colaborador com somente dígitos, conforme desktop;
  o código correntista alternativo do cadastro não substitui esse valor.
- Histórico ID usa os nove últimos dígitos, completados à esquerda; sem dígitos,
  fica vazio. Nulos legados de flags do plano são lidos como zero, sem persistência.

A API GET `/api/v1/companies/{company_id}/competences` lista competências distintas;
GET `/api/v1/companies/{company_id}/accounting-review` exige `competence=MM/YYYY` e
aceita `offset` e `limit` com os mesmos limites da listagem financeira. Não cria
cadastros ausentes, não altera importações e não executa validação/exportação TXT.
Campos ausentes continuam vazios ou nulos conforme a origem.

## Compatibilidade e validação

Referência de comportamento: desktop v2.18 `page_finance`, `save_finance`,
`refresh_param_contabil`, `active_import_ids` e `account_requires_cor_compat`.
Testes usam cenários sintéticos com expectativas conferidas pelas regras dessas
funções. Cobrem precisão, duplicatas, nomes/CPF, histórico, CC/COR, permissões,
auditoria, concorrência com inativação e troca de contexto na interface.
Nenhuma migration ou dependência nova é necessária. Dados, backups e credenciais
operacionais permanecem fora do Git. A instalação não repete a conversão SQLite.
