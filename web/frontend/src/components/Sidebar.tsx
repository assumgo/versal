export const pages = ['Dashboard', 'Empresas', 'Colaboradores', 'Importação Folha', 'Plano de Contas', 'Rubricas', 'Encargos da Empresa', 'Parametrização Contábil', 'Parametrização Financeira', 'Exportação TXT', 'Backup'] as const;
export type Page = typeof pages[number];

type Props = { company: string; activePage: Page; open: boolean; onNavigate: (page: Page) => void; onClose: () => void };
export function Sidebar({ company, activePage, open, onNavigate, onClose }: Props) {
  return <aside id="sidebar" className={`sidebar ${open ? 'is-open' : ''}`}>
    <button className="drawer-close" onClick={onClose} aria-label="Fechar menu">×</button>
    <div className="brand"><img src="/assets/logo_versal_agro.png" alt="Versal Agro Contabilidade" /><strong>Integrador Folha TXT</strong></div>
    <div className="company-hint"><span>Empresa atual</span><strong>{company}</strong></div>
    <nav aria-label="Navegação principal">{pages.map(page => <button key={page} aria-current={activePage === page ? 'page' : undefined} onClick={() => onNavigate(page)}>{page}</button>)}</nav>
    <footer>Versal Folha TXT · Web<br />© Versal Agro Contabilidade</footer>
  </aside>;
}
