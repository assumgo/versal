import { beforeEach, describe, expect, it } from 'vitest';
import { addShortcut, listShortcuts } from './store';

describe('atalhos incluídos pelo administrador', () => {
  beforeEach(() => localStorage.removeItem('intranet.shortcuts'));

  it('recusa nome vazio, endereço inseguro e grupo ausente', () => {
    expect(addShortcut({ label: '  ', hint: '', href: 'https://sharepoint.exemplo/sites/a', groups: ['todos'], icon: 'documents' }).ok).toBe(false);
    expect(addShortcut({ label: 'Contratos', hint: '', href: 'javascript:alert(1)', groups: ['todos'], icon: 'documents' }).ok).toBe(false);
    expect(addShortcut({ label: 'Contratos', hint: '', href: 'https://sharepoint.exemplo/sites/contratos', groups: [], icon: 'documents' }).ok).toBe(false);
    expect(listShortcuts().some(item => item.label === 'Contratos')).toBe(false);
  });

  it('acrescenta o atalho com o endereço informado', () => {
    const result = addShortcut({ label: 'Contratos', hint: 'Minutas', href: 'https://sharepoint.exemplo/sites/contratos', groups: ['financeiro'], icon: 'documents' });
    expect(result.ok).toBe(true);
    const created = listShortcuts().find(item => item.label === 'Contratos');
    expect(created?.href).toBe('https://sharepoint.exemplo/sites/contratos');
    expect(created?.groups).toEqual(['financeiro']);
  });
});