import { useEffect, useRef, useState } from 'react';
import type { ListQuery, Page } from '../api/accounting';
import { errorMessage } from '../api/client';

export function useCatalogPage<T>(load: (query: ListQuery) => Promise<Page<T>>) {
  const [page, setPage] = useState<Page<T>>({ items: [], total: 0, offset: 0, limit: 50 });
  const [q, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [limit, setSize] = useState(50);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    load({ q, offset, limit }).then(value => { if (active) setPage(value); }).catch(error => { if (active) setError(errorMessage(error)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [load, q, offset, limit, revision]);
  return { page, q, offset, limit, loading, error, setError, alive,
    search: (value: string) => { setQuery(value); setOffset(0); setRevision(value => value + 1); },
    setOffset, setLimit: (value: number) => { setSize(value); setOffset(0); },
    reload: () => setRevision(value => value + 1) };
}
