import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { fornecedoresApi, type Fornecedor } from '../api/fornecedores';
import { ApiError } from '../api/client';
import { formatCpfCnpj } from '../lib/format';

type FormState = {
  razao_social: string;
  nome_fantasia: string;
  documento: string;
  ativo: boolean;
};

const emptyForm: FormState = {
  razao_social: '',
  nome_fantasia: '',
  documento: '',
  ativo: true,
};

type FornecedoresProps = {
  createRequest?: number;
};

export function Fornecedores({ createRequest = 0 }: FornecedoresProps) {
  const formId = useId();
  const razaoRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Fornecedor[]>([]);
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
      setItems(await fornecedoresApi.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar fornecedores');
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
    window.requestAnimationFrame(() => razaoRef.current?.focus());
  }, [createRequest]);

  function startEdit(item: Fornecedor) {
    setEditingId(item.id);
    setForm({
      razao_social: item.razao_social,
      nome_fantasia: item.nome_fantasia,
      documento: formatCpfCnpj(item.documento),
      ativo: item.ativo,
    });
    setNotice('');
    setError('');
    razaoRef.current?.focus();
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
      razao_social: form.razao_social.trim(),
      nome_fantasia: form.nome_fantasia.trim(),
      documento: form.documento,
      ativo: form.ativo,
    };
    try {
      if (editingId) {
        await fornecedoresApi.update(editingId, payload);
        setNotice('Fornecedor atualizado.');
      } else {
        await fornecedoresApi.create(payload);
        setNotice('Fornecedor criado.');
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar o fornecedor');
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: Fornecedor) {
    if (!window.confirm(`Excluir o fornecedor "${item.razao_social}"?`)) return;
    setError('');
    setNotice('');
    try {
      await fornecedoresApi.remove(item.id);
      if (editingId === item.id) resetForm();
      setNotice('Fornecedor excluído.');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível excluir o fornecedor');
    }
  }

  return (
    <section className="cadastros-page">
      <header className="page-header">
        <span className="eyebrow">Cadastros</span>
        <h1>Fornecedores</h1>
        <p>Cadastre os emitentes das notas fiscais de entrada de equipamentos.</p>
      </header>

      <div className="cadastros-layout">
        <form className="card-panel cadastro-form" onSubmit={(event) => void onSubmit(event)}>
          <div className="form-heading">
            <h2>{editingId ? 'Editar fornecedor' : 'Novo fornecedor'}</h2>
            {editingId && (
              <button type="button" className="btn btn-ghost" onClick={resetForm}>
                Cancelar edição
              </button>
            )}
          </div>

          <div className="field">
            <label htmlFor={`${formId}-razao`}>Razão social</label>
            <input
              ref={razaoRef}
              id={`${formId}-razao`}
              value={form.razao_social}
              onChange={(event) => setForm((current) => ({ ...current, razao_social: event.target.value }))}
              required
              maxLength={180}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-fantasia`}>Nome fantasia</label>
            <input
              id={`${formId}-fantasia`}
              value={form.nome_fantasia}
              onChange={(event) => setForm((current) => ({ ...current, nome_fantasia: event.target.value }))}
              required
              maxLength={180}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-documento`}>CNPJ/CPF</label>
            <input
              id={`${formId}-documento`}
              value={form.documento}
              onChange={(event) =>
                setForm((current) => ({ ...current, documento: formatCpfCnpj(event.target.value) }))
              }
              required
              inputMode="numeric"
              placeholder="00.000.000/0000-00"
            />
          </div>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={form.ativo}
              onChange={(event) => setForm((current) => ({ ...current, ativo: event.target.checked }))}
            />
            Fornecedor ativo
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

          <button type="submit" className="btn btn-primary" disabled={saving || !form.razao_social.trim()}>
            {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Criar fornecedor'}
          </button>
        </form>

        <div className="card-panel cadastro-table-wrap">
          <div className="table-heading">
            <h2>Fornecedores cadastrados</h2>
            <span>{items.length} registro(s)</span>
          </div>

          {loading ? (
            <p className="muted">Carregando...</p>
          ) : items.length === 0 ? (
            <div className="empty-state">Nenhum fornecedor cadastrado.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Razão social</th>
                    <th>Nome fantasia</th>
                    <th>CNPJ/CPF</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.razao_social}</strong>
                      </td>
                      <td>{item.nome_fantasia}</td>
                      <td>{formatCpfCnpj(item.documento)}</td>
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
