export const previewCompany = { id: 1, codigo_siagri: '901', razao: 'Empresa sintética', fantasia: null, cnpj: '00.000.000/0000-00', status: 'Ativa' };
export const previewResult = {
  company_id: 1, requested_competence: '09/2026', filename: 'input.pdf', size_bytes: 50, sha256: 'a'.repeat(64), status: 'ready' as const,
  issues: [{ code: 'homologation_pending', severity: 'warning' as const, message: 'Homologação pendente.' }],
  summary: { employees: 2, rubrics: 3, totals_by_type: { P: '20.00', D: '-1.25', E: '0' }, net_total: '123456789012345678901234567890.123456789' },
  statement: { competencia: '09/2026', tipo_importacao: 'Extrato' as const, empresa: { codigo_siagri: '901', razao: 'Empresa sintética', cnpj: '00.000.000/0000-00' }, colaboradores: [
    { matricula: '001', nome: 'Ana Sintética', cpf: '000.000.000-00', situacao: 'Ativo', cargo: 'Analista', centro_custo: '0001', liquido: '10.00', rubricas: [
      { codigo: '001', descricao: 'SALARIO BASE', referencia: '30,00', valor: '10.00', tipo: 'P' },
      { codigo: '001', descricao: 'SALARIO BASE', referencia: '30,00', valor: '10.00', tipo: 'P' }] },
    { matricula: '002', nome: 'João Fictício', cpf: '111.111.111-11', situacao: 'Ativo', cargo: '', centro_custo: '', liquido: '8.75', rubricas: [
      { codigo: '002', descricao: 'AJUSTE', referencia: '', valor: '-1.25', tipo: 'D' }] },
  ] },
};
