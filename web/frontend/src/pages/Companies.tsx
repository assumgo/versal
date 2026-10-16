import { companies, type CompanyInput } from '../api/companies';
import { CrudScreen } from '../components/CrudScreen';
const fields = [{ key: 'codigo_siagri', label: 'Código Siagri', required: true }, { key: 'razao', label: 'Razão social', required: true }, { key: 'fantasia', label: 'Nome fantasia' }, { key: 'cnpj', label: 'CNPJ' }];
export function Companies({ canWrite, onChanged }: { canWrite: boolean; onChanged: () => void }) {
  return <CrudScreen title="Empresas" caption="Empresas cadastradas" createLabel="Nova empresa" fields={fields} statuses={['Ativa', 'Inativa']} canWrite={canWrite} load={companies.list} save={(data, id) => companies.save(data as CompanyInput, id)} remove={companies.remove} removeLabel="Inativar" onChanged={onChanged} />;
}
