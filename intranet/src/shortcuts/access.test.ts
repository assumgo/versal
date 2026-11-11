import { describe, expect, it } from 'vitest';
import { findShortcut, shortcuts } from './catalog';
import { canAccess, safeHref, visibleShortcuts } from './access';

const folha = findShortcut('folha')!;
const documentos = findShortcut('documentos')!;

describe('acesso aos atalhos', () => {
  it('exige interseção entre os grupos do usuário e os do atalho', () => {
    expect(canAccess(['todos'], documentos)).toBe(true);
    expect(canAccess(['financeiro'], folha)).toBe(true);
    expect(canAccess(['todos'], folha)).toBe(false);
    expect(canAccess(['rh', 'financeiro'], folha)).toBe(true);
    expect(canAccess([], documentos)).toBe(false);
    expect(canAccess(['todos'], { groups: [] })).toBe(false);
  });

  it('omite da grade o atalho que a pessoa não pode abrir', () => {
    const labels = visibleShortcuts(['todos', 'rh'], shortcuts).map(item => item.id);
    expect(labels).toEqual(['documentos', 'pessoas', 'beneficios']);
    expect(labels).not.toContain('folha');
    expect(labels).not.toContain('projetos');
  });

  it('recusa endereço que não seja http(s)', () => {
    expect(safeHref('https://sharepoint.exemplo/sites/folha')).toBe('https://sharepoint.exemplo/sites/folha');
    expect(safeHref('javascript:alert(1)')).toBeNull();
    expect(safeHref('nota-interna')).toBeNull();
  });
});
