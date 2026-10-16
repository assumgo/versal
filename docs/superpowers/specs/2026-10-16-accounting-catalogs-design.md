# Cadastros contábeis — plano de contas e rubricas

## Objetivo e decisões do usuário

Disponibilizar consulta, criação e edição do plano de contas e das rubricas por
empresa na aplicação web, aproveitando os dados migrados. O usuário escolheu os
cadastros como próxima entrega e determinou manter a regra do desktop para
centro de custo (CC) e correntista (COR), após esclarecimento das diferenças entre
salvar o cadastro e conferir/exportar. Especificação aprovada pelo usuário em
2026-10-16; o plano de implementação segue para revisão. A aprovação não autoriza
implementar regras diferentes das descritas.

Trata-se de dois módulos novos de API e interface, usando os modelos já existentes.
Não alterar o esquema, renumerar IDs, remigrar o SQLite ou modificar cadastros
automaticamente ao abrir uma tela. A instância local já populada deve continuar
funcionando durante o desenvolvimento em ambiente separado.

## Abordagem e recorte

Implementar primeiro o plano de contas e depois as rubricas, na mesma entrega.
Isso permite selecionar contas existentes ao configurar débito/crédito das
rubricas. Construir uma tela especializada para cada módulo, reutilizando tabela,
campos, alertas e estilos do sistema; o formulário genérico atual não representa
adequadamente as opções CC/COR e a seleção de contas.

Uma entrega somente de consulta não permitiria manter os cadastros. Incluir todas
as parametrizações e importação de planilhas nesta entrega aumentaria o escopo
antes de validar a manutenção manual. Por isso, o recorte proposto é consulta,
criação e edição dos dois cadastros, com busca e paginação.

## Plano de contas

Exibir ID, conta, descrição, Gera CC, tipo de correntista e Gera COR. Disponibilizar
busca por código/descrição, páginas de 50 registros e seleção de tamanho 25/50/100.
A ordenação é conta textual e ID como desempate; manter zeros à esquerda.

Na criação, conta e descrição são obrigatórias. Aplicar a normalização de conta
do desktop: trim, remoção de `.0` final e remoção de caracteres não numéricos;
rejeitar resultado vazio. Não impor o limite de 10–12 dígitos do parser de
planilhas ao cadastro manual. Gera CC aceita Sim/Não. Tipo de correntista permanece
texto, com sugestões `2-Parceiro` e `9-Nenhum`; outros textos legados continuam
legíveis. Na criação ou alteração explícita do tipo, Gera COR segue a regra de
importação do desktop: texto iniciado por `2` gera COR, os demais não geram.
Exibir esse resultado no formulário, sem oferecer um controle contraditório.

O código da conta é imutável após a criação nesta entrega, porque as referências
nas rubricas são textuais. Permitir editar descrição, CC e tipo de correntista.
Atualização parcial que não altera tipo preserva o Gera COR existente, inclusive
em dados legados divergentes. Nenhuma edição de conta atualiza rubricas em massa.

Não oferecer exclusão individual ou exclusão do plano inteiro nesta entrega.
Não existe status em `chart_accounts`; não acrescentar inativação artificial.

## Rubricas

Exibir ID, código, descrição, tipo, contas de débito/crédito, quatro opções CC/COR,
código de histórico, histórico e status. Buscar por código/descrição, filtrar
status e paginar como o plano de contas. Ordenar por código textual e ID.

Formulário com dados gerais, débito e crédito. Código e descrição são obrigatórios
na criação e não podem ser esvaziados explicitamente na edição. Código é textual
e pode conter letras, como nas rubricas de encargos. Tipo aceita P/D/E em novas
alterações; não redefinir silenciosamente um tipo legado ao editar outro campo.
Status aceita Ativa/Inativa, com Ativa como padrão na criação. Inativação e
reativação são alterações explícitas de status, sem apagar o cadastro.

Contas têm pesquisa no plano da mesma empresa e também permitem informar um código
ainda não cadastrado, como no desktop. Débito/crédito podem permanecer vazios;
a exigência de parametrização completa pertence à futura conferência da folha.
Normalizar códigos de conta fornecidos no salvamento conforme o desktop.

Código de histórico fornecido é formatado como `hist9`: somente dígitos, últimas
nove posições e preenchimento com zeros à esquerda. Na criação, vazio usa o padrão
desktop `1000182`, armazenado como `001000182`. Na edição parcial, campo omitido
mantém o valor existente; vazio explícito aplica o padrão. Histórico explícito
recebe trim e limite de 200 caracteres, conforme o formulário desktop; leitura
não corta textos legados. Informar o limite no formulário.

## Regra CC/COR do desktop — decisão aprovada

Referência somente leitura: `versal_folha_txt_v2_18/app.py`, funções
`apply_account_flags`, `save_rubric`, `save_all_rubrics_from_table`,
`sync_rubric_flags_from_plan` e `account_requires_cor_compat`.

### Ao salvar uma rubrica

Para débito e crédito, separadamente:

1. Procurar a conta normalizada no plano da mesma empresa.
2. Se existir, copiar CC/COR dessa conta para as opções da rubrica, substituindo
   as marcações manuais. A API aplica a regra, independentemente do formulário.
3. Se não existir, manter as opções manuais enviadas. Em PATCH, opção omitida
   mantém o valor existente; em criação, as quatro opções começam em Sim,
   conforme `clear_rubric` do desktop. Nulos legados não são corrigidos por leitura.

Aplicar a regra dos dois lados em todo salvamento da rubrica, inclusive quando
apenas descrição ou status é alterado: isso reproduz a rotina de salvamento do
desktop. A resposta devolve os valores efetivamente persistidos.

