# Extração dos parsers de Extrato Mensal

Status: proposta para revisão; implementação ainda não iniciada.

## Objetivo

Preparar a leitura web de Extrato Mensal PDF, XLS e XLSX por extração das
funções do desktop, comparando o resultado integral com o corpus congelado.
Esta entrega é a primeira parte da futura importação de folha: não inclui
upload HTTP, interface, persistência, criação de cadastros ou exportação TXT.
O desktop permanece operacional. A equivalência técnica com os sete casos
sintéticos não constitui homologação funcional ou Windows.

## Referência verificada

Fonte somente leitura: `/home/gabriel/Downloads/versal_folha_txt_v2_18/app.py`.
SHA-256: `ab2203e8b0e56550dfcd1baa84e4c6a89618809b06fa9b420d722ea8fc6905c2`.
O hash confere com todos os manifestos do corpus existente.
Não importar esse módulo na aplicação: sua inicialização carrega Qt e cria
diretórios. A aplicação web será independente da instalação desktop.

## Alternativas e escolha

1. Extrair os parsers de Extrato e seus auxiliares para módulos independentes.
   É a escolha proposta: permite testar equivalência sem envolver banco ou UI.
2. Transportar o leitor genérico completo, incluindo provisões. Amplia suporte
   aparente a famílias que ainda não têm corpus de referência.
3. Integrar upload e persistência na mesma entrega. Mistura diferenças de
   leitura com autorização, armazenamento e sincronização dos cadastros.

## Componentes e contrato

Criar módulos em `web/backend/app/parsers/`: tipos de saída, auxiliares de
conversão/identificação de empresa, leitura PDF e leitura Excel de Extrato.
Expor `parse_pdf(path)` e `parse_excel(path)` por uma interface pública única.
Os caminhos são arquivos locais disponibilizados pelo chamador; não há leitura
de URLs, extração de arquivos compactados ou armazenamento de uploads.

Usar TypedDict para documentar o resultado sem coerção ou preenchimento novo:
`competencia`, `empresa` (`codigo_siagri`, `razao`, `cnpj`), `tipo_importacao`
igual a `Extrato` e `colaboradores`. Cada colaborador contém `matricula`,
`nome`, `cpf`, `situacao`, `cargo`, `centro_custo`, `liquido` e `rubricas`.
Rubricas contêm `codigo`, `descricao`, `referencia`, `valor` e `tipo`.
`liquido` e `valor` são Decimal em memória; somente a comparação com JSON os
serializa como texto. Preservar a conversão e o arredondamento já praticados
pelo desktop; não acrescentar conversões monetárias para float.

Extrair `parse_extrato_text`, `parse_extrato_rows`, `parse_company_from_text`,
`br_to_decimal` e os auxiliares transitivamente necessários. Não copiar banco,
Qt, interface, exportadores ou rotinas de sincronização.

PDF usa pdfplumber e fallback PyMuPDF quando o leitor principal lança exceção.
Não acionar fallback apenas por resultado sem texto, conforme referência.
Excel usa calamine e fallback pandas, com openpyxl/XLSX e xlrd/XLS, mantendo
a primeira aba. Fixar pdfplumber 0.11.10 e python-calamine 0.9.0, versões do
corpus; declarar também as dependências dos fallbacks no backend e documentar
as versões utilizadas na validação. Não incluir ferramentas geradoras do
corpus como dependências de execução.

## Limites e erros

Preservar a prioridade de EXTRATO MENSAL sobre menções a 13º no cabeçalho.
Quando a identificação original indicar provisão de 13º ou férias sem título
de Extrato, lançar uma exceção específica de layout não suportado, sem executar
`parse_provisao_rows`. Não presumir suporte a provisões ou encargos.
Planilha legível sem cabeçalho continua produzindo o resultado vazio registrado
no corpus; não transformá-la em arquivo corrompido. A classificação detalhada
de layouts desconhecidos fica para o desenho de upload/prévia.

Erros dos leitores após esgotar fallback continuam sendo erros, sem saída parcial.
Não adicionar respostas HTTP nesta entrega. Não há OCR. Não selecionar empresa
no banco a partir do CNPJ detectado: o parser apenas devolve os dados lidos.
O futuro serviço de importação deverá validar empresa e competência autorizadas.

Manter as divergências documentadas: Á na descrição PDF, CC capturado como código
de rubrica e supressão de zeros/duplicatas no Excel. Os testes caracterizam esses
comportamentos; nenhuma correção nem alteração dos esperados é autorizada por
esta extração. A decisão funcional e a homologação Windows seguem pendentes.

## Verificação e critérios de conclusão

- Comparar o resultado completo e ordenado dos sete arquivos com seus JSONs
  congelados, incluindo campos vazios, identificadores, rubricas e decimais.
- Executar os testes de hashes e totais existentes sem regenerar referências.
- Exercitar fallback PDF e Excel com falhas controladas do leitor principal;
  verificar propagação da falha quando ambos os leitores falharem.
- Exercitar as duas famílias de provisão rejeitadas, prioridade de Extrato e
  leitura somente da primeira aba com casos sintéticos direcionados.
- Garantir que importar e executar os parsers não requer Qt, configuração de
  sessão ou conexão com banco. Não executar testes no banco operacional.
- Executar regressões do backend e registrar quais testes de integração
  eventualmente ficaram sem execução; usar PostgreSQL descartável se necessário.
- Documentar contrato, bibliotecas, comandos e limites no guia de formatos.

Sucesso significa equivalência nos casos disponíveis, testes dos limites e
independência do desktop. Upload, validação de contexto e persistência exigem
um desenho posterior; não estão implicitamente liberados por esta entrega.
