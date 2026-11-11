import type { ShortcutIcon } from './icons';

/**
 * Atalhos da página inicial. Substitua esta lista pelos sites internos.
 *
 * `groups` define quem pode ver e abrir o atalho.
 * A pessoa precisa ter pelo menos um desses grupos na sessão.
 * `todos` é o grupo de toda a empresa. Lista vazia não abre para ninguém.
 *
 * A grade esconde o atalho, e o endereço direto também é recusado,
 * quando o usuário logado não tem grupo compatível.
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
