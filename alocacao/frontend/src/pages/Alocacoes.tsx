import { useEffect, useId, useState, type FormEvent } from 'react';
import {
  alocacoesApi,
  type Alocacao,
  type AlocacaoTipo,
  type DestinoTipo,
} from '../api/alocacoes';
import { ApiError } from '../api/client';
import { colaboradoresApi, type Colaborador } from '../api/colaboradores';
import { equipamentosApi, type Equipamento } from '../api/equipamentos';
import { locaisApi, type Local } from '../api/locais';
import { tresApi } from '../api/tres';

type AlocacoesProps = {
  createRequest?: number;
};

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  }).format(date);
}

export function Alocacoes({ createRequest = 0 }: AlocacoesProps) {
  const formId = useId();
  const [items, setItems] = useState<Alocacao[]>([]);
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [locais, setLocais] = useState<Local[]>([]);
  const [equipamentos, setEquipamentos] = useState<Equipamento[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [tipo, setTipo] = useState<AlocacaoTipo>('entrega');
  const [destinoTipo, setDestinoTipo] = useState<DestinoTipo>('colaborador');
  const [equipamentoId, setEquipamentoId] = useState('');
  const [quantidade, setQuantidade] = useState('1');
  const [colaboradorId, setColaboradorId] = useState('');
  const [localId, setLocalId] = useState('');
  const [dataPrevisao, setDataPrevisao] = useState('');
  const [search, setSearch] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function loadAux() {
    const [cols, locs] = await Promise.all([colaboradoresApi.list(), locaisApi.list()]);
    setColaboradores(cols.filter((item) => item.ativo));
    setLocais(locs);
  }

  async function loadEquipamentos(nextTipo: AlocacaoTipo, nextDestino: DestinoTipo = destinoTipo) {
    // Manutenção lista disponíveis e alocados; demais destinos seguem o tipo
    if (nextDestino === 'manutencao') {
      setEquipamentos(await equipamentosApi.list({}));
      return;
    }
    const status = nextTipo === 'entrega' ? 'disponivel' : 'alocado';
    setEquipamentos(await equipamentosApi.list({ status }));
  }

  async function loadAlocacoes(q?: string) {
    setLoading(true);
    setError('');
    try {
      setItems(await alocacoesApi.list({ q: q || undefined }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar alocações');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void Promise.all([loadAux(), loadAlocacoes(), loadEquipamentos('entrega', 'colaborador')]).catch((err) =>
      setError(err instanceof Error ? err.message : 'Falha ao carregar dados'),
    );
  }, []);

  useEffect(() => {
    if (createRequest <= 0) return;
    openCreate();
  }, [createRequest]);

  function openCreate() {
    setFormOpen(true);
    setTipo('entrega');
    setDestinoTipo('colaborador');
    setEquipamentoId('');
    setQuantidade('1');
    setColaboradorId('');
    setLocalId('');
    setDataPrevisao(new Date().toISOString().slice(0, 10));
    setNotice('');
    setError('');
    void loadEquipamentos('entrega', 'colaborador');
  }

  function closeForm() {
    setFormOpen(false);
    setError('');
  }

  async function onChangeTipo(next: AlocacaoTipo) {
    setTipo(next);
    setEquipamentoId('');
    await loadEquipamentos(next, destinoTipo);
  }

  async function onChangeDestino(next: DestinoTipo) {
    setDestinoTipo(next);
    setColaboradorId('');
    setLocalId('');
    setEquipamentoId('');
    await loadEquipamentos(tipo, next);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!equipamentoId) {
      setError('Selecione um equipamento');
      return;
    }
    if (destinoTipo === 'colaborador' && !colaboradorId) {
      setError('Selecione um colaborador');
      return;
    }
    if (destinoTipo === 'local' && !localId) {
      setError('Selecione um local');
      return;
    }
    if (destinoTipo === 'colaborador' && tipo === 'entrega' && !dataPrevisao) {
      setError('Informe a data de previsão de entrega');
      return;
    }
    const qty = Number(quantidade);
    if (!Number.isFinite(qty) || qty < 1) {
      setError('Quantidade inválida');
      return;
    }

    setSaving(true);
    setError('');
    setNotice('');
    try {
      const created = await alocacoesApi.create({
        tipo,
        destino_tipo: destinoTipo,
        equipamento_id: Number(equipamentoId),
        quantidade: qty,
        colaborador_id: destinoTipo === 'colaborador' ? Number(colaboradorId) : null,
        local_id: destinoTipo === 'local' ? Number(localId) : null,
        data_previsao: destinoTipo === 'colaborador' ? dataPrevisao || null : null,
      });
      const treMsg = created.tre_codigo
        ? ` TRE ${created.tipo === 'entrega' ? 'de entrega' : 'de devolução'} ${created.tre_codigo} gerado.`
        : ' Movimento registrado sem TRE.';
      setNotice(`Alocação ${created.codigo} criada.${treMsg}`);
      closeForm();
      await Promise.all([loadAlocacoes(search || undefined), loadEquipamentos(tipo, destinoTipo)]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível salvar a alocação');
    } finally {
      setSaving(false);
    }
  }

  const selectedEquipamento = equipamentos.find((item) => String(item.id) === equipamentoId);

  return (
    <section className="equipamentos-page">
      <header className="page-header">
        <span className="eyebrow">Operações</span>
        <h1>Alocações</h1>
        <p>
          Movimente o estoque de equipamentos para colaborador (com TRE), local ou manutenção. Só é possível
          movimentar produtos vinculados a equipamentos.
        </p>
      </header>

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
            <h2>Nova alocação</h2>
            <button type="button" className="btn btn-ghost" onClick={closeForm}>
              Fechar
            </button>
          </div>

          <div className="form-grid-2">
            <div className="field">
              <label htmlFor={`${formId}-tipo`}>Tipo</label>
              <select
                id={`${formId}-tipo`}
                value={tipo}
                onChange={(event) => void onChangeTipo(event.target.value as AlocacaoTipo)}
                required
              >
                <option value="entrega">Entrega</option>
                <option value="devolucao">Devolução</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor={`${formId}-destino-tipo`}>Destino</label>
              <select
                id={`${formId}-destino-tipo`}
                value={destinoTipo}
                onChange={(event) => void onChangeDestino(event.target.value as DestinoTipo)}
                required
              >
                <option value="colaborador">Colaborador</option>
                <option value="local">Local</option>
                <option value="manutencao">Manutenção</option>
              </select>
            </div>
          </div>

          <div className="field">
            <label htmlFor={`${formId}-codigo`}>Código</label>
            <input id={`${formId}-codigo`} value="Gerado automaticamente" disabled readOnly />
          </div>

          <div className="form-grid-2">
            <div className="field">
              <label htmlFor={`${formId}-equipamento`}>Equipamento</label>
              <select
                id={`${formId}-equipamento`}
                value={equipamentoId}
                onChange={(event) => setEquipamentoId(event.target.value)}
                required
              >
                <option value="">Selecione</option>
                {equipamentos.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.codigo} — {item.produto_codigo} {item.produto_descricao} (pat.{' '}
                    {item.numero_patrimonio})
                    {destinoTipo === 'manutencao'
                      ? ` · ${item.status === 'disponivel' ? 'Disponível' : 'Alocado'}`
                      : ''}
                  </option>
                ))}
              </select>
              {equipamentos.length === 0 && (
                <p className="muted">
                  {destinoTipo === 'manutencao'
                    ? 'Nenhum equipamento cadastrado para enviar à manutenção.'
                    : `Nenhum equipamento ${tipo === 'entrega' ? 'disponível' : 'alocado'} para movimentar.`}
                </p>
              )}
            </div>
            <div className="field">
              <label htmlFor={`${formId}-quantidade`}>Quantidade</label>
              <input
                id={`${formId}-quantidade`}
                type="number"
                min={1}
                step={1}
                value={quantidade}
                onChange={(event) => setQuantidade(event.target.value)}
                required
              />
            </div>
          </div>

          {destinoTipo === 'colaborador' && (
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
          )}
          {destinoTipo === 'local' && (
            <div className="field">
              <label htmlFor={`${formId}-local`}>Local</label>
              <select
                id={`${formId}-local`}
                value={localId}
                onChange={(event) => setLocalId(event.target.value)}
                required
              >
                <option value="">Selecione</option>
                {locais.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.codigo} — {item.nome}
                  </option>
                ))}
              </select>
            </div>
          )}

          {destinoTipo === 'colaborador' && (
            <div className="field">
              <label htmlFor={`${formId}-previsao`}>Data de previsão de entrega</label>
              <input
                id={`${formId}-previsao`}
                type="date"
                value={dataPrevisao}
                onChange={(event) => setDataPrevisao(event.target.value)}
                required={tipo === 'entrega'}
              />
            </div>
          )}

          <div className="field">
            <label htmlFor={`${formId}-criacao`}>Data de criação</label>
            <input id={`${formId}-criacao`} value="Preenchida automaticamente ao salvar" disabled readOnly />
          </div>

          {selectedEquipamento && (
            <div className="form-alert success" role="status">
              Produto {selectedEquipamento.produto_codigo}: estoque será atualizado conforme o movimento.
            </div>
          )}

          {destinoTipo === 'colaborador' && (
            <p className="muted">
              Destino colaborador gera automaticamente o TRE de {tipo === 'entrega' ? 'entrega' : 'devolução'}.
            </p>
          )}
          {destinoTipo === 'local' && (
            <p className="muted">Destino local apenas registra o movimento e atualiza o estoque disponível.</p>
          )}
          {destinoTipo === 'manutencao' && (
            <p className="muted">
              Manutenção lista todos os equipamentos (disponíveis e alocados). Se já estiver alocado, a entrega
              anterior é encerrada e o item passa para manutenção.
            </p>
          )}

          <button type="submit" className="btn btn-primary" disabled={saving || equipamentos.length === 0}>
            {saving ? 'Salvando...' : 'Registrar alocação'}
          </button>
        </form>
      )}

      <div className="card-panel filters-panel">
        <div className="filters-grid locais-filters">
          <div className="field">
            <label htmlFor={`${formId}-busca`}>Pesquisar</label>
            <input
              id={`${formId}-busca`}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Código, colaborador, local ou equipamento"
            />
          </div>
          <div className="filters-actions">
            <button type="button" className="btn btn-primary" onClick={() => void loadAlocacoes(search)} disabled={loading}>
              Pesquisar
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setSearch('');
                void loadAlocacoes();
              }}
              disabled={loading}
            >
              Ver todos
            </button>
          </div>
        </div>
      </div>

      <div className="card-panel cadastro-table-wrap">
        <div className="table-heading">
          <h2>Movimentos de alocação</h2>
          <span>{loading ? '...' : `${items.length} registro(s)`}</span>
        </div>

        {loading ? (
          <p className="muted">Carregando...</p>
        ) : items.length === 0 ? (
          <div className="empty-state">Nenhuma alocação encontrada.</div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Tipo</th>
                  <th>Destino</th>
                  <th>Equipamento</th>
                  <th>Qtde</th>
                  <th>Data criação</th>
                  <th>TRE</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.codigo}</strong>
                    </td>
                    <td>
                      <span className={`status-pill${item.tipo === 'entrega' ? ' on' : ''}`}>
                        {item.tipo === 'entrega' ? 'Entrega' : 'Devolução'}
                      </span>
                    </td>
                    <td>
                      <div>{item.destino_tipo === 'colaborador' ? 'Colaborador' : 'Local'}</div>
                      <div className="muted">{item.destino_nome}</div>
                    </td>
                    <td>
                      <strong>{item.equipamento_codigo}</strong>
                      <div className="muted">
                        {item.produto_codigo} — {item.produto_descricao}
                      </div>
                    </td>
                    <td>{item.quantidade}</td>
                    <td>{formatDateTime(item.created_at)}</td>
                    <td>
                      {item.tre_id ? (
                        <a href={tresApi.pdfUrl(item.tre_id)} target="_blank" rel="noreferrer">
                          {item.tre_codigo || 'PDF'}
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
