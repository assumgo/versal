import { DataTable } from '../components/DataTable';
const rows = [{ id: '001', code: '1001', name: 'Empresa Demonstração Ltda.', cnpj: '00.000.000/0000-00', status: 'Ativa' }];
export function Companies() {
  return <><div className="page-heading"><div><p className="eyebrow">CADASTROS</p><h1>Empresas</h1><p>Exemplo visual do cadastro de empresas. Dados fictícios.</p></div></div><section className="panel"><DataTable caption="Empresas cadastradas" rows={rows} rowKey={row => row.id} columns={[
    { key: 'id', title: 'ID', render: row => row.id }, { key: 'code', title: 'Código Siagri', render: row => row.code }, { key: 'name', title: 'Razão social', render: row => row.name }, { key: 'cnpj', title: 'CNPJ', render: row => row.cnpj }, { key: 'status', title: 'Status', render: row => <span className="status-badge success">{row.status}</span> },
  ]} /></section></>;
}
