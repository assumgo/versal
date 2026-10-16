# Contrato de equivalência de parsers e TXT

Este documento estabelece a condição de entrada para uma migração futura; não
implementa parser, exportador ou carga de dados. O desktop continua operacional.
O [contrato de esquema](legacy-schema-compatibility.md) rege a preservação de
campos, IDs BIGINT, vínculos, competência textual e sequências no PostgreSQL.

## Corpus e referência

Antes de extrair funções puras de `app.py`, preparar casos PDF, XLS e XLSX
anonimizados, os resultados intermediários esperados e o TXT produzido pelo desktop
com esses mesmos arquivos. Seguir as [regras das fixtures](../backend/tests/fixtures/README.md).
A saída de referência deve ser revisada pelo responsável pela folha, com versão
ou commit do desktop e parâmetros completos de execução. Não tratar comportamento
suspeito como regra: registrar divergência e decisão antes de atualizar a referência.

Cada caso terá manifesto com identificador, formato/layout, versão do desktop,
configuração de empresa/competência, parâmetros contábeis/financeiros, hashes SHA-256
dos arquivos, contagens, totais esperados, resultado ou erro esperado e justificativa.
Fixar relógio e demais entradas variáveis quando influenciarem o resultado.
Não gerar o esperado com o próprio código web submetido ao teste.

## Cobertura mínima antes da extração

| Grupo | Casos obrigatórios |
| --- | --- |
| Entrada | Cada layout real identificado de PDF/XLS/XLSX; acentos, espaços, células vazias e múltiplas páginas/abas conforme suportado |
| Escopo | Duas empresas, duas competências, matrícula/CPF e código de rubrica repetidos entre empresas |
| Valores | Zero, negativos, centavos, grandes valores, separadores locais e precisão adicional quando aceita pelo desktop |
| Histórico | Campos opcionais nulos, repetição aceita, CPF/CNPJ formatados e linhas sem cadastro correspondente |
| Falhas | Arquivo vazio, truncado ou formato inválido, campos obrigatórios ausentes e empresa/competência divergentes |
| TXT | Cada layout exportado (incluindo Siagri/Aliare quando aplicável), registros de cabeçalho/detalhe/rodapé e limites de largura |

Adicionar casos para cada defeito encontrado. Casos ainda não conhecidos devem
ficar como lacunas explícitas, nunca como layouts presumidos homologados.

## Comparação e critérios de aprovação

1. Executar desktop e candidato sobre a mesma fixture e configuração, em ambiente
   isolado, sem gravações no banco operacional nem envio ao sistema de destino.
2. Comparar empresa e competência, identidade e campos dos colaboradores, rubricas,
   referências, tipos, contas, centros de custo e cada valor/líquido por linha.
   Conferir contagens, duplicatas, vínculos e totais por empresa/competência/rubrica.
   Usar `Decimal` a partir de texto, nunca `float`; tolerância monetária zero.
3. Não remover duplicatas, pontuação, espaços, zeros à esquerda nem reordenar
   linhas silenciosamente. Para uma estrutura declaradamente sem ordem, comparar
   multiconjuntos com multiplicidade; documentar essa regra no manifesto.
4. Comparar TXT byte a byte: encoding, BOM, quebras CRLF/LF, espaços finais,
   preenchimento, largura em bytes/caracteres conforme layout, ordenação, sinais,
   casas decimais, cabeçalhos e rodapés. Hash igual comprova igualdade do arquivo.
   Campos variáveis só podem ser normalizados com regra prévia, precisa e revisada
   no manifesto; conservar também os arquivos originais e o diff sem normalização.
5. Para entradas inválidas, comparar categoria do erro, ausência de saída exportável
   e ausência de persistência parcial. Na futura API, testar também RBAC e bloqueio
   entre empresas; o parser não substitui autorização no servidor.

A aprovação exige todos os casos do corpus passando, nenhuma divergência sem
resolução e revisão do responsável funcional. Registrar relatório com versões,
comandos, hashes, diferenças por campo/posição de byte e decisão de cada diferença.
Uma alteração intencional exige novo esperado revisado e teste de regressão,
sem sobrescrever a referência apenas para tornar a suíte verde.

## Conferência e migração futura

Extrair primeiro funções puras, preservando o desktop. Executar a web em modo de
conferência sobre cópias autorizadas, sem substituir exportações oficiais. Definir
com o responsável um período representativo, incluindo fechamento de competência;
a troca depende de equivalência comprovada e aprovação registrada. Em divergência,
manter o desktop e interromper a adoção do candidato, preservando os relatórios.

A carga SQLite é uma etapa separada: obter cópia consistente e backup verificado,
diagnosticar órfãos e vínculos entre empresas, preservar IDs/campos sem renumerar ou
descartar registros e sincronizar sequências em janela sem inserções. Reconciliar
contagens, vínculos e decimais conforme o contrato de esquema antes de autorizar
qualquer corte. Não executar essa carga, reversão ou restauração como parte da fase 1.
