import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { App } from '../App';

async function enterAs(name: RegExp) {
  render(<App />);
  await userEvent.click(screen.getByRole('button', { name }));
}

describe('página inicial', () => {
  it('mostra só os atalhos dos grupos de quem entrou', async () => {
    await enterAs(/Acesso geral/);
    expect(screen.getByRole('heading', { name: 'Página inicial' })).toBeVisible();
    expect(screen.getByRole('link', { name: /Documentos/ })).toBeVisible();
    expect(screen.queryByRole('link', { name: /Folha/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Pessoas/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Projetos/ })).not.toBeInTheDocument();
    expect(document.body.innerHTML).not.toContain('sites/folha');
    expect(document.body.innerHTML).not.toContain('sites/projetos');
    expect(screen.getByRole('heading', { name: 'Comunicados' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Quadro do Teams' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Prazos do fechamento de novembro' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Manutenção no compartilhamento nesta sexta' })).toBeVisible();
  });

  it('troca a grade quando a conta muda', async () => {
    await enterAs(/Time financeiro/);
    expect(screen.getByRole('link', { name: /Folha/ })).toBeVisible();
    expect(screen.queryByRole('link', { name: /Pessoas/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Conta: Time financeiro' }));
    await userEvent.click(screen.getByRole('menuitem', { name: /RH e operação/ }));
    expect(screen.getByRole('link', { name: /Pessoas/ })).toBeVisible();
    expect(screen.getByRole('link', { name: /Operação/ })).toBeVisible();
    expect(screen.queryByRole('link', { name: /Folha/ })).not.toBeInTheDocument();
    expect(document.body.innerHTML).not.toContain('sites/folha');
  });

  it('abre o site permitido e recusa o endereço direto sem o grupo', async () => {
    await enterAs(/Time financeiro/);
    await userEvent.click(screen.getByRole('link', { name: /Folha/ }));
    expect(screen.getByRole('heading', { name: 'Folha' })).toBeVisible();
    expect(screen.getByRole('link', { name: 'Abrir site' })).toHaveAttribute('href', 'https://sharepoint.exemplo/sites/folha');
    act(() => {
      window.history.pushState({}, '', '/atalhos/pessoas');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
    expect(screen.getByRole('heading', { name: 'Pessoas' })).toBeVisible();
    expect(screen.getByText(/não está no seu acesso/i)).toBeVisible();
    expect(screen.queryByRole('link', { name: 'Abrir site' })).not.toBeInTheDocument();
    expect(document.body.innerHTML).not.toContain('sites/pessoas');
  });
});
