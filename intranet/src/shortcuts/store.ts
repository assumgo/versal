import { audienceGroups } from '../auth/directory';
import { shortcuts, type Shortcut } from './catalog';
import type { ShortcutIcon } from './icons';
import { safeHref } from './access';

const storageKey = 'intranet.shortcuts';

export type ShortcutDraft = {
  label: string;
  hint: string;
  href: string;
  groups: readonly string[];
  icon: ShortcutIcon;
};

const icons: readonly ShortcutIcon[] = ['documents', 'people', 'benefits', 'finance', 'operations', 'projects'];

export function listShortcuts() {
  return [...shortcuts, ...readAdded()];
}

export function addShortcut(draft: ShortcutDraft): { ok: true; shortcut: Shortcut } | { ok: false; error: string } {
  const label = draft.label.trim();
  const hint = draft.hint.trim();
  const href = safeHref(draft.href.trim());
  const groups = draft.groups.filter(group => (audienceGroups as readonly string[]).includes(group));
  if (!label) return { ok: false, error: 'Informe o nome do atalho.' };
  if (!href) return { ok: false, error: 'Informe um endereço http ou https.' };
  if (groups.length === 0) return { ok: false, error: 'Escolha quem pode abrir o atalho.' };
  const current = listShortcuts();
  const shortcut: Shortcut = {
    id: uniqueId(label, current),
    label,
    hint,
    href,
    groups,
    icon: icons.includes(draft.icon) ? draft.icon : 'documents',
  };
  localStorage.setItem(storageKey, JSON.stringify([...readAdded(), shortcut]));
  return { ok: true, shortcut };
}

function readAdded() {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isShortcut);
  } catch {
    return [];
  }
}

function isShortcut(value: unknown): value is Shortcut {
  if (!value || typeof value !== 'object') return false;
  const item = value as Partial<Shortcut>;
  return typeof item.id === 'string'
    && typeof item.label === 'string'
    && typeof item.hint === 'string'
    && typeof item.href === 'string'
    && Array.isArray(item.groups)
    && icons.includes(item.icon as ShortcutIcon);
}

function uniqueId(label: string, existing: readonly Shortcut[]) {
  const base = label.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'atalho';
  const ids = new Set(existing.map(item => item.id));
  if (!ids.has(base)) return base;
  let index = 2;
  while (ids.has(`${base}-${index}`)) index += 1;
  return `${base}-${index}`;
}
