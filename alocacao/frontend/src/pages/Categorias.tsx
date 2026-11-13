import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { categoriasApi, type Categoria } from '../api/categorias';
import { ApiError } from '../api/client';

type FormState = {
  nome: string;
  descricao: string;
  ativo: boolean;
};

const emptyForm: FormState = { nome: '', descricao: '', ativo: true };

type CategoriasProps = {
  createRequest?: number;
};

export function Categorias({ createRequest = 0 }: CategoriasProps) {
  const formId = useId();
  const nomeRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Categoria[]>([]);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const data = await categoriasApi.list();
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar categorias');
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

  function startEdit(item: Categoria) {
    setEditingId(item.id);
    setForm({
      nome: item.nome,
      descricao: item.descricao ?? '',
      ativo: item.ativo,
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
    try {
      if (editingId) {
        await categoriasApi.update(editingId, {
          nome: form.nome.trim(),
          descricao: form.descricao.trim() || null,
          ativo: form.ativo,
        });
        setNotice('Categoria atualizada.');
      } else {
        await categoriasApi.create({
          nome: form.nome.trim(),
          descricao: form.descricao.trim() || null,
          ativo: form.ativo,
        });
        setNotice('Categoria criada.');
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar a categoria');
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: Categoria) {
    const confirmed = window.confirm(`Excluir a categoria "${item.nome}"?`);
    if (!confirmed) return;
    setError('');
    setNotice('');
    try {
      await categoriasApi.remove(item.id);
      if (editingId === item.id) resetForm();
      setNotice('Categoria excluída.');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível excluir a categoria');
    }
  }

  async function toggleAtivo(item: Categoria) {
    setError('');
    try {
      await categoriasApi.update(item.id, { ativo: !item.ativo });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível alterar o status');
    }
  }

  return (
    <section className="cadastros-page">
      <header className="page-header">
        <span className="eyebrow">Cadastros</span>
        <h1>Categorias</h1>
        <p>Gerencie as famílias de equipamentos usadas em entradas, alocações e TREs.</p>
      </header>

      <div className="cadastros-layout">
        <form className="card-panel cadastro-form" onSubmit={(event) => void onSubmit(event)} aria-labelledby={`${formId}-title`}>
          <div className="form-heading">
            <h2 id={`${formId}-title`}>{editingId ? 'Editar categoria' : 'Nova categoria'}</h2>
            {editingId && (
              <button type="button" className="btn btn-ghost" onClick={resetForm}>
                Cancelar edição
              </button>
            )}
          </div>

          <div className="field">
            <label htmlFor={`${formId}-nome`}>Nome</label>
            <input
              ref={nomeRef}
              id={`${formId}-nome`}
              value={form.nome}
              onChange={(event) => setForm((current) => ({ ...current, nome: event.target.value }))}
              required
              maxLength={80}
              placeholder="Ex.: Notebook"
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-descricao`}>Descrição</label>
            <textarea
              id={`${formId}-descricao`}
              value={form.descricao}
              onChange={(event) => setForm((current) => ({ ...current, descricao: event.target.value }))}
              maxLength={500}
              rows={3}
              placeholder="Opcional"
            />
          </div>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={form.ativo}
              onChange={(event) => setForm((current) => ({ ...current, ativo: event.target.checked }))}
            />
            Categoria ativa
          </label>

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
            {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Criar categoria'}
          </button>
        </form>

        <div className="card-panel cadastro-table-wrap">
          <div className="table-heading">
            <h2>Categorias cadastradas</h2>
            <span>{items.length} registro(s)</span>
          </div>

          {loading ? (
            <p className="muted">Carregando...</p>
          ) : items.length === 0 ? (
            <div className="empty-state">Nenhuma categoria cadastrada.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Descrição</th>
                    <th>Status</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.nome}</strong>
                      </td>
                      <td>{item.descricao || '—'}</td>
                      <td>
                        <button
                          type="button"
                          className={`status-pill${item.ativo ? ' on' : ''}`}
                          onClick={() => void toggleAtivo(item)}
                          title="Alternar status"
                        >
                          {item.ativo ? 'Ativa' : 'Inativa'}
                        </button>
                      </td>
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
