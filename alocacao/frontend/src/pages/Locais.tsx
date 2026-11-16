import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { ApiError } from '../api/client';
import { locaisApi, type Local } from '../api/locais';

type FormState = {
  codigo: string;
  nome: string;
  descricao: string;
};

const emptyForm: FormState = {
  codigo: '',
  nome: '',
  descricao: '',
};

type LocaisProps = {
  createRequest?: number;
};

export function Locais({ createRequest = 0 }: LocaisProps) {
  const formId = useId();
  const nomeRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Local[]>([]);
  const [search, setSearch] = useState('');
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load(q?: string) {
    setLoading(true);
    setError('');
    try {
      setItems(await locaisApi.list(q));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar locais');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (createRequest <= 0) return;
    setEditingId(null);
    setForm(emptyForm);
    setNotice('');
    setError('');
    window.requestAnimationFrame(() => nomeRef.current?.focus());
  }, [createRequest]);

  function startEdit(item: Local) {
    setEditingId(item.id);
    setForm({
      codigo: item.codigo,
      nome: item.nome,
      descricao: item.descricao,
    });
    setNotice('');
    setError('');
    nomeRef.current?.focus();
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
    setError('');
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    const payload = {
      nome: form.nome.trim(),
      descricao: form.descricao.trim(),
    };
    try {
      if (editingId) {
        await locaisApi.update(editingId, payload);
        setNotice('Local atualizado.');
      } else {
        await locaisApi.create(payload);
        setNotice('Local criado.');
      }
      resetForm();
      await load(search || undefined);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar o local');
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: Local) {
    if (!window.confirm(`Excluir o local "${item.nome}" (${item.codigo})?`)) return;
    setError('');
    setNotice('');
    try {
      await locaisApi.remove(item.id);
      if (editingId === item.id) resetForm();
      setNotice('Local excluído.');
      await load(search || undefined);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível excluir o local');
    }
  }

  return (
    <section className="cadastros-page">
      <header className="page-header">
        <span className="eyebrow">Cadastros</span>
        <h1>Locais</h1>
        <p>Cadastre os locais usados nas alocações de equipamentos sem emissão de TRE.</p>
      </header>

      <div className="cadastros-layout">
        <form className="card-panel cadastro-form" onSubmit={(event) => void onSubmit(event)}>
          <div className="form-heading">
            <h2>{editingId ? 'Editar local' : 'Novo local'}</h2>
            {editingId && (
              <button type="button" className="btn btn-ghost" onClick={resetForm}>
                Cancelar edição
              </button>
            )}
          </div>

          <div className="field">
            <label htmlFor={`${formId}-codigo`}>Código</label>
            <input
              id={`${formId}-codigo`}
              value={editingId ? form.codigo : 'Gerado automaticamente'}
              disabled
              readOnly
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-nome`}>Nome</label>
            <input
              ref={nomeRef}
              id={`${formId}-nome`}
              value={form.nome}
              onChange={(event) => setForm((current) => ({ ...current, nome: event.target.value }))}
              required
              maxLength={120}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-descricao`}>Descrição</label>
            <textarea
              id={`${formId}-descricao`}
              value={form.descricao}
              onChange={(event) => setForm((current) => ({ ...current, descricao: event.target.value }))}
              rows={4}
              maxLength={2000}
            />
          </div>

          {error && (
            <div className="form-alert error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="form-alert success" role="status">
              {notice}
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={saving || !form.nome.trim()}>
            {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Criar local'}
          </button>
        </form>

        <div className="card-panel cadastro-table-wrap">
          <div className="table-heading">
            <h2>Locais cadastrados</h2>
            <span>{items.length} registro(s)</span>
          </div>

          <div className="filters-panel" style={{ marginBottom: '0.85rem' }}>
            <div className="filters-grid locais-filters">
              <div className="field">
                <label htmlFor={`${formId}-busca`}>Pesquisar por nome ou código</label>
                <input
                  id={`${formId}-busca`}
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Nome ou código"
                />
              </div>
              <div className="filters-actions">
                <button type="button" className="btn btn-primary" onClick={() => void load(search)} disabled={loading}>
                  Pesquisar
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setSearch('');
                    void load();
                  }}
                  disabled={loading}
                >
                  Ver todos
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <p className="muted">Carregando...</p>
          ) : items.length === 0 ? (
            <div className="empty-state">Nenhum local encontrado.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nome</th>
                    <th>Descrição</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.codigo}</strong>
                      </td>
                      <td>{item.nome}</td>
                      <td>{item.descricao || '—'}</td>
                      <td className="actions">
                        <button type="button" className="btn btn-ghost" onClick={() => startEdit(item)}>
                          Editar
                        </button>
                        <button type="button" className="btn-danger-link" onClick={() => void onDelete(item)}>
                          Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
