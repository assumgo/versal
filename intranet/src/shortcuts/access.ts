import type { Shortcut } from './catalog';

/**
 * O atalho abre quando a pessoa logada tem pelo menos um grupo declarado nele.
 * `todos` entra nessa conta como os demais: só vale se também estiver no usuário.
 */
export function canAccess(groups: readonly string[], shortcut: Pick<Shortcut, 'groups'>) {
  if (shortcut.groups.length === 0 || groups.length === 0) return false;
  return shortcut.groups.some(group => groups.includes(group));
}

export function visibleShortcuts(groups: readonly string[], catalog: readonly Shortcut[]) {
  return catalog.filter(shortcut => canAccess(groups, shortcut));
}

/** Aceita só http(s). Um href malformado não vira link clicável. */
export function safeHref(href: string) {
  try {
    const url = new URL(href);
    if (url.protocol === 'https:' || url.protocol === 'http:') return url.toString();
  } catch {
    return null;
  }
  return null;
}
