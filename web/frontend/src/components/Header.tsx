type Props = { company: string; competence: string; menuOpen: boolean; onOpenMenu: () => void };
export function Header({ company, competence, menuOpen, onOpenMenu }: Props) {
  return <header className="top-header">
    <button className="menu-trigger" aria-label="Abrir menu" aria-controls="sidebar" aria-expanded={menuOpen} onClick={onOpenMenu}>☰</button>
    <div className="context-field"><label htmlFor="active-company">Empresa ativa</label><input id="active-company" value={company} readOnly /></div>
    <div className="context-field competence"><label htmlFor="active-competence">Competência ativa</label><input id="active-competence" type="month" value={competence} readOnly /></div>
    <span className="demo-badge">Demonstração</span>
  </header>;
}
