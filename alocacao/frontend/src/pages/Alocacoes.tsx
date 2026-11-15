import { useEffect, useId, useState, type FormEvent } from 'react';
import { alocacoesApi, type Alocacao } from '../api/alocacoes';
import { ApiError } from '../api/client';
import { colaboradoresApi, type Colaborador } from '../api/colaboradores';
import { equipamentosApi, type Equipamento } from '../api/equipamentos';
import { tresApi } from '../api/tres';

type AlocacoesProps = {
  createRequest?: number;
};

export function Alocacoes({ createRequest = 0 }: AlocacoesProps) {
  const formId = useId();
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [disponiveis, setDisponiveis] = useState<Equipamento[]>([]);
  const [ativas, setAtivas] = useState<Alocacao[]>([]);
  const [colaboradorId, setColaboradorId] = useState('');
  const [selectedEquipamentos, setSelectedEquipamentos] = useState<number[]>([]);
  const [selectedAlocacoes, setSelectedAlocacoes] = useState<number[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load() {
    setError('');
    try {
      const [cols, equips, alocs] = await Promise.all([
        colaboradoresApi.list(),
        equipamentosApi.list({ status: 'disponivel' }),
        alocacoesApi.list(true),
      ]);
      setColaboradores(cols.filter((item) => item.ativo));
      setDisponiveis(equips);
      setAtivas(alocs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar alocações');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (createRequest <= 0) return;
    setFormOpen(true);
    setNotice('');
    setError('');
  }, [createRequest]);

  function toggleEquipamento(id: number) {
    setSelectedEquipamentos((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  function toggleAlocacao(id: number) {
    setSelectedAlocacoes((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!colaboradorId) {
      setError('Selecione um colaborador');
      return;
    }
    if (selectedEquipamentos.length === 0) {
      setError('Selecione ao menos um equipamento disponível');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const result = await alocacoesApi.create({
        colaborador_id: Number(colaboradorId),
        equipamento_ids: selectedEquipamentos,
      });
      setNotice(`Alocação criada. TRE de entrega ${result.tre_codigo} gerado.`);
      setFormOpen(false);
      setColaboradorId('');
      setSelectedEquipamentos([]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível criar a alocação');
    } finally {
      setSaving(false);
    }
  }

  async function onDevolver() {
    if (selectedAlocacoes.length === 0) {
      setError('Selecione alocações ativas para devolver');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const result = await alocacoesApi.devolver(selectedAlocacoes);
      setNotice(`Devolução registrada. TRE de devolução ${result.tre_codigo} gerado.`);
      setSelectedAlocacoes([]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível devolver');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="equipamentos-page">
      <header className="page-header">
        <span className="eyebrow">Operações</span>
        <h1>Alocações</h1>
        <p>Ao alocar ou devolver equipamentos, o sistema emite automaticamente o TRE correspondente.</p>
      </header>

      {error && (
        <div className="form-alert error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="form-alert success" role="status">
          {notice}{' '}
          <a href="/tres">Ver TREs</a>
        </div>
      )}

      {formOpen && (
        <form className="card-panel cadastro-form equipamento-form" onSubmit={(event) => void onSubmit(event)}>
          <div className="form-heading">
            <h2>Nova alocação</h2>
            <button type="button" className="btn btn-ghost" onClick={() => setFormOpen(false)}>
              Fechar
            </button>
          </div>

          <div className="field">
            <label htmlFor={`${formId}-colaborador`}>Colaborador</label>
            <select
              id={`${formId}-colaborador`}
              value={colaboradorId}
              onChange={(event) => setColaboradorId(event.target.value)}
              required
            >
              <option value="">Selecione</option>
              {colaboradores.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <span className="field-label">Equipamentos disponíveis</span>
            {disponiveis.length === 0 ? (
              <div className="empty-state">Nenhum equipamento disponível.</div>
            ) : (
              <div className="check-list">
                {disponiveis.map((item) => (
                  <label key={item.id} className="check-item">
                    <input
                      type="checkbox"
                      checked={selectedEquipamentos.includes(item.id)}
                      onChange={() => toggleEquipamento(item.id)}
                    />
                    <span>
                      <strong>{item.codigo}</strong> — {item.produto_codigo} {item.produto_descricao} (pat. {item.numero_patrimonio})
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <button type="submit" className="btn btn-primary" disabled={saving || disponiveis.length === 0}>
            {saving ? 'Salvando...' : 'Alocar e gerar TRE de entrega'}
          </button>
        </form>
      )}

      <div className="card-panel cadastro-table-wrap">
        <div className="table-heading">
          <h2>Alocações ativas</h2>
          <button type="button" className="btn btn-primary" onClick={() => void onDevolver()} disabled={saving}>
            Devolver selecionados
          </button>
        </div>

        {ativas.length === 0 ? (
          <div className="empty-state">Nenhuma alocação ativa.</div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Equipamento</th>
                  <th>Produto</th>
                  <th>Patrimônio</th>
                  <th>Colaborador</th>
                  <th>TRE entrega</th>
                </tr>
              </thead>
              <tbody>
                {ativas.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Selecionar alocação ${item.id}`}
                        checked={selectedAlocacoes.includes(item.id)}
                        onChange={() => toggleAlocacao(item.id)}
                      />
                    </td>
                    <td>
                      <strong>{item.equipamento_codigo}</strong>
                    </td>
                    <td>
                      {item.produto_codigo} — {item.produto_descricao}
                    </td>
                    <td>{item.numero_patrimonio}</td>
                    <td>{item.colaborador_nome}</td>
                    <td>
                      {item.tre_entrega_id ? (
                        <a href={tresApi.pdfUrl(item.tre_entrega_id)} target="_blank" rel="noreferrer">
                          PDF
                        </a>
                      ) : (
                        '—'
                      )}
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
