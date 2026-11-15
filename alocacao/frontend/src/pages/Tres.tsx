import { useId, useState } from 'react';
import { ApiError } from '../api/client';
import { tresApi, type Tre, type TreTipo } from '../api/tres';

function tipoLabel(tipo: TreTipo) {
  return tipo === 'entrega' ? 'Entrega' : 'Devolução';
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  }).format(date);
}

export function Tres() {
  const formId = useId();
  const [nome, setNome] = useState('');
  const [codigo, setCodigo] = useState('');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [items, setItems] = useState<Tre[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function onSearch() {
    setLoading(true);
    setError('');
    try {
      setItems(
        await tresApi.list({
          nome,
          codigo,
          data_inicio: dataInicio || undefined,
          data_fim: dataFim || undefined,
        }),
      );
      setSearched(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Falha ao pesquisar TREs');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="equipamentos-page">
      <header className="page-header">
        <span className="eyebrow">Documentos</span>
        <h1>TREs</h1>
        <p>Termos de Responsabilidade gerados na alocação e na devolução de equipamentos.</p>
      </header>

      <div className="card-panel filters-panel">
        <div className="filters-grid tre-filters">
          <div className="field">
            <label htmlFor={`${formId}-nome`}>Nome do colaborador</label>
            <input
              id={`${formId}-nome`}
              value={nome}
              onChange={(event) => setNome(event.target.value)}
              placeholder="Buscar por nome"
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-codigo`}>Código</label>
            <input
              id={`${formId}-codigo`}
              value={codigo}
              onChange={(event) => setCodigo(event.target.value)}
              placeholder="Ex.: 000001"
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-inicio`}>Data emissão (de)</label>
            <input
              id={`${formId}-inicio`}
              type="date"
              value={dataInicio}
              onChange={(event) => setDataInicio(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor={`${formId}-fim`}>Data emissão (até)</label>
            <input
              id={`${formId}-fim`}
              type="date"
              value={dataFim}
              onChange={(event) => setDataFim(event.target.value)}
            />
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

      <div className="card-panel cadastro-table-wrap">
        <div className="table-heading">
          <h2>TREs emitidos</h2>
          <span>{searched ? `${items.length} registro(s)` : 'Sem pesquisa'}</span>
        </div>

        {!searched ? (
          <div className="empty-state">Informe os filtros e clique em Pesquisar para listar os TREs.</div>
        ) : loading ? (
          <p className="muted">Carregando...</p>
        ) : items.length === 0 ? (
          <div className="empty-state">Nenhum TRE encontrado para os filtros informados.</div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Colaborador</th>
                  <th>Data criação</th>
                  <th>Tipo</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.codigo}</strong>
                    </td>
                    <td>{item.colaborador_nome}</td>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td>
                      <span className={`status-pill${item.tipo === 'entrega' ? ' on' : ''}`}>
                        {tipoLabel(item.tipo)}
                      </span>
                    </td>
                    <td className="actions">
                      <a className="btn btn-ghost" href={tresApi.pdfUrl(item.id)} target="_blank" rel="noreferrer">
                        Baixar PDF
                      </a>
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
