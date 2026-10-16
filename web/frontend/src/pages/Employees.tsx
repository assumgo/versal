import { useCallback } from 'react';
import { employees, type EmployeeInput } from '../api/employees';
import type { Company } from '../api/companies';
import { CrudScreen } from '../components/CrudScreen';
import { Alert } from '../components/Alert';
const fields = [{ key: 'nome', label: 'Nome' }, { key: 'cpf', label: 'CPF' }, { key: 'matricula', label: 'Matrícula' }, { key: 'cargo', label: 'Cargo' }, { key: 'centro_custo', label: 'Centro de custo' }, { key: 'codigo_correntista', label: 'Código do correntista' }];
export function Employees({ company, canWrite }: { company: Company | null; canWrite: boolean }) {
  const load = useCallback(() => employees.list(company!.id), [company?.id]);
  if (!company) return <><h1>Colaboradores</h1><Alert>Selecione uma empresa.</Alert></>;
  return <><Alert>{company.status === 'Inativa' ? 'Empresa inativa: disponível somente para consulta.' : `Colaboradores de ${company.razao ?? company.id}`}</Alert><CrudScreen key={`${company.id}:${company.status}`} title="Colaboradores" caption="Colaboradores cadastrados" createLabel="Novo colaborador" fields={fields} statuses={['Ativo', 'Inativo']} canWrite={canWrite && company.status !== 'Inativa'} load={load} save={(data, id) => employees.save(company.id, data as EmployeeInput, id)} remove={id => employees.remove(company.id, id)} removeLabel="Excluir" /></>;
}