Na tela, ao selecionar uma conta cadastrada, apresentar CC/COR dessa conta e
explicar que prevalecem ao salvar. Para uma conta não cadastrada, liberar as
opções manuais. Abrir uma rubrica não provoca gravação nem sincronização; mostrar
os valores salvos e, havendo divergência, informar o que será aplicado ao salvar.

### Na futura conferência/exportação

Não implementar exportação nem sincronização em massa neste recorte. Preservar
para a etapa futura a regra distinta do desktop: CC/COR efetivo é Sim se a conta
ou a rubrica exigir; COR também pode ser obrigatório, em linhas vinculadas a
colaborador, para as contas `4211020001` e `4211010001`.
Não aplicar essa exceção de exportação ao cadastro para substituir a regra de
salvamento aprovada pelo usuário.

## Compatibilidade e registros repetidos

Respostas aceitam os nulos e textos legados existentes. PATCH altera somente os
campos fornecidos, exceto a reaplicação CC/COR descrita acima. Não reformatar todos
os códigos, históricos ou flags ao listar, migrar ou inicializar o serviço.

Não criar constraints de unicidade nem deduplicar os dados migrados. Para novos
cadastros, recusar código já existente na mesma empresa com 409; na edição, manter
um código repetido legado é permitido, mas uma troca para outro código já usado
é recusada. A verificação ocorre sob bloqueio da empresa para serializar escritas.

Se um código do plano já tiver registros repetidos, o lookup da regra usa o menor
ID para uma escolha estável da primeira ocorrência. A busca mostra os IDs das
ocorrências; nenhuma é apagada ou mesclada. Comparar códigos como texto, usando
exatamente o código normalizado fornecido, sem converter para inteiro.

## API, autorização e transações

Rotas sob `/api/v1/companies/{company_id}`:

- `GET/POST /chart-accounts` e `GET/PATCH /chart-accounts/{account_id}`.
- `GET/POST /rubrics` e `GET/PATCH /rubrics/{rubric_id}`.

Listagens recebem `q`, `offset >= 0` e `limit` entre 1 e 100 (padrão 50); rubricas
também recebem status opcional. Resposta: `{items, total, offset, limit}`.
Campos e opções usam os nomes legados, flags inteiras 0/1 nas escritas e nulos
aceitos nas respostas. Rejeitar flags fora do domínio, campos extras, PATCH vazio,
IDs inválidos e tentativa de alterar `company_id` com 422.

Todos os perfis autenticados com vínculo à empresa podem ler. Apenas Administrador
e Contador com vínculo podem criar/editar. Operador e Consulta recebem 403 nas
escritas. Falta de vínculo recebe 403; ID de registro de outra empresa dentro de
uma empresa autorizada recebe 404, sem exposição de dados.

Empresa inativa permite consulta e bloqueia escrita com 409. Escritas bloqueiam a
linha da empresa com o mesmo mecanismo usado pela inativação, incluindo cadastros,
edições e verificação de duplicatas. Persistência e auditoria ocorrem na mesma
transação. Registrar ator, empresa, entidade, ID, ação e nomes dos campos alterados;
não registrar valores completos dos formulários. Falha de auditoria desfaz tudo.

Usar schemas, repositories e services específicos; reutilizar autenticação,
autorização e auditoria existentes. Não criar dependências novas ou migrations.

## Interface e contexto

Adicionar rotas `/plano-de-contas` e `/rubricas` ao roteamento existente e conectar
os itens correspondentes da sidebar. Reutilizar o visual e a responsividade do
sistema. Preservar as demais telas e o estado de autenticação.

Sem empresa selecionada, pedir seleção. Empresa inativa e perfil sem escrita
usam somente consulta. Alterar a empresa limpa formulário, resultados e paginação;
respostas atrasadas da empresa anterior não podem preencher a nova tela. Usar
mensagens de carregamento, vazio, erro e gravação, além de tentativas de consulta.
Não reaplicar automaticamente uma escrita interrompida por mudança de sessão.

Cadastros pertencem à empresa, independentemente da competência do cabeçalho;
informar isso na tela. Busca no plano deve ser paginada na API para não renderizar
todas as contas nem carregar um seletor com milhares de opções de uma vez.

## Critérios de validação

- PostgreSQL descartável e fixtures sintéticas para CRUD, paginação, busca,
  nulos/repetições legadas, RBAC e bloqueio entre empresas.
- Testes da regra desktop cobrindo os quatro campos, conta existente com Não e
  marcação manual Sim (resultado Não ao salvar), conta com Sim e manual Não
  (resultado Sim), conta ausente e rubrica legada com nulos.
- Salvar somente descrição/status também reaplica as regras da conta; consultar
  nunca modifica rubricas ou plano. Alterar conta não sincroniza outras rubricas.
- Concorrência com inativação/duplicação usa conexões independentes; falha de
  auditoria deixa cadastros e flags sem alteração parcial.
- Frontend: consulta/edição, pesquisa/paginação, regras exibidas, perfis, troca de
  empresa com requisições pendentes, sessão expirada e tabela em tela pequena.
- Executar suíte backend, Alembic check, testes frontend, build e Playwright;
  registrar capturas desktop/mobile das novas telas com dados sintéticos.
- Após aprovação da implementação, atualizar a instância local preservando volume,
  usuários e vínculos. Conferir por leitura os cadastros migrados, sem usá-los como
  fixtures nem executar testes de mutação no banco da aplicação.

## Fora de escopo

Importação/exportação XLS/XLSX, edição em grade e operações em massa, exclusão do
plano, parametrização financeira, conferência por competência, parsers, TXT,
painel de indicadores e alterações das regras do desktop fora de CC/COR.
