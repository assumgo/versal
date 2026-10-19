import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { Company } from '../api/companies';
import { errorMessage } from '../api/client';
import { payrollImports, type PayrollImportCreated, type PayrollImportHistoryItem, type PayrollImportHistoryPage } from '../api/payrollImports';
import { payrollPreview, type PayrollPreviewResponse } from '../api/payrollPreview';
import { Alert } from '../components/Alert';
import { CatalogPagination } from '../components/CatalogPagination';
import { DataTable, type Column } from '../components/DataTable';
import { PayrollPreviewResult } from '../components/PayrollPreviewResult';

type Props = { company: Company | null; competence: string; canPreview: boolean; canRead?: boolean };
export function PayrollImportPreview({ company, competence, canPreview, canRead = canPreview }: Props) {
  if (!company) return <><h1>Importação de folha</h1><Alert>Selecione uma empresa.</Alert></>;
  if (!canRead) return <><h1>Importação de folha</h1><Alert>Sem permissão para consultar importações.</Alert></>;
  if (company.status !== 'Ativa') return <><h1>Importação de folha</h1><Alert>Empresa inativa.</Alert></>;
  return <PreviewContext key={`${company.id}:${company.status}:${competence}:${canPreview}:${canRead}`}
    company={company} competence={competence} canPreview={canPreview} />;
}

const historyColumns: Column<PayrollImportHistoryItem>[] = [
  { key: 'competence', title: 'Competência', render: row => row.competence ?? '—' },
  { key: 'filename', title: 'Arquivo', render: row => row.filename ?? '—' },
  { key: 'imported_at', title: 'Data', render: row => row.imported_at ? <time dateTime={row.imported_at}>{row.imported_at}</time> : '—' },
  { key: 'status', title: 'Estado', render: row => row.status ?? '—' },
  { key: 'employees', title: 'Colaboradores', render: row => row.employees ?? '—' },
  { key: 'rubrics', title: 'Rubricas', render: row => row.rubrics ?? '—' },
];

