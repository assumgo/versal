# Formatos do desktop e corpus inicial

Referência: `app.py` da distribuição desktop 2.18. Seu SHA-256 e os leitores
utilizados estão nos manifestos. O mapeamento foi feito por leitura do código e
execução isolada das funções de parsing, sem iniciar Qt ou acessar banco.

## Inventário

| Família | Entrada | Funções / identificação |
| --- | --- | --- |
| Extrato mensal | PDF | `parse_pdf` → `parse_extrato_text`; pdfplumber e fallback PyMuPDF; sem OCR |
| Extrato mensal | XLS/XLSX | `parse_excel` → `parse_extrato_rows`; primeira aba; prioridade de EXTRATO MENSAL sobre menções a 13º |
| Provisão de 13º | XLS/XLSX | `parse_provisao_rows(..., '13')`; título; linha Provisionado no mês; valores nas colunas 15/17/19/25/27/30 (base zero) |
| Provisão de férias | XLS/XLSX | `parse_provisao_rows(..., 'FERIAS')`; mesma estrutura fixa |
| Encargos da empresa | PDF/XLS/XLSX | `parse_encargos_file`; empregados versus contribuintes; FGTS, INSS_EMP, INSS_TERC e RAT |
| Plano de contas Siagri | XLS/XLSX | `parse_plano_contas_excel`; cabeçalhos ou posições fixas; contas de 10–12 dígitos; última duplicata prevalece |
| Cadastro de rubricas | XLS/XLSX | `App.import_rubrics_xlsx`; Código + Descrição/Nome; inclui/atualiza cadastro e deriva flags do plano |

`parse_excel` tenta calamine e depois pandas. `_read_excel_rows_any`, usado em
outros fluxos, acrescenta xlrd e conversão por LibreOffice. Não são a mesma cadeia.
PDF digitalizado sem texto não tem OCR implementado. Não presumir suporte.

## Modelos encontrados e conferidos

A pasta de modelos indicada pelo usuário contém dois Extratos Mensais (PDF e XLS)
e modelos TXT contábil e financeiro. Os originais não foram copiados para o Git.
Com calamine 0.9.0 e pdfplumber 0.11.10, as funções originais leram diretamente
ambos os extratos: 4 colaboradores, 11 rubricas, empresa e competência detectadas.
Isso corrige a investigação inicial com xlrd/pdftotext/LibreOffice: a ausência de
competência na cópia convertida não demonstra defeito no arquivo original.
O ambiente Windows e suas versões efetivas de bibliotecas ainda não foram aferidos.

Os TXT servem como referências de estrutura, não como esperados dos extratos:
a correspondência entre arquivos, competência e parâmetros não foi estabelecida.

| Modelo TXT | Registros e larguras observadas (caracteres sem CRLF) |
| --- | --- |
| Contábil | FOL 32; CON 294; CUS 31; COR 33 |
| Financeiro | CAB 104; PAR 337; CON 294; CUS 31; COR 33 |

Ambos têm CRLF. O contábil foi identificado como texto ISO-8859 e o financeiro
como ASCII; a codificação exata do contábil requer confirmação. O exportador do
código consultado usa UTF-8 e `write_text('\n'.join(...))`: não considerar os
modelos equivalentes byte a byte sem esclarecer versão, encoding e configuração.
Os modelos de importação XLS/XLSX das outras famílias não estavam nessa pasta.

## Corpus entregue

Diretório: `web/backend/tests/fixtures/parser_equivalence/`.
Todos os documentos são inteiramente sintéticos, criados do zero; não são cópias
com tarjas nem substituições sobre arquivos reais. Nomes, documentos repetitivos,
empresa, matrículas e valores foram inventados. PDF tem fonte incorporada e duas
páginas no caso normal. Excel tem uma aba, sem fórmulas, comentários ou dados ocultos.

