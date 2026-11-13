import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { colaboradoresApi, type Colaborador } from '../api/colaboradores';
import { ApiError } from '../api/client';
import { formatCpf, formatPhone } from '../lib/format';

type FormState = {
  nome: string;
  email_pessoal: string;
  cpf: string;
  data_nascimento: string;
  celular: string;
  ativo: boolean;
};

const emptyForm: FormState = {
  nome: '',
  email_pessoal: '',
  cpf: '',
  data_nascimento: '',
  celular: '',
  ativo: true,
};

type ColaboradoresProps = {
  createRequest?: number;
};

export function Colaboradores({ createRequest = 0 }: ColaboradoresProps) {
  const formId = useId();
  const nomeRef = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Colaborador[]>([]);
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
      setItems(await colaboradoresApi.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar colaboradores');
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

  function startEdit(item: Colaborador) {
    setEditingId(item.id);
    setForm({
      nome: item.nome,
      email_pessoal: item.email_pessoal,
      cpf: formatCpf(item.cpf),
      data_nascimento: item.data_nascimento,
      celular: formatPhone(item.celular),
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
    const payload = {
      nome: form.nome.trim(),
      email_pessoal: form.email_pessoal.trim(),
      cpf: form.cpf,
      data_nascimento: form.data_nascimento,
      celular: form.celular,
      ativo: form.ativo,
    };
    try {
      if (editingId) {
        await colaboradoresApi.update(editingId, payload);
        setNotice('Colaborador atualizado.');
      } else {
        await colaboradoresApi.create(payload);
        setNotice('Colaborador criado.');
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar o colaborador');
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(item: Colaborador) {
    if (!window.confirm(`Excluir o colaborador "${item.nome}"?`)) return;
    setError('');
    setNotice('');
    try {
      await colaboradoresApi.remove(item.id);
      if (editingId === item.id) resetForm();
      setNotice('Colaborador excluído.');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível excluir o colaborador');
    }
  }

  return (
    <section className="cadastros-page">
      <header className="page-header">
        <span className="eyebrow">Cadastros</span>
        <h1>Colaboradores</h1>
        <p>Cadastre os destinatários das alocações e dos documentos TRE.</p>
      </header>

      <div className="cadastros-layout">
        <form className="card-panel cadastro-form" onSubmit={(event) => void onSubmit(event)}>
          <div className="form-heading">
            <h2>{editingId ? 'Editar colaborador' : 'Novo colaborador'}</h2>
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
              maxLength={120}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-email`}>E-mail pessoal</label>
            <input
              id={`${formId}-email`}
              type="email"
              value={form.email_pessoal}
              onChange={(event) => setForm((current) => ({ ...current, email_pessoal: event.target.value }))}
              required
              maxLength={180}
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-cpf`}>CPF</label>
            <input
              id={`${formId}-cpf`}
              value={form.cpf}
              onChange={(event) => setForm((current) => ({ ...current, cpf: formatCpf(event.target.value) }))}
              required
              inputMode="numeric"
              placeholder="000.000.000-00"
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-nascimento`}>Data de nascimento</label>
            <input
              id={`${formId}-nascimento`}
              type="date"
              value={form.data_nascimento}
              onChange={(event) => setForm((current) => ({ ...current, data_nascimento: event.target.value }))}
              required
            />
          </div>

          <div className="field">
            <label htmlFor={`${formId}-celular`}>Número celular</label>
            <input
              id={`${formId}-celular`}
              value={form.celular}
              onChange={(event) => setForm((current) => ({ ...current, celular: formatPhone(event.target.value) }))}
              required
              inputMode="tel"
              placeholder="(00) 00000-0000"
            />
          </div>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={form.ativo}
              onChange={(event) => setForm((current) => ({ ...current, ativo: event.target.checked }))}
            />
            Colaborador ativo
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
            {saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Criar colaborador'}
          </button>
        </form>

        <div className="card-panel cadastro-table-wrap">
          <div className="table-heading">
            <h2>Colaboradores cadastrados</h2>
            <span>{items.length} registro(s)</span>
          </div>

          {loading ? (
            <p className="muted">Carregando...</p>
          ) : items.length === 0 ? (
            <div className="empty-state">Nenhum colaborador cadastrado.</div>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>E-mail</th>
                    <th>CPF</th>
                    <th>Nascimento</th>
                    <th>Celular</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.nome}</strong>
                      </td>
                      <td>{item.email_pessoal}</td>
                      <td>{formatCpf(item.cpf)}</td>
                      <td>{item.data_nascimento.split('-').reverse().join('/')}</td>
                      <td>{formatPhone(item.celular)}</td>
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
