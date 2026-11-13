import { ThemeToggle } from './ThemeToggle';
import { IconSearch } from './icons';

type TopBarProps = {
  menuOpen: boolean;
  onOpenMenu: () => void;
  search: string;
  onSearch: (value: string) => void;
  ctaLabel: string;
  onCta?: () => void;
};

export function TopBar({
  menuOpen,
  onOpenMenu,
  search,
  onSearch,
  ctaLabel,
  onCta,
}: TopBarProps) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="menu-trigger"
        aria-label="Abrir menu"
        aria-controls="sidebar"
        aria-expanded={menuOpen}
        onClick={onOpenMenu}
      >
        ☰
      </button>

      <label className="search-box">
        <IconSearch />
        <input
          type="search"
          placeholder="Buscar por nº de série, colaborador, NF ou equipamento"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
        />
      </label>

      <div className="topbar-actions">
        <ThemeToggle />
        <button type="button" className="btn btn-primary" onClick={onCta}>
          {ctaLabel}
        </button>
      </div>
    </header>
  );
}
