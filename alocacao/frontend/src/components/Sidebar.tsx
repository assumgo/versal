import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import {
  IconAlloc,
  IconCadastros,
  IconConfig,
  IconDashboard,
  IconEquipment,
  IconInvoice,
  IconTRE,
} from './icons';

const cadastroChildren = [
  { to: '/cadastros/categorias', label: 'Categorias' },
  { to: '/cadastros/colaboradores', label: 'Colaboradores' },
  { to: '/cadastros/fornecedores', label: 'Fornecedores' },
] as const;

const items = [
  { to: '/', label: 'Dashboard', icon: IconDashboard, end: true },
  { label: 'Cadastros', icon: IconCadastros, children: cadastroChildren },
  { to: '/configuracoes', label: 'Configurações', icon: IconConfig },
  { to: '/notas-fiscais', label: 'Notas Fiscais', icon: IconInvoice },
  { to: '/tres', label: 'TREs', icon: IconTRE },
  { to: '/alocacoes', label: 'Alocações', icon: IconAlloc },
  { to: '/equipamentos', label: 'Equipamentos', icon: IconEquipment },
] as const;

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

export function Sidebar({ open, onClose }: SidebarProps) {
  const auth = useAuth();
  const location = useLocation();
  const cadastrosActive = location.pathname.startsWith('/cadastros');
  const [cadastrosOpen, setCadastrosOpen] = useState(cadastrosActive);

  useEffect(() => {
    if (cadastrosActive) setCadastrosOpen(true);
  }, [cadastrosActive]);

  return (
    <aside id="sidebar" className={`sidebar${open ? ' open' : ''}`} aria-label="Navegação principal">
      <div className="brand">
        <img className="logo-full" src="/logo1.png" alt="Versal Agro Contabilidade" />
      </div>

      <ul className="nav-list">
        {items.map((item) => {
          const Icon = item.icon;
          if ('children' in item) {
            return (
              <li key={item.label} className="nav-group">
                <button
                  type="button"
                  className={`nav-item nav-parent${cadastrosActive ? ' active' : ''}`}
                  aria-expanded={cadastrosOpen}
                  onClick={() => setCadastrosOpen((value) => !value)}
                >
                  <Icon />
                  <span>{item.label}</span>
                  <span className={`nav-chevron${cadastrosOpen ? ' open' : ''}`} aria-hidden>
                    ▾
                  </span>
                </button>
                {cadastrosOpen && (
                  <ul className="nav-sublist">
                    {item.children.map((child) => (
                      <li key={child.to}>
                        <NavLink
                          to={child.to}
                          className={({ isActive }) => `nav-item nav-subitem${isActive ? ' active' : ''}`}
                          onClick={onClose}
                        >
                          <span>{child.label}</span>
                        </NavLink>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          }

          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={'end' in item ? item.end : false}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                onClick={onClose}
              >
                <Icon />
                <span>{item.label}</span>
              </NavLink>
            </li>
          );
        })}
      </ul>

      <div className="sidebar-footer">
        <div className="label">Conectado como</div>
        <div className="user-email">{auth.user?.email}</div>
        <button type="button" className="btn-danger-link" onClick={() => void auth.logout()}>
          Sair
        </button>
      </div>
    </aside>
  );
}
