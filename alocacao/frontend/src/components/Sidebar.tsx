import { NavLink } from 'react-router-dom';
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

const items = [
  { to: '/', label: 'Dashboard', icon: IconDashboard, end: true },
  { to: '/cadastros', label: 'Cadastros', icon: IconCadastros },
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

  return (
    <aside id="sidebar" className={`sidebar${open ? ' open' : ''}`} aria-label="Navegação principal">
      <div className="brand">
        <img className="logo-full" src="/logo1.png" alt="Versal Agro Contabilidade" />
      </div>

      <ul className="nav-list">
        {items.map((item) => {
          const Icon = item.icon;
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
