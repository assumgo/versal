export type ShortcutIcon = 'documents' | 'people' | 'benefits' | 'finance' | 'operations' | 'projects';

const paths: Record<ShortcutIcon, string> = {
  documents: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zm0 0v5h5M8 13h8M8 17h5',
  people: 'M16 19v-1a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v1M10 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6m10 7v-1a3 3 0 0 0-2.2-2.9M16 6.1a3 3 0 0 1 0 5.8',
  benefits: 'M12 21s-7-4.4-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 5.6-7 10-7 10',
  finance: 'M4 19V5M4 19h16M8 16v-4M12 16V8M16 16v-6',
  operations: 'M4 4h7v7H4zm9 0h7v7h-7zM4 13h7v7H4zm9 0h7v7h-7z',
  projects: 'M4 8h16v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zm4-3h8v3H8z',
};

export function ShortcutGlyph({ name }: { name: ShortcutIcon }) {
  return (
    <svg className="glyph" viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  );
}
