# Migração única de SQLite para PostgreSQL

## Objetivo e escopo aprovado

Disponibilizar um comando local, sem tela, para transferir os dados do desktop
para o PostgreSQL da aplicação web uma única vez. Simular por padrão e gravar
somente com `--apply`. Preservar IDs, campos, nulos, relacionamentos, duplicatas
permitidas e valores históricos. Exigir as sete tabelas operacionais vazias no
destino. Não substituir, mesclar ou apagar registros existentes.

O usuário aprovou esse funcionamento em 2026-10-16. Também determinou que o banco
real não seja commitado. Banco, WAL, SHM, cópias e relatórios com dados reais ficam
fora do repositório; os testes terão somente dados sintéticos.

## Interface

Executar a partir de `web/backend/`:

```bash
.venv/bin/python -m app.scripts.migrate_sqlite --source /caminho/versal_folha.db
.venv/bin/python -m app.scripts.migrate_sqlite --source /caminho/versal_folha.db --apply
```

O destino vem de `DATABASE_URL` na configuração do backend, nunca de uma senha
na linha de comando. Exigir PostgreSQL com migrações Alembic atualizadas; o comando
não cria nem altera o esquema. A configuração segue o backend existente.
Uma opção `--report /caminho/relatorio.json` permite salvar o resultado;
sem ela, mostrar um resumo no terminal. Recusar sobrescrever relatório existente
e validar seu caminho antes de iniciar a carga. Códigos de saída: 0 para simulação
ou aplicação bem-sucedida; 1 para falha ou inconsistência; 2 para argumentos inválidos.

## Origem e fotografia consistente

Exigir o desktop fechado. Copiar DB/WAL/SHM para pasta temporária privada,
verificando identidade, metadados e hashes antes/depois; recusar alterações durante
a cópia e rollback journal presente. Abrir somente a cópia em modo leitura e usar
a API de backup para produzir uma fotografia consistente temporária, incluindo
transações confirmadas no WAL. Essa abordagem evita que SQLite modifique o SHM
da origem mesmo em uma conexão declarada somente leitura.
Não usar `immutable=1`, que pode ignorar o WAL. Não executar checkpoint, reparo ou
comandos de escrita na origem. Se a abertura somente leitura exigir alteração
dos arquivos auxiliares ou falhar, interromper e orientar o uso de uma cópia
consistente obtida com o desktop fechado. Nunca copiar apenas o arquivo principal
quando houver WAL ativo. Remover a fotografia temporária ao terminar.

Rodar verificação de integridade e conferir colunas/tipos das sete tabelas antes
de transferir. Colunas inesperadas nas tabelas migradas bloqueiam a operação para
evitar perda silenciosa; tabelas adicionais são informadas como fora do escopo.

## Mapeamento e validação

Copiar, nesta ordem: `companies`, `employees`, `rubrics`, `chart_accounts`,
`finance_params`, `imports`, `payroll_lines`. Usar colunas explicitamente mapeadas
ao contrato de compatibilidade, sem passar pelas validações de novos cadastros.
Os campos novos da web usam defaults ou nulos conforme o esquema.

Validar IDs inteiros de 64 bits e referências às empresas/importações, incluindo
divergência de empresa entre linha e importação. Respeitar as combinações nulas
aceitas pelas FKs PostgreSQL. Bloquear valores incompatíveis, sem corrigir,
renumerar, arredondar ou descartar registros automaticamente.

Ler NUMERIC como texto no SQLite e converter com `Decimal`, sem criar valores
monetários a partir de floats Python. A migração preserva o valor que o SQLite
efetivamente armazena e expõe; não pode reconstruir precisão já perdida pelo
desktop. Rejeitar números inválidos ou não finitos e REAL cuja conversão para texto não
retorne exatamente ao valor SQLite, para impedir perda adicional de precisão. Preservar textos, espaços,
formatação de documentos e competência textual.

## Simulação e aplicação

A simulação verifica origem, esquema e estado vazio do destino e produz contagens,
totais decimais e diagnósticos, sem executar DML nem ajustar sequências no destino.
Ela não equivale a comprovar uma carga concluída.

Na aplicação, abrir uma transação PostgreSQL e bloquear as sete tabelas contra
escritas concorrentes em ordem fixa. Revalidar que estão vazias sob esses bloqueios.
Inserir os dados em lotes, preservando os IDs, e verificar a cópia na mesma
transação. Qualquer erro anterior ao commit desfaz toda a carga.

Sincronizar os geradores de IDs com `ALTER TABLE ... ALTER COLUMN id RESTART WITH`
transacional, usando o maior ID e um mínimo de 1. Bloquear previamente IDs que não
permitam gerar um sucessor BIGINT. Assim uma falha também reverte os ajustes das
sequências. Nenhum outro comando pode escrever no destino durante a migração.

## Conferência e relatório

Comparar todos os campos legados por ID, contagens por tabela e totais de `valor`
e `liquido` por empresa/competência; tolerância monetária zero. Comparar nulos e
multiplicidade exatamente. Só confirmar após a conferência completa.

O relatório identifica modo, versão do comando, resultado, contagens, totais,
problemas por tabela/ID e confirmação do commit. Não incluir nomes, CPF/CNPJ,
linhas completas, credenciais ou URL de conexão. Mensagens de exceção do driver
não são impressas diretamente, pois podem conter dados ou parâmetros SQL.
Se a escrita do relatório falhar após o commit, indicar explicitamente que a carga
foi confirmada e que somente o relatório falhou; não sugerir repetição da carga.

## Acesso após a migração

Não criar usuários ou vínculos automaticamente. Os usuários, papéis e sessões da
web permanecem separados do legado. Documentar que o administrador deve conceder
acesso às empresas importadas pelos mecanismos existentes de administração.
Os nomes de arquivos históricos são preservados; os PDFs/planilhas originais
não são enviados ao armazenamento web por esta ferramenta.

## Testes e entrega

Testes unitários com SQLite sintético: estrutura, integridade, WAL, referências,
nulos, IDs extremos, NUMERIC e proteção dos relatórios. Integração em PostgreSQL
descartável: simulação sem escrita, aplicação fiel, geração de IDs após carga,
recusa de destino ocupado/reexecução, rollback de falha e concorrência de escrita.
Não executar testes nem carga real no banco operacional.

Atualizar o guia do backend e o contrato de compatibilidade com os comandos,
pré-requisitos, backup e conferência. Adicionar padrões de ignore para SQLite e
seus arquivos WAL/SHM. O banco real não é fixture e não faz parte da entrega.

## Fora de escopo

Interface gráfica, sincronização recorrente, merge de bancos, migração de parsers,
arquivos originais, exportação TXT, reparo automático e corte operacional.
