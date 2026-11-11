import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';

describe('página inicial', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('abre com todos os atalhos e põe comunicados abaixo do quadro do Teams', () => {
    render(<App />);
    for (const name of ['Documentos', 'Pessoas', 'Benefícios', 'Folha', 'Operação', 'Projetos']) {
      expect(screen.getByRole('button', { name: new RegExp(name) })).toBeVisible();
    }
    expect(document.body.innerHTML).not.toContain('sites/folha');
    const sections = screen.getAllByRole('heading', { level: 2 }).map(heading => heading.textContent);
    expect(sections).toEqual(['Atalhos', 'Quadro do Teams', 'Comunicados']);
    expect(screen.getByRole('heading', { name: 'Prazos do fechamento de novembro' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Manutenção no compartilhamento nesta sexta' })).toBeVisible();
  });

  it('abre o site quando há permissão e mostra o aviso quando não há', async () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null);
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /Documentos/ }));
    expect(open).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog', { name: 'Documentos' })).toHaveTextContent('Você não tem permissão para acessar este local.');
    await userEvent.click(screen.getByRole('button', { name: 'Fechar' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Conta: Visitante' }));
    await userEvent.click(screen.getByRole('menuitem', { name: /Time financeiro/ }));
    await userEvent.click(screen.getByRole('button', { name: /Folha/ }));
    expect(open).toHaveBeenCalledWith('https://sharepoint.exemplo/sites/folha', '_blank', 'noopener,noreferrer');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /Pessoas/ }));
    expect(screen.getByRole('dialog', { name: 'Pessoas' })).toBeVisible();
    expect(open).toHaveBeenCalledTimes(1);
  });

  it('deixa o administrador incluir o endereço de um atalho novo', async () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null);
    render(<App />);
    expect(screen.queryByRole('button', { name: 'Incluir atalho' })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Conta: Visitante' }));
    await userEvent.click(screen.getByRole('menuitem', { name: /Time financeiro/ }));
    expect(screen.queryByRole('button', { name: 'Incluir atalho' })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Conta: Time financeiro' }));
    await userEvent.click(screen.getByRole('menuitem', { name: /Administrador/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Incluir atalho' }));
    await userEvent.type(screen.getByRole('textbox', { name: 'Nome' }), 'Contratos');
    await userEvent.type(screen.getByRole('textbox', { name: 'Endereço' }), 'javascript:alert(1)');
    await userEvent.click(screen.getByRole('button', { name: 'Salvar atalho' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Informe um endereço http ou https.');

    const address = screen.getByRole('textbox', { name: 'Endereço' });
    await userEvent.clear(address);
    await userEvent.type(address, 'https://sharepoint.exemplo/sites/contratos');
    await userEvent.click(screen.getByRole('checkbox', { name: 'Toda a empresa' }));
    await userEvent.click(screen.getByRole('checkbox', { name: 'Financeiro' }));
    await userEvent.click(screen.getByRole('button', { name: 'Salvar atalho' }));
    expect(screen.queryByRole('dialog', { name: 'Incluir atalho' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Contratos/ })).toBeVisible();
    expect(document.body.innerHTML).not.toContain('sites/contratos');

    await userEvent.click(screen.getByRole('button', { name: 'Conta: Administrador' }));
    await userEvent.click(screen.getByRole('menuitem', { name: /Time financeiro/ }));
    await userEvent.click(screen.getByRole('button', { name: /Contratos/ }));
    expect(open).toHaveBeenCalledWith('https://sharepoint.exemplo/sites/contratos', '_blank', 'noopener,noreferrer');
  });
});
