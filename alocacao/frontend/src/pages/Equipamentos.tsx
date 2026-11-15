import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { categoriasApi, type Categoria } from '../api/categorias';
import { ApiError } from '../api/client';
import {
  equipamentosApi,
  type Equipamento,
  type EquipamentoStatus,
} from '../api/equipamentos';
import { produtosApi, type Produto } from '../api/produtos';

type FormState = {
  produto_id: string;
  numero_serie: string;
  numero_patrimonio: string;
  mac_address: string;
};

const emptyForm: FormState = {
  produto_id: '',
  numero_serie: '',
  numero_patrimonio: '',
  mac_address: '',
};

type EquipamentosProps = {
  createRequest?: number;
};

function statusLabel(status: EquipamentoStatus) {
  return status === 'alocado' ? 'Alocado' : 'Disponível';
}

export function Equipamentos({ createRequest = 0 }: EquipamentosProps) {
  const formId = useId();
  const serieRef = useRef<HTMLInputElement>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [filterCategoria, setFilterCategoria] = useState('');
  const [filterStatus, setFilterStatus] = useState<EquipamentoStatus>('disponivel');
  const [items, setItems] = useState<Equipamento[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    void Promise.all([categoriasApi.list(true), produtosApi.list()])
      .then(([cats, prods]) => {
        setCategorias(cats);
        setProdutos(prods);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Falha ao carregar dados auxiliares'));
  }, []);

  useEffect(() => {
    if (createRequest <= 0) return;
    openCreate();
  }, [createRequest]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setFormOpen(true);
    setError('');
    setNotice('');
    window.requestAnimationFrame(() => serieRef.current?.focus());
  }

  function openEdit(item: Equipamento) {
    setEditingId(item.id);
    setForm({
      produto_id: String(item.produto_id),
      numero_serie: item.numero_serie,
      numero_patrimonio: item.numero_patrimonio,
      mac_address: item.mac_address ?? '',
    });
    setFormOpen(true);
    setError('');
    setNotice('');
    window.requestAnimationFrame(() => serieRef.current?.focus());
  }

  function closeForm() {
    setFormOpen(false);
    setEditingId(null);
    setForm(emptyForm);
    setError('');
  }

  async function onSearch(options?: { clearNotice?: boolean }) {
    setLoading(true);
    setError('');
    if (options?.clearNotice !== false) setNotice('');
    try {
      const data = await equipamentosApi.list({
        categoria_id: filterCategoria ? Number(filterCategoria) : null,
        status: filterStatus,
      });
      setItems(data);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao pesquisar equipamentos');
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!form.produto_id) {
      setError('Selecione um produto');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    const payload = {
      produto_id: Number(form.produto_id),
      numero_serie: form.numero_serie.trim(),
      numero_patrimonio: form.numero_patrimonio.trim(),
      mac_address: form.mac_address.trim() || null,
    };
    try {
      if (editingId) {
        await equipamentosApi.update(editingId, payload);
        setNotice('Equipamento atualizado.');
      } else {
        await equipamentosApi.create(payload);
        setNotice('Equipamento criado.');
      }
      closeForm();
      if (searched) await onSearch({ clearNotice: false });
      else {
        const prods = await produtosApi.list();
        setProdutos(prods);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar o equipamento');
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: Equipamento) {
    if (!window.confirm(`Excluir o equipamento patrimônio "${item.numero_patrimonio}" (ID ${item.id})?`)) return;
    setError('');
    setNotice('');
    try {
      await equipamentosApi.remove(item.id);
      setNotice('Equipamento excluído.');
      if (editingId === item.id) closeForm();
      if (searched) await onSearch({ clearNotice: false });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível excluir o equipamento');
    }
  }

  return (
    <section className="equipamentos-page">
      <header className="page-header">
        <span className="eyebrow">Inventário</span>
        <h1>Equipamentos</h1>
        <p>Pesquise por categoria e status. A grade inicia vazia até você clicar em Pesquisar.</p>
      </header>

      <div className="card-panel filters-panel">
        <div className="filters-grid">
          <div className="field">
            <label htmlFor={`${formId}-filtro-categoria`}>Categoria</label>
            <select
              id={`${formId}-filtro-categoria`}
              value={filterCategoria}
              onChange={(event) => setFilterCategoria(event.target.value)}
            >
              <option value="">Todas</option>
              {categorias.map((categoria) => (
                <option key={categoria.id} value={categoria.id}>
                  {categoria.nome}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor={`${formId}-filtro-status`}>Status</label>
            <select
              id={`${formId}-filtro-status`}
              value={filterStatus}
              onChange={(event) => setFilterStatus(event.target.value as EquipamentoStatus)}
            >
              <option value="disponivel">Disponível</option>
              <option value="alocado">Alocado</option>
            </select>
          </div>

          <div className="filters-actions">
            <button type="button" className="btn btn-primary" onClick={() => void onSearch()} disabled={loading}>
              {loading ? 'Pesquisando...' : 'Pesquisar'}
            </button>
          </div>
        </div>
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

      {formOpen && (
        <form className="card-panel cadastro-form equipamento-form" onSubmit={(event) => void onSubmit(event)}>
          <div className="form-heading">
            <h2>{editingId ? `Editar equipamento #${editingId}` : 'Novo equipamento'}</h2>
            <button type="button" className="btn btn-ghost" onClick={closeForm}>
              Fechar
            </button>
          </div>

          {editingId && (
            <div className="field">
              <label htmlFor={`${formId}-id`}>ID</label>
              <input id={`${formId}-id`} value={editingId} disabled readOnly />
            </div>
          )}

          <div className="form-grid-2">
            <div className="field">
              <label htmlFor={`${formId}-produto`}>Produto</label>
              <select
                id={`${formId}-produto`}
                value={form.produto_id}
                onChange={(event) => setForm((current) => ({ ...current, produto_id: event.target.value }))}
                required
              >
                <option value="">Selecione</option>
                {produtos.map((produto) => (
                  <option key={produto.id} value={produto.id}>
                    {produto.codigo} — {produto.descricao}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor={`${formId}-serie`}>Número de série</label>
              <input
                ref={serieRef}
                id={`${formId}-serie`}
                value={form.numero_serie}
                onChange={(event) => setForm((current) => ({ ...current, numero_serie: event.target.value }))}
                required
                maxLength={100}
              />
            </div>
            <div className="field">
              <label htmlFor={`${formId}-patrimonio`}>Número patrimônio</label>
              <input
                id={`${formId}-patrimonio`}
                value={form.numero_patrimonio}
                onChange={(event) =>
                  setForm((current) => ({ ...current, numero_patrimonio: event.target.value }))
                }
                required
                maxLength={100}
              />
            </div>
            <div className="field">
              <label htmlFor={`${formId}-mac`}>MAC Address</label>
              <input
                id={`${formId}-mac`}
                value={form.mac_address}
                onChange={(event) => setForm((current) => ({ ...current, mac_address: event.target.value }))}
                maxLength={32}
                placeholder="Opcional"
              />
            </div>
          </div>

          {produtos.length === 0 && (
            <div className="form-alert error" role="status">
              Cadastre um produto em Cadastros → Produtos antes de incluir equipamentos.
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={saving || produtos.length === 0}>
            {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Incluir equipamento'}
          </button>
        </form>
      )}

      <div className="card-panel cadastro-table-wrap">
        <div className="table-heading">
          <h2>Relação de equipamentos</h2>
          <span>{searched ? `${items.length} registro(s)` : 'Sem pesquisa'}</span>
        </div>

        {!searched ? (
          <div className="empty-state">Selecione os filtros e clique em Pesquisar para listar os equipamentos.</div>
        ) : loading ? (
          <p className="muted">Carregando...</p>
        ) : items.length === 0 ? (
          <div className="empty-state">Nenhum equipamento encontrado para os filtros informados.</div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Produto</th>
                  <th>Marca</th>
                  <th>Modelo</th>
                  <th>Série</th>
                  <th>Patrimônio</th>
                  <th>MAC</th>
                  <th>Categoria</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className={editingId === item.id ? 'row-selected' : undefined}>
                    <td>{item.id}</td>
                    <td>
                      <strong>{item.produto_codigo}</strong>
                      <div className="muted">{item.produto_descricao}</div>
                    </td>
                    <td>{item.marca}</td>
                    <td>{item.modelo}</td>
                    <td>{item.numero_serie}</td>
                    <td>{item.numero_patrimonio}</td>
                    <td>{item.mac_address || '—'}</td>
                    <td>{item.categoria_nome}</td>
                    <td>
                      <span className={`status-pill${item.status === 'disponivel' ? ' on' : ''}`}>
                        {statusLabel(item.status)}
                      </span>
                    </td>
                    <td className="actions">
                      <button type="button" className="btn btn-ghost" onClick={() => openEdit(item)}>
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
    </section>
  );
}
