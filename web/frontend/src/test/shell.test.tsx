import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { AppShell } from '../App';
import { Dashboard } from '../pages/Dashboard';
import { useState } from 'react';
import type { Page } from '../components/Sidebar';
function App() { const [page, setPage] = useState<Page>('Dashboard'); return <AppShell company="Empresa Demonstração" competence="2026-10" activePage={page} onNavigate={setPage}><p>dados simulados</p>{page === 'Dashboard' ? <Dashboard /> : <h1>{page}</h1>}</AppShell>; }

const navigation = ['Dashboard', 'Empresas', 'Colaboradores', 'Importação Folha', 'Plano de Contas', 'Rubricas', 'Encargos da Empresa', 'Parametrização Contábil', 'Parametrização Financeira', 'Exportação TXT', 'Backup'];

describe('Versal shell', () => {
  it('preserves desktop navigation order and updates the active page', async () => {
    render(<App />);
    const nav = screen.getByRole('navigation', { name: 'Navegação principal' });
    expect(within(nav).getAllByRole('button').map(item => item.textContent)).toEqual(navigation);
    expect(within(nav).getByRole('button', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page');
    await userEvent.click(within(nav).getByRole('button', { name: 'Empresas' }));
    expect(screen.getByRole('heading', { name: 'Empresas', level: 1 })).toBeVisible();
    expect(within(nav).getByRole('button', { name: 'Empresas' })).toHaveAttribute('aria-current', 'page');
  });
  it('shows the original dashboard metrics with clearly identified demo data', () => {
    render(<App />);
    for (const label of ['Colaboradores ativos', 'Verbas parametrizadas', 'Importações', 'Pendências']) {
      expect(screen.getByRole('heading', { name: label })).toBeVisible();
    }
    expect(screen.getByText(/dados simulados/i)).toBeVisible();
    expect(screen.getByRole('region', { name: 'Últimas importações' })).toHaveClass('table-scroll');
  });
  it('opens the drawer and closes on navigation, outside click and Escape', async () => {
    render(<App />);
    const trigger = screen.getByRole('button', { name: 'Abrir menu' });
    await userEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    await userEvent.click(screen.getByRole('button', { name: 'Colaboradores' }));
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(trigger);
    await userEvent.keyboard('{Escape}');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(trigger);
    await userEvent.click(screen.getByRole('button', { name: 'Fechar menu pelo fundo' }));
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });
  it('accepts company, competence and arbitrary page content', () => {
    render(<AppShell company="Empresa de teste" competence="2026-09" activePage="Dashboard" onNavigate={() => {}}><h1>Conteúdo da página</h1></AppShell>);
    expect(screen.getByLabelText('Empresa ativa')).toHaveValue('Empresa de teste');
    expect(screen.getByLabelText('Competência ativa')).toHaveValue('2026-09');
    expect(screen.getByRole('heading', { name: 'Conteúdo da página' })).toBeVisible();
  });
});
