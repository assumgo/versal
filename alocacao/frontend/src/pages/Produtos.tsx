import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { categoriasApi, type Categoria } from '../api/categorias';
import { ApiError } from '../api/client';
import { produtosApi, type Produto } from '../api/produtos';

type FormState = {
  codigo: string;
  descricao: string;
  marca: string;
  modelo: string;
  categoria_id: string;
};

const emptyForm: FormState = {
  codigo: '',
  descricao: '',
  marca: '',
  modelo: '',
  categoria_id: '',
};

type ProdutosProps = {
  createRequest?: number;
};

export function Produtos({ createRequest = 0 }: ProdutosProps) {
  const formId = useId();
  const descricaoRef = useRef<HTMLInputElement>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [items, setItems] = useState<Produto[]>([]);
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
      setItems(await produtosApi.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar produtos');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void categoriasApi
      .list(true)
      .then((data) => setCategorias(data))
      .catch((err) => setError(err instanceof Error ? err.message : 'Falha ao carregar categorias'));
    void load();
  }, []);

  useEffect(() => {
    if (createRequest <= 0) return;
    setEditingId(null);
    setForm(emptyForm);
    setNotice('');
    setError('');
    window.requestAnimationFrame(() => descricaoRef.current?.focus());
  }, [createRequest]);

  function startEdit(item: Produto) {
    setEditingId(item.id);
    setForm({
      codigo: item.codigo,
      descricao: item.descricao,
      marca: item.marca,
      modelo: item.modelo,
      categoria_id: String(item.categoria_id),
    });
    setNotice('');
    setError('');
    descricaoRef.current?.focus();
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
    setError('');
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!form.categoria_id) {
      setError('Selecione uma categoria');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    const payload = {
      descricao: form.descricao.trim(),
      marca: form.marca.trim(),
      modelo: form.modelo.trim(),
      categoria_id: Number(form.categoria_id),
    };
    try {
      if (editingId) {
        await produtosApi.update(editingId, payload);
        setNotice('Produto atualizado.');
      } else {
        await produtosApi.create(payload);
        setNotice('Produto criado.');
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar o produto');
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: Produto) {
    if (!window.confirm(`Excluir o produto "${item.codigo}"?`)) return;
    setError('');
    setNotice('');
    try {
      await produtosApi.remove(item.id);
      if (editingId === item.id) resetForm();
      setNotice('Produto excluído.');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível excluir o produto');
    }
  }

  return (
    <section className="cadastros-page">
      <header className="page-header">
        <span className="eyebrow">Cadastros</span>
        <h1>Produtos</h1>
        <p>Cadastre o catálogo de produtos vinculados às categorias de equipamentos.</p>
      </header>

      <div className="cadastros-layout">
        <form className="card-panel cadastro-form" onSubmit={(event) => void onSubmit(event)}>
          <div className="form-heading">
            <h2>{editingId ? 'Editar produto' : 'Novo produto'}</h2>
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
            <label htmlFor={`${formId}-descricao`}>Descrição</label>
            <input
              ref={descricaoRef}
              id={`${formId}-descricao`}
              value={form.descricao}
              onChange={(event) => setForm((current) => ({ ...current, descricao: event.target.value }))}
              required
              maxLength={200}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-marca`}>Marca</label>
            <input
              id={`${formId}-marca`}
              value={form.marca}
              onChange={(event) => setForm((current) => ({ ...current, marca: event.target.value }))}
              required
              maxLength={100}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-modelo`}>Modelo</label>
            <input
              id={`${formId}-modelo`}
              value={form.modelo}
              onChange={(event) => setForm((current) => ({ ...current, modelo: event.target.value }))}
              required
              maxLength={100}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-categoria`}>Categoria</label>
            <select
              id={`${formId}-categoria`}
              value={form.categoria_id}
              onChange={(event) => setForm((current) => ({ ...current, categoria_id: event.target.value }))}
              required
            >
              <option value="">Selecione</option>
              {categorias.map((categoria) => (
                <option key={categoria.id} value={categoria.id}>
                  {categoria.nome}
                </option>
              ))}
            </select>
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

          <button type="submit" className="btn btn-primary" disabled={saving || !form.descricao.trim()}>
            {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Criar produto'}
          </button>
        </form>

        <div className="card-panel cadastro-table-wrap">
          <div className="table-heading">
            <h2>Produtos cadastrados</h2>
            <span>{items.length} registro(s)</span>
          </div>

          {loading ? (
            <p className="muted">Carregando...</p>
          ) : items.length === 0 ? (
            <div className="empty-state">Nenhum produto cadastrado.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Descrição</th>
                    <th>Marca</th>
                    <th>Modelo</th>
                    <th>Categoria</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.codigo}</strong>
                      </td>
                      <td>{item.descricao}</td>
                      <td>{item.marca}</td>
                      <td>{item.modelo}</td>
                      <td>{item.categoria_nome}</td>
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
