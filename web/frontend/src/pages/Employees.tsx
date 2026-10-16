import { DataTable } from '../components/DataTable';
const rows = [{ id: '001', name: 'Pessoa de exemplo', cpf: '000.000.000-00', registration: '0001', role: 'Auxiliar administrativo', cost: 'Administrativo', account: '10001', status: 'Ativo' }];
export function Employees() {
  return <><div className="page-heading"><div><p className="eyebrow">CADASTROS</p><h1>Colaboradores</h1><p>Exemplo visual dos colaboradores da empresa ativa. Dados fictícios.</p></div></div><section className="panel"><DataTable caption="Colaboradores cadastrados" rows={rows} rowKey={row => row.id} columns={[
    { key: 'id', title: 'ID', render: row => row.id }, { key: 'name', title: 'Nome', render: row => row.name }, { key: 'cpf', title: 'CPF', render: row => row.cpf }, { key: 'registration', title: 'Matrícula', render: row => row.registration }, { key: 'role', title: 'Cargo', render: row => row.role }, { key: 'cost', title: 'Centro de custo', render: row => row.cost }, { key: 'account', title: 'Código do correntista', render: row => row.account }, { key: 'status', title: 'Status', render: row => <span className="status-badge success">{row.status}</span> },
  ]} /></section></>;
}
