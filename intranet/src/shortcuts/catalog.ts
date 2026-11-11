import type { ShortcutIcon } from './icons';

/**
 * Atalhos da página inicial. Substitua esta lista pelos sites internos.
 *
 * A página mostra todos os atalhos. `groups` só entra na hora do clique:
 * a pessoa abre o site se tiver pelo menos um desses grupos.
 * `todos` é o grupo de toda a empresa. Sem grupo compatível, um aviso
 * informa que não há permissão para o local.
 */
export type Shortcut = {
  id: string;
  label: string;
  hint: string;
  href: string;
  groups: readonly string[];
  icon: ShortcutIcon;
};

export const shortcuts: readonly Shortcut[] = [
  {
    id: 'documentos',
    label: 'Documentos',
    hint: 'Arquivos compartilhados da empresa',
    href: 'https://sharepoint.exemplo/sites/documentos',
    groups: ['todos'],
    icon: 'documents',
  },
  {
    id: 'pessoas',
    label: 'Pessoas',
    hint: 'Cadastros e documentos de RH',
    href: 'https://sharepoint.exemplo/sites/pessoas',
    groups: ['rh'],
    icon: 'people',
  },
  {
    id: 'beneficios',
    label: 'Benefícios',
    hint: 'Políticas e comprovantes',
    href: 'https://sharepoint.exemplo/sites/beneficios',
    groups: ['rh'],
    icon: 'benefits',
  },
  {
    id: 'folha',
    label: 'Folha',
    hint: 'Fechamento e relatórios financeiros',
    href: 'https://sharepoint.exemplo/sites/folha',
    groups: ['financeiro'],
    icon: 'finance',
  },
  {
    id: 'operacao',
    label: 'Operação',
    hint: 'Rotinas e quadros do time',
    href: 'https://sharepoint.exemplo/sites/operacao',
    groups: ['operacao'],
    icon: 'operations',
  },
  {
    id: 'projetos',
    label: 'Projetos',
    hint: 'Pastas dos projetos internos',
    href: 'https://sharepoint.exemplo/sites/projetos',
    groups: ['projetos'],
    icon: 'projects',
  },
];

export function findShortcut(id: string) {
  return shortcuts.find(shortcut => shortcut.id === id) ?? null;
}
