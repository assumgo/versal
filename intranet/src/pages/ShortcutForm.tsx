import { useEffect, useRef, useState, type FormEvent } from 'react';
import { audienceGroups, labelFor } from '../auth/directory';
import type { ShortcutIcon } from '../shortcuts/icons';
import type { ShortcutDraft } from '../shortcuts/store';

const iconOptions: { value: ShortcutIcon; label: string }[] = [
  { value: 'documents', label: 'Documentos' },
  { value: 'people', label: 'Pessoas' },
  { value: 'benefits', label: 'Benefícios' },
  { value: 'finance', label: 'Financeiro' },
  { value: 'operations', label: 'Operação' },
  { value: 'projects', label: 'Projetos' },
];

export function ShortcutForm({ onClose, onCreate }: { onClose: () => void; onCreate: (draft: ShortcutDraft) => string | null }) {
  const [error, setError] = useState('');
  const nameRef = useRef<HTMLInputElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    nameRef.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') closeRef.current();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const message = onCreate({
      label: String(data.get('label') ?? ''),
      hint: String(data.get('hint') ?? ''),
      href: String(data.get('href') ?? ''),
      groups: data.getAll('groups').map(String),
      icon: String(data.get('icon') ?? 'documents') as ShortcutIcon,
    });
    setError(message ?? '');
    if (!message) onClose();
  }

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <form className="modal modal-form" role="dialog" aria-modal="true" aria-labelledby="incluir-atalho" onSubmit={submit} onMouseDown={event => event.stopPropagation()}>
        <h2 id="incluir-atalho">Incluir atalho</h2>
        <p>O atalho aparece para todo mundo. O endereço só abre para os grupos marcados.</p>
        {error && <p className="form-error" role="alert">{error}</p>}
        <label className="form-field">Nome<input ref={nameRef} name="label" required /></label>
        <label className="form-field">Descrição<input name="hint" /></label>
        <label className="form-field">Endereço<input name="href" placeholder="https://" required /></label>
        <label className="form-field">Ícone
          <select name="icon" defaultValue="documents">
            {iconOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <fieldset>
          <legend>Quem pode abrir</legend>
          <div className="checks">
            {audienceGroups.map(group => (
              <label key={group}>
                <input type="checkbox" name="groups" value={group} defaultChecked={group === 'todos'} />
                {labelFor(group)}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="form-actions">
          <button type="submit" className="primary">Salvar atalho</button>
          <button type="button" className="ghost" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </div>
  );
}