| Caso | Resultado observado nas funções do desktop |
| --- | --- |
| extrato_pdf | 2 colaboradores, 4 rubricas; divergência de código descrita abaixo |
| extrato_xls / extrato_xlsx | 2 colaboradores, 4 rubricas; JSONs idênticos |
| extrato_xlsx_edge | 2 colaboradores, 6 rubricas; negativos mantidos, zero e repetição de código/valor descartados |
| extrato_pdf_accent | 2 colaboradores, apenas 2 descontos: salário com Á não é capturado |
| extrato_pdf_empty | Relatório válido sem colaboradores: lista vazia, competência presente |
| extrato_xlsx_empty | Planilha legível sem cabeçalho: lista vazia, competência ausente |

Cada caso contém entrada binária, `expected.json` congelado e `manifest.json`
com hashes, referência, ambiente, contagens e totais. Decimais são serializados
como texto, com comparação integral ordenada e tolerância zero. Os líquidos são
valores independentes informados no documento, não recalculados das rubricas.

### Divergências preservadas, aguardando decisão

1. **Á na descrição PDF:** a expressão regular original aceita vários acentos,
   mas não Á. SALÁRIO BASE não produz a rubrica; SALARIO BASE produz. O caso
   `extrato_pdf_accent` registra essa omissão, sem corrigi-la na saída esperada.
2. **CC antes da rubrica no PDF:** no layout sintético, o parser captura `0001`
   do CC como código e `001 SALARIO BASE` como descrição da primeira rubrica.
   No Excel, código `001` e descrição `SALARIO BASE` são preservados. Os valores
   e contagens coincidem, mas a identidade da rubrica diverge. Não homologar só
   por totais; isso exige conferência no desktop Windows e decisão funcional.
3. **Duplicatas e zeros:** a leitura Excel suprime duplicata com mesmo código e
   valor no colaborador e ignora valor zero. Esse comportamento pertence ao
   parser; não confundir com a conferência web de movimentos já persistidos,
   que preserva a multiplicidade existente no banco.

Esses resultados caracterizam o código de referência; não são regras desejadas
aprovadas. Os manifestos estão como `pending_functional_and_windows_review`.
Nenhuma saída TXT foi fabricada como se fosse exportada pelo desktop: falta a
configuração reproduzível de contas, colaboradores, parâmetros e relógio.

## Reprodução

As ferramentas opcionais ficam separadas de `requirements.txt` da aplicação:

```bash
python -m pip install -r web/backend/tests/fixtures/parser_equivalence/requirements-corpus.txt
python web/backend/tests/fixtures/parser_equivalence/verify_desktop.py --desktop-source /caminho/desktop/app.py
```

O verificador só define as funções de topo do arquivo confiável indicado; não
executa inicialização global, classes, Qt, banco ou interface. Executar apenas com
código de desktop confiável. Ele compara as entradas com os esperados congelados.
Executá-lo no Windows com a mesma fonte e comparar os resultados é a próxima
verificação necessária. A referência Linux não substitui essa confirmação.

`build_corpus.py` reproduz somente as entradas (fonte DejaVu Sans no caminho Linux
indicado no script); nunca reescreve esperados. As propriedades e timestamps do
XLSX e PDF são fixados. A captura inicial é uma ação explícita:
`verify_desktop.py --desktop-source ... --capture-reference`; arquivos de saída
são criados exclusivamente, sem sobrescrever referências existentes.

Os testes de integridade não precisam de bibliotecas de PDF/Excel nem do desktop:

```bash
cd web/backend
python -m pytest tests/test_parser_corpus.py -q
```

## API Python dos parsers web

O backend possui leitores de **Extrato Mensal**, extraídos da referência 2.18
identificada acima, em `app/parsers/`. Não importam Qt, configuração da API,
SQLAlchemy ou o arquivo desktop; não acessam banco nem alteram a entrada.

Na pasta `web/backend/`, com as dependências de `requirements.txt` instaladas:

```python
from pathlib import Path
from app.parsers import parse_excel, parse_pdf, UnsupportedLayoutError

resultado_pdf = parse_pdf(Path('extrato.pdf'))
resultado_excel = parse_excel(Path('extrato.xlsx'))  # também aceita XLS
```