function PreviewContext({ company, competence, canPreview }: { company: Company; competence: string; canPreview: boolean }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PayrollPreviewResponse | null>(null);
  const [saved, setSaved] = useState<PayrollImportCreated | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState('');
  const [confirmError, setConfirmError] = useState('');
  const [history, setHistory] = useState<PayrollImportHistoryPage>({ items: [], offset: 0, limit: 50, total: 0 });
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState('');
  const [historyOffset, setHistoryOffset] = useState(0);
  const [historyLimit, setHistoryLimit] = useState(50);
  const [historyRevision, setHistoryRevision] = useState(0);
  const [historyRequest, setHistoryRequest] = useState(0);
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const confirmController = useRef<AbortController | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  useEffect(() => () => {
    generation.current++;
    controller.current?.abort();
    confirmController.current?.abort();
  }, []);

  useEffect(() => {
    const abort = new AbortController();
    let active = true;
    setHistoryLoading(true);
    setHistoryError('');
    payrollImports.list(company.id, { offset: historyOffset, limit: historyLimit }, { signal: abort.signal })
      .then(page => { if (active) setHistory(page); })
      .catch(reason => { if (active) setHistoryError(errorMessage(reason)); })
      .finally(() => { if (active) setHistoryLoading(false); });
    return () => { active = false; abort.abort(); };
  }, [company.id, historyOffset, historyLimit, historyRevision, historyRequest]);

  const valid = /^[0-9]{4}-(0[1-9]|1[0-2])$/.test(competence);
  const displayCompetence = valid ? `${competence.slice(5)}/${competence.slice(0, 4)}` : '';
  function choose(next: File | null) {
    generation.current++;
    controller.current?.abort();
    confirmController.current?.abort();
    setBusy(false); setConfirmBusy(false); setPreview(null); setSaved(null);
    setError(''); setConfirmError(''); setFile(null);
    if (!next) return;
    if (!/\.(pdf|xlsx?)$/i.test(next.name)) { setError('Envie PDF, XLS ou XLSX.'); return; }
    if (!next.size) { setError('O arquivo está vazio.'); return; }
    if (next.size > 10 * 1024 * 1024) { setError('O arquivo excede 10 MiB.'); return; }
    setFile(next);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || !valid || busy || confirmBusy) return;
    const started = ++generation.current;
    controller.current?.abort(); controller.current = new AbortController();
    setBusy(true); setError(''); setConfirmError(''); setSaved(null); setPreview(null);
    try {
      const result = await payrollPreview.generate(company.id, file, displayCompetence, { signal: controller.current.signal });
      if (started === generation.current) setPreview(result);
    } catch (reason) {
      if (started === generation.current) setError(errorMessage(reason));
    } finally {
      if (started === generation.current) setBusy(false);
    }
  }
  async function confirm() {
    if (!file || !preview || preview.status !== 'ready' || !canPreview || confirmBusy || busy) return;
    const started = ++generation.current;
    confirmController.current?.abort(); confirmController.current = new AbortController();
    setConfirmBusy(true); setConfirmError(''); setError('');
    try {
      const result = await payrollImports.confirm(company.id, file, displayCompetence, preview.sha256,
        { signal: confirmController.current.signal });
      if (started !== generation.current) return;
      setSaved(result); setPreview(null); setFile(null);
      if (fileInput.current) fileInput.current.value = '';
      setHistoryOffset(0); setHistoryRevision(value => value + 1);
    } catch (reason) {
      if (started === generation.current) setConfirmError(errorMessage(reason));
    } finally {
      if (started === generation.current) setConfirmBusy(false);
    }
  }

  return <div className="preview-page"><h1>Importação de folha</h1>
    <Alert>Confira a prévia antes de confirmar. A confirmação grava um snapshot da folha; o arquivo original é descartado após a leitura.</Alert>
    <p>Contexto: {company.razao ?? company.id} · {displayCompetence || 'Selecione uma competência válida no cabeçalho.'}</p>
    {canPreview ? <form className="panel preview-upload" onSubmit={submit}>
      <label htmlFor="preview-file">Extrato Mensal</label>
      <input ref={fileInput} id="preview-file" type="file" accept=".pdf,.xls,.xlsx" onChange={event => choose(event.target.files?.[0] ?? null)} />
      <p>PDF, XLS ou XLSX, até 10 MiB. O documento será descartado após a leitura.</p>
      <button disabled={!file || !valid || busy || confirmBusy} type="submit">{busy ? 'Gerando prévia…' : 'Gerar prévia'}</button>
    </form> : <Alert>Seu perfil pode consultar o histórico, mas não pode confirmar importações.</Alert>}
    {error && <Alert variant="error">{error}</Alert>}
    {confirmError && <Alert variant="error">{confirmError}</Alert>}
    {saved && <Alert variant="success">Importação #{saved.import_id} concluída · {saved.competence} · {saved.employees} colaboradores · {saved.rubrics} rubricas.</Alert>}
    {preview && <><PayrollPreviewResult preview={preview} />
      {canPreview && preview.status === 'ready' && <button type="button" disabled={confirmBusy || busy} onClick={() => void confirm()}>
        {confirmBusy ? 'Salvando importação…' : 'Confirmar importação'}
      </button>}
    </>}
    <section className="panel" aria-labelledby="payroll-history-heading">
      <div className="page-heading"><h2 id="payroll-history-heading">Histórico de importações</h2>
        <button className="secondary" type="button" disabled={historyLoading} onClick={() => setHistoryRequest(value => value + 1)}>Atualizar histórico</button>
      </div>
      {historyError && <><Alert variant="error">{historyError}</Alert>
        <button className="secondary" type="button" disabled={historyLoading} onClick={() => setHistoryRequest(value => value + 1)}>Tentar novamente</button>
      </>}
      {historyLoading ? <p role="status">Carregando histórico…</p> : historyError ? null : <>
        <DataTable caption="Histórico de importações" rows={history.items} rowKey={row => row.import_id} columns={historyColumns} />
        <CatalogPagination total={history.total} offset={historyOffset} limit={historyLimit} busy={historyLoading}
          onOffsetChange={setHistoryOffset} onLimitChange={value => { setHistoryOffset(0); setHistoryLimit(Math.min(100, value)); }} />
      </>}
    </section>
  </div>;
}
