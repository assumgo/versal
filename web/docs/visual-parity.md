# Paridade visual — Task 7

Referência consultada: `versal_folha_txt_v2_18/app.py`, `MainWindow`, linhas
950–1140, e assets originais da distribuição desktop. A comparação é baseada
no código e nos assets do desktop; não foi executado o aplicativo operacional.

| Elemento desktop | Implementação web |
| --- | --- |
| Logo Versal Agro e ícone da aplicação | Arquivos originais, sem alteração, em `frontend/public/assets/`; ícone aplicado no documento HTML |
| Verde `#315f2f`, destaque `#89bf21`, fundo `#f7faf5`, borda `#cfdccc` | Variáveis em `styles/tokens.css` |
| Sidebar branca, largura 295 px, título “Integrador Folha TXT” | `Sidebar`, fixa no desktop, com rolagem própria |
| Empresa atual na sidebar | Mesmo contexto recebido por `AppShell` e mostrado no cabeçalho |
| Dashboard → Empresas → Colaboradores → Importação Folha → Plano de Contas → Rubricas → Encargos da Empresa → Parametrização Contábil → Parametrização Financeira → Exportação TXT → Backup | Todos os onze itens, nomes e ordem preservados; item ativo com destaque verde claro e `aria-current` |
| Cabeçalho de empresa e competência | `Header`, valores recebidos pelo shell; somente leitura nesta demonstração. Seleção integrada à sessão pertence à Task 8 |
| Colaboradores ativos, Verbas parametrizadas, Importações, Pendências | Quatro `StatCard`, mesmos títulos do desktop, valores fictícios |
| Conteúdo rolável | Documento com rolagem vertical e sidebar independente |
| Tabelas compactas, cabeçalho verde suave, linhas alternadas | `DataTable` com cabeçalhos semânticos e região focalizável de rolagem horizontal |
| Cadastro de empresas: ID, código, razão, CNPJ, status | Tabela demonstrativa de `Companies` |
| Cadastro de colaboradores: ID, nome, CPF, matrícula, cargo, centro de custo, correntista, status | Tabela demonstrativa de `Employees`, sem ocultar colunas no celular |
| Controles arredondados e compactos | Estilos globais e `FormField`; `ConfirmModal` usa diálogo nativo, cancelamento por Escape e devolução de foco |
| Rodapé Versal Agro Contabilidade | Preservado, com identificação Web em lugar da versão do executável |

Adaptações: abaixo de 901 px a navegação vira drawer com fechamento por item,
botão, fundo e Escape, contenção e retorno de foco e bloqueio do conteúdo por
`inert`. Os indicadores passam a duas colunas. O destaque ativo usa texto verde
escuro sobre verde claro para melhorar a leitura. Telas dos módulos posteriores
informam sua indisponibilidade; não executam importação, exportação ou backup.
Login é componente de prévia, com envio desabilitado, preparado para a Task 8.
Todos os dados são fictícios e identificados como demonstração.

## Evidências

Capturas feitas pelo Playwright com Google Chrome local:

- [Desktop, 1440 × 1000](screenshots/task7-desktop.png)
- [Celular, 390 × 844](screenshots/task7-mobile.png)
- [Drawer no celular](screenshots/task7-mobile-drawer.png)
- [Tabela no celular, rolada até a última coluna](screenshots/task7-mobile-table.png)

## Validação reproduzível

Em `web/frontend`, execute `npm ci`, `npm test -- --run` e `npm run build`.
Para os testes reais de navegador e regeneração das capturas, execute
`npm run test:e2e`. É necessário Google Chrome em `/usr/bin/google-chrome`,
ou definir `CHROME_PATH` com o caminho do executável. O Playwright inicia o
Vite na porta 5174 e pode reutilizar um servidor local já iniciado nessa porta.
Nenhum teste acessa o banco de dados.
