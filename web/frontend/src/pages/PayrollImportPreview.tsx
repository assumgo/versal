import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { Company } from '../api/companies';
import { errorMessage } from '../api/client';
import { payrollPreview, type PayrollPreviewResponse } from '../api/payrollPreview';
import { Alert } from '../components/Alert';
import { PayrollPreviewResult } from '../components/PayrollPreviewResult';

type Props = { company: Company | null; competence: string; canPreview: boolean };
export function PayrollImportPreview({ company, competence, canPreview }: Props) {
  if (!company) return <><h1>Importação de folha</h1><Alert>Selecione uma empresa.</Alert></>;
  if (!canPreview) return <><h1>Importação de folha</h1><Alert>Sem permissão para enviar documentos.</Alert></>;
  if (company.status !== 'Ativa') return <><h1>Importação de folha</h1><Alert>Empresa inativa.</Alert></>;
  return <PreviewContext key={`${company.id}:${company.status}:${competence}:${canPreview}`} company={company} competence={competence} />;
}
function PreviewContext({ company, competence }: { company: Company; competence: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PayrollPreviewResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => { generation.current++; controller.current?.abort(); }, []);
  const valid = /^[0-9]{4}-(0[1-9]|1[0-2])$/.test(competence);
  const displayCompetence = valid ? `${competence.slice(5)}/${competence.slice(0, 4)}` : '';
  function choose(next: File | null) {
    generation.current++; controller.current?.abort();
    setBusy(false); setPreview(null); setError(''); setFile(null);
    if (!next) return;
    if (!/\.(pdf|xlsx?)$/i.test(next.name)) { setError('Envie PDF, XLS ou XLSX.'); return; }
    if (!next.size) { setError('O arquivo está vazio.'); return; }
    if (next.size > 10 * 1024 * 1024) { setError('O arquivo excede 10 MiB.'); return; }
    setFile(next);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || !valid || busy) return;
    const started = ++generation.current;
    controller.current?.abort(); controller.current = new AbortController();
    setBusy(true); setError(''); setPreview(null);
    try {
      const result = await payrollPreview.generate(company.id, file, displayCompetence, { signal: controller.current.signal });
      if (started === generation.current) setPreview(result);
    } catch (error) {
      if (started === generation.current) setError(errorMessage(error));
    } finally {
      if (started === generation.current) setBusy(false);
    }
  }
  return <div className="preview-page"><h1>Importação de folha</h1>
    <Alert>Envie um Extrato Mensal para conferir os dados. Esta prévia não grava a folha nem altera cadastros.</Alert>
    <p>Contexto: {company.razao ?? company.id} · {displayCompetence || 'Selecione uma competência válida no cabeçalho.'}</p>
    <form className="panel preview-upload" onSubmit={submit}>
      <label htmlFor="preview-file">Extrato Mensal</label>
      <input id="preview-file" type="file" accept=".pdf,.xls,.xlsx" onChange={event => choose(event.target.files?.[0] ?? null)} />
      <p>PDF, XLS ou XLSX, até 10 MiB. O documento será descartado após a leitura.</p>
      <button disabled={!file || !valid || busy} type="submit">{busy ? 'Gerando prévia…' : 'Gerar prévia'}</button>
    </form>
    {error && <Alert variant="error">{error}</Alert>}
    {preview && <PayrollPreviewResult preview={preview} />}
  </div>;
}
