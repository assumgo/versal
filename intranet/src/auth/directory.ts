/** Usuário da sessão local. No SharePoint, `groups` vem do login (Entra ID). */
export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
  groups: readonly string[];
};

/**
 * Acessos de pré-visualização. Troque pelos grupos reais de cada pessoa
 * quando a página passar a usar o usuário autenticado do Microsoft 365.
 */
export const directory: readonly DirectoryUser[] = [
  {
    id: 'geral',
    name: 'Acesso geral',
    email: 'geral@versal.local',
    groups: ['todos'],
  },
  {
    id: 'financeiro',
    name: 'Time financeiro',
    email: 'financeiro@versal.local',
    groups: ['todos', 'financeiro'],
  },
  {
    id: 'rh',
    name: 'RH e operação',
    email: 'rh.operacao@versal.local',
    groups: ['todos', 'rh', 'operacao'],
  },
  {
    id: 'admin',
    name: 'Administrador',
    email: 'admin@versal.local',
    groups: ['todos', 'administrador'],
  },
];

export const groupLabels: Record<string, string> = {
  todos: 'Toda a empresa',
  rh: 'RH',
  financeiro: 'Financeiro',
  operacao: 'Operação',
  projetos: 'Projetos',
  administrador: 'Administrador',
};

export const audienceGroups = ['todos', 'rh', 'financeiro', 'operacao', 'projetos'] as const;

export function labelFor(group: string) {
  return groupLabels[group] ?? group;
}

export function groupsLabel(groups: readonly string[]) {
  return groups.map(labelFor).join(' · ');
}

export function isAdministrator(user: DirectoryUser | null) {
  return Boolean(user?.groups.includes('administrador'));
}

export function findUser(id: string | null) {
  return directory.find(user => user.id === id) ?? null;
}

export function initials(name: string) {
  const words = name.split(/\s+/).filter(word => word.length > 2 || word === word.toUpperCase());
  const picked = (words.length > 0 ? words : name.split(/\s+/)).slice(0, 2);
  return picked.map(word => word[0]?.toUpperCase() ?? '').join('');
}
