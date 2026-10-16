import { DataTable } from '../components/DataTable';
import { StatCard } from '../components/StatCard';
const imports = [
  { id: 1, file: 'Extrato mensal · exemplo.xlsx', type: 'Folha mensal', date: '15/10/2026', rows: 248, status: 'Conferido' },
  { id: 2, file: 'Provisão de férias · exemplo.pdf', type: 'Provisão de férias', date: '14/10/2026', rows: 124, status: 'Em conferência' },
  { id: 3, file: 'Provisão de 13º · exemplo.xlsx', type: 'Provisão de 13º', date: '14/10/2026', rows: 124, status: 'Conferido' },
];
export function Dashboard() {
  return <><div className="page-heading"><div><p className="eyebrow">VISÃO GERAL</p><h1>Dashboard</h1><p>Acompanhe a preparação da folha e a conferência dos dados do mês.</p></div><span className="period-tag">Outubro / 2026</span></div>
    <div className="stats-grid"><StatCard title="Colaboradores ativos" value="124" detail="Na empresa selecionada" /><StatCard title="Verbas parametrizadas" value="38" detail="Configurações da competência" /><StatCard title="Importações" value="3" detail="Arquivos demonstrativos" /><StatCard title="Pendências" value="2" detail="Aguardando conferência" /></div>
    <section className="panel"><div className="section-heading"><div><h2>Últimas importações</h2><p>Arquivos e situação da conferência na competência ativa.</p></div><span className="count-badge">3 arquivos</span></div><DataTable caption="Últimas importações" rows={imports} rowKey={row => row.id} columns={[
      { key: 'file', title: 'Arquivo', render: row => <strong>{row.file}</strong> },
      { key: 'type', title: 'Tipo', render: row => row.type },
      { key: 'date', title: 'Importado em', render: row => row.date },
      { key: 'rows', title: 'Registros', render: row => row.rows },
      { key: 'status', title: 'Situação', render: row => <span className={`status-badge ${row.status === 'Conferido' ? 'success' : 'pending'}`}>{row.status}</span> },
    ]} /></section>
    <section className="panel month-summary"><h2>Conferência da competência</h2><p>Revise as rubricas e a parametrização antes de gerar o arquivo TXT.</p><div className="summary-line"><span>Folha mensal</span><span className="status-badge success">Conferida</span></div><div className="summary-line"><span>Parametrização contábil e financeira</span><span className="status-badge pending">2 pendências</span></div></section>
  </>;
}
