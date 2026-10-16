# Plano de contas e rubricas na web

Os dois módulos usam os cadastros existentes da empresa selecionada, em todas as
competências. Não é necessário repetir a conversão SQLite. IDs, nulos e registros
repetidos migrados são preservados; abrir as telas não sincroniza cadastros.

## Acesso e navegação

Use **Plano de Contas** (`/plano-de-contas`) e **Rubricas** (`/rubricas`) na sidebar.
Todos os quatro perfis podem consultar empresas às quais estejam vinculados.
Somente **Administrador** e **Contador** podem criar e editar. Empresa inativa
permite consulta e recusa alterações. O administrador também precisa de vínculo
explícito com a empresa.

Listagens têm pesquisa por código/descrição, paginação de 25/50/100 registros
(padrão 50) e ordenação textual por código e ID. A busca trata `%` e `_`
literalmente. Rubricas podem ser filtradas por status. A API pagina os resultados;
a tela não carrega todas as contas do plano para montar um seletor gigante.

## Plano de contas

Campos: conta, descrição, Gera CC, tipo de correntista e Gera COR. Conta e descrição
são obrigatórias na criação. O código é normalizado como no desktop e conserva
zeros à esquerda. Após criar, o código é fixo; descrição, CC e tipo de correntista
podem ser alterados.

Ao criar ou alterar o tipo, `2-Parceiro` (ou outro texto iniciado por `2`) gera COR;
os demais tipos não geram. Se apenas descrição ou CC for alterado, o COR existente
é preservado, inclusive uma divergência legada. Editar uma conta não atualiza as
rubricas em massa. Não há exclusão de contas neste recorte.

## Rubricas e regra de salvamento do desktop

Código e descrição são obrigatórios na criação. O código é textual, aceitando
rubricas como FGTS. Tipo aceita P/D/E e status Ativa/Inativa. Rubricas são
inativadas/reativadas explicitamente por status, sem exclusão.

Débito e crédito têm busca no plano da mesma empresa. Também é possível informar
uma conta ainda não cadastrada ou deixá-la vazia para parametrização posterior.
Ao salvar, para cada lado:

- **Conta cadastrada:** suas opções CC/COR substituem as marcações da rubrica.
- **Conta não cadastrada:** são mantidas as opções manuais.
- A regra também vale ao editar somente descrição ou status.

Exemplo: conta com Gera CC **Não** e rubrica salva com Gera CC **Sim**. Abrir a
rubrica mostra o aviso de divergência e informa que a conta prevalecerá. Ao salvar,
o Gera CC da rubrica passa a **Não**, como no desktop. A leitura não grava essa
alteração sozinha.

A tela mostra as opções salvas quando divergem do plano e o resultado que será
aplicado ao salvar. Opções de uma conta conhecida são informativas; sem conta,
Sim/Não pode ser escolhido manualmente. Se uma conta legada tiver flags nulas ou
inválidas, corrija explicitamente o plano antes de salvar uma rubrica dependente;
a API recusa com 409 sem gravar parcialmente.

A regra de futura conferência/exportação é diferente: conta ou rubrica podem
exigir CC/COR, e certas contas de salários/pró-labore exigem COR nas linhas
vinculadas a colaborador. Essa regra de exportação não é aplicada ao salvar o
cadastro. TXT e conferência não fazem parte desta entrega.

Código de histórico informado é formatado com nove dígitos; vazio explícito usa
`001000182`. Histórico alterado recebe trim e limite de 200 caracteres. Uma edição
que não altera esses campos preserva o histórico legado, mesmo nulo ou maior.
Campos omitidos no PATCH permanecem como estão, exceto as flags reaplicadas pela
regra de salvamento acima. Tipo legado não é redefinido ao editar outro campo.

Novos códigos repetidos na mesma empresa são recusados. Repetições legadas seguem
legíveis e editáveis por ID. Se um código de conta já estiver repetido, o lookup
usa o menor ID da mesma empresa, sem excluir ou mesclar as outras ocorrências.

## API

Prefixo `/api/v1/companies/{company_id}`:

| Recurso | Rotas |
| --- | --- |
| Plano de contas | `GET/POST /chart-accounts`, `GET/PATCH /chart-accounts/{account_id}` |
| Rubricas | `GET/POST /rubrics`, `GET/PATCH /rubrics/{rubric_id}` |

Listagens retornam `{items, total, offset, limit}` e aceitam `q`, `offset >= 0` e
`limit` de 1 a 100. Plano aceita `conta` para igualdade textual exata; rubricas
aceitam `status`. POST retorna 201; PATCH retorna 200. Flags de entrada são inteiros
0/1, não booleanos; respostas mantêm nulos legados.

Falta de autenticação retorna 401; falta de papel ou vínculo retorna 403; ID de
outra empresa dentro do escopo autorizado retorna 404; empresa inativa,
duplicação ou flags de conta inutilizáveis retornam 409. Corpo vazio, campos
extras, alteração do código da conta e valores inválidos retornam 422.

Escrita e auditoria são confirmadas na mesma transação. O bloqueio da empresa
serializa gravações com duplicação/inativação concorrente. A auditoria registra
nomes dos campos alterados, inclusive flags derivadas, sem valores de formulário.

## Verificação e capturas

Os testes usam somente PostgreSQL descartável e fixtures sintéticas. Para o
frontend, `npm test -- --run` e `npm run build`. Playwright usa servidor próprio
na porta 5175 (ou `E2E_PORT`), recusa a porta 5174 da instância convertida e não
reutiliza servidor existente. Todos os endpoints dos testes de navegador são
interceptados; nenhuma mutação é enviada ao banco da aplicação.

Capturas sintéticas:

- `screenshots/accounting-plan-desktop.png`
- `screenshots/accounting-rubric-desktop.png`
- `screenshots/accounting-plan-mobile.png`
- `screenshots/accounting-rubric-mobile.png`

Na atualização da instância local, preserve projeto Compose, `.env`, volume,
usuários e vínculos. Recrie as imagens/serviços da aplicação sem `down -v`, sem
executar o migrador SQLite e sem recriar administrador. Faça backup antes e
confira contagens, login e consultas depois. Não use dados da aplicação como
fixtures nem execute testes de mutação nessa base.

O combo Tipo de correntista permite selecionar `2-Parceiro` ou `9-Nenhum`. Tipos legados diferentes continuam disponíveis ao editar a conta e são preservados enquanto não forem alterados.