Ambas as funções aceitam `str` ou `Path` de arquivo local existente. URLs não são
buscadas; caminho ausente recebe `FileNotFoundError` antes de acionar os leitores.
Devolvem `ParsedStatement`, um dicionário tipado declarado em
`app/parsers/types.py`. Campos: `competencia`,
`empresa` (`codigo_siagri`, `razao`, `cnpj`), `tipo_importacao` (`Extrato`) e
`colaboradores`. Cada colaborador contém matrícula, nome, CPF, situação, cargo,
centro de custo, líquido e rubricas. Cada rubrica contém código, descrição,
referência, valor e tipo, com as mesmas chaves do JSON congelado. Valores e
líquidos são `Decimal` em memória; serializar como texto ao produzir JSON,
sem convertê-los para float. As conversões e o arredondamento monetário do
desktop permanecem; isso não garante precisão que o parser original não oferecia.

O PDF usa pdfplumber e, somente em exceção, PyMuPDF. Um documento sem texto não
aciona fallback e não tem OCR. Excel usa calamine e, em exceção, pandas com
openpyxl/XLSX ou xlrd/XLS. Ambos leem somente a primeira aba. Erros do segundo
leitor propagam sem resultado parcial. Arquivo legível sem cabeçalho mantém o
resultado vazio caracterizado; lista vazia não prova validade de um layout.

EXTRATO MENSAL tem prioridade sobre menções a 13º. Um título reconhecido de
provisão sem título de Extrato lança `UnsupportedLayoutError`; provisões e
encargos não fazem parte desta API. As divergências de acentos, CC e deduplicação
documentadas acima continuam presentes. Dados de empresa são apenas detectados:
não selecionam empresa no banco e não substituem a autorização de futura importação.

Versões usadas na validação Linux/Python 3.12.3:

| Biblioteca | Versão |
| --- | --- |
| pdfplumber | 0.11.10 (fixada em requirements) |
| python-calamine | 0.9.0 (fixada em requirements) |
| PyMuPDF | 1.28.2 |
| pandas | 2.3.3 |
| openpyxl | 3.1.5 |
| xlrd | 2.0.2 |

Os fallbacks possuem limites de versão em `requirements.txt`; a tabela registra
o ambiente efetivamente testado, sem representar homologação de todas as versões.

```bash
cd web/backend
.venv/bin/python -m pytest tests/test_extrato_parsing.py tests/test_extrato_pdf.py tests/test_extrato_excel.py tests/test_parser_corpus.py tests/test_parser_isolation.py -q
```

Os sete resultados congelados são comparados integralmente, em ordem, com
decimais em texto e tolerância zero. Há testes de fallback real para XLS/XLSX
e PDF, prioridade de títulos, rejeição de provisões, primeira aba, isolamento
de Qt/banco e preservação dos arquivos. Nenhum esperado é regenerado por eles.
Não há upload HTTP, prévia de importação, persistência ou exportação nesta entrega.
A aprovação funcional e a conferência Windows dos manifestos continuam pendentes.

Verificação da extração em 2026-10-17: 51 testes focados passaram. O script
`bash web/backend/tests/run_postgres.sh`, executado com PostgreSQL 16 descartável,
passou os 296 testes nas duas execuções, antes e depois de reverter/reaplicar
as migrações; Alembic não detectou divergência de esquema. Os nove corpos de
funções puras foram também comparados por AST com a fonte desktop e são iguais.

## Lacunas

Faltam modelos e corpus de provisões, encargos, plano e rubricas; variantes de
layout reais, XLS não padrão e seus fallbacks; documentos truncados/corrompidos;
valores grandes, múltiplas abas e divergência de empresa/competência. Ausência de
movimentos não equivale a erro de arquivo corrompido. A extração web cobre somente
o Extrato Mensal; ainda não há validação de upload, persistência, exportação ou
homologação funcional nesta entrega.
