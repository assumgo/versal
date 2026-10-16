# Fixtures e anonimização

`legacy_schema.sql` contém somente o DDL de referência do desktop, sem dados reais.
Os testes atuais geram registros sintéticos; ainda não há corpus PDF/XLS/XLSX/TXT
homologado nem implementação de parser/exportador nesta fase.

Para a próxima etapa, organizar cada caso em `parser_equivalence/<case_id>/`, com
`manifest.json`, entrada, resultado estruturado esperado e saída TXT de referência.
O manifesto segue o [protocolo de equivalência](../../../docs/parser-equivalence-strategy.md):
versão do desktop, parâmetros reproduzíveis, layout/encoding, hashes, contagens,
totais, erros esperados, regras de comparação e aprovação funcional.

Preferir documentos inteiramente sintéticos. Quando necessário usar uma origem
real autorizada, trabalhar em cópia isolada e substituir nomes, CPF/CNPJ,
matrículas, empresas, endereços, contatos, contas bancárias, salários identificáveis,
nomes de arquivo e caminhos por dados fictícios. Preservar comprimentos, máscaras,
dígitos verificadores quando relevantes, acentos, duplicatas, relações, precisão,
formatação e complexidade do layout que o caso pretende testar. Gerar novamente
os esperados no desktop usando a entrada já anonimizada.

Manter substituições consistentes entre entrada, configuração, JSON esperado e TXT.
Não versionar a tabela reversível de correspondência, a origem real, bancos SQLite,
credenciais, tokens, logs com dados pessoais ou planilhas temporárias. Hash de um
identificador real não constitui anonimização suficiente.

Revisar também metadados de PDF/Office, autor, comentários, abas/linhas ocultas,
fórmulas, imagens, anexos, texto OCR e propriedades embutidas. Confirmar que a
anonimização não introduziu um formato que o desktop já não consegue interpretar.
Antes de adicionar ao Git, fazer revisão manual e independente da ausência de dados
reais e registrar a procedência sintética/anonimizada no manifesto, sem identificar
a pessoa original. Não adicionar arquivos reais nesta tarefa.

Preservar o esperado: uma mudança no candidato não autoriza regenerá-lo. Atualizações
exigem justificativa, revisão funcional e novo caso de regressão. Reportar
cobertura ausente explicitamente; uma fixture de DDL não comprova equivalência de
parsers, TXT ou migração operacional.
