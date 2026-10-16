import { useEffect, useRef, useState } from 'react';
import { chartAccounts, type ChartAccount } from '../api/chartAccounts';
import { normalizeAccount, type Page } from '../api/accounting';
import { errorMessage } from '../api/client';
import { CatalogPagination } from './CatalogPagination';
import { Alert } from './Alert';

type Props = { companyId: number; label: string; value: string; onChange: (value: string) => void; onResolved: (account: ChartAccount | null) => void; disabled: boolean };
export function AccountPicker({ companyId, label, value, onChange, onResolved, disabled }: Props) {
  const [choices, setChoices] = useState<Page<ChartAccount> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const callback = useRef(onResolved);
  callback.current = onResolved;
  const generation = useRef(0);
  const searchVersion = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    ++searchVersion.current;
    setChoices(null); setBusy(false); setError(''); callback.current(null);
    const code = normalizeAccount(value);
    if (!code) return;
    const timer = window.setTimeout(() => {
      chartAccounts.list(companyId, { q: '', offset: 0, limit: 1, conta: code }).then(result => {
        if (generation.current === current) callback.current(result.items[0] ?? null);
      }).catch(error => { if (generation.current === current) setError(errorMessage(error)); });
    }, 200);
    return () => { window.clearTimeout(timer); ++generation.current; ++searchVersion.current; };
  }, [companyId, value]);
  async function search(offset = 0, limit = 25) {
    const current = ++searchVersion.current;
    setBusy(true); setError('');
    try {
      const result = await chartAccounts.list(companyId, { q: value, offset, limit });
      if (searchVersion.current === current) setChoices(result);
    } catch (error) { if (searchVersion.current === current) setError(errorMessage(error)); }
    finally { if (searchVersion.current === current) setBusy(false); }
  }
  return <div className="account-picker"><label>{label}<input value={value} disabled={disabled} onChange={event => onChange(event.target.value)} placeholder="Código ou descrição para pesquisar" /></label><button type="button" className="secondary" disabled={disabled || busy} onClick={() => void search()} aria-label={`Buscar ${label.toLowerCase()}`}>Buscar no plano</button>
    {value.trim() && !normalizeAccount(value) && <p className="catalog-hint">Pesquise a descrição e selecione uma conta, ou informe um código com dígitos.</p>}
    {error && <Alert variant="error">{error}</Alert>}
    {choices && <section className="account-choices" aria-label={`Resultados de ${label.toLowerCase()}`}><ul>{choices.items.map(row => <li key={row.id}><button type="button" disabled={disabled} className="secondary" aria-label={`Selecionar conta ${row.id}`} onClick={() => { onChange(row.conta ?? ''); callback.current(row); setChoices(null); }}>{row.conta ?? 'Sem código'} — {row.descricao ?? 'Sem descrição'} (ID {row.id})</button></li>)}</ul>{choices.items.length === 0 && <p>Nenhuma conta encontrada. Você pode informar um código manualmente.</p>}<CatalogPagination total={choices.total} offset={choices.offset} limit={choices.limit} busy={busy || disabled} onOffsetChange={offset => void search(offset, choices.limit)} onLimitChange={limit => void search(0, limit)} /></section>}
  </div>;
}
