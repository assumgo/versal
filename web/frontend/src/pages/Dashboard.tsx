import { useEffect, useState, type CSSProperties, type FormEvent } from 'react';
import { appointments, type Appointment } from '../api/appointments';
import type { Company } from '../api/companies';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';
import { LoadingState } from '../components/LoadingState';
import { errorMessage } from '../api/client';

const weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function parseMonth(value: string | undefined) {
  return value && /^\d{4}-(0[1-9]|1[0-2])$/.test(value) ? value : currentMonth();
}

function monthGrid(month: string) {
  const [year, number] = month.split('-').map(Number);
  const count = new Date(year, number, 0).getDate();
  const lead = (new Date(year, number - 1, 1).getDay() + 6) % 7;
  const weeks = Math.ceil((lead + count) / 7);
  const cells = Array.from({ length: weeks * 7 }, (_, index) => {
    const date = new Date(year, number - 1, 1 - lead + index);
    const iso = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    return { iso, day: date.getDate(), inMonth: date.getMonth() === number - 1, weekend: index % 7 >= 5 };
  });
  return { year, number, weeks, cells };
}

function todayIso() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

function formatDay(iso: string) {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' });
}

function dayName(iso: string, count: number) {
  const formatted = formatDay(iso);
  if (count === 0) return `${formatted}, sem agendamentos`;
  return `${formatted}, ${count === 1 ? '1 agendamento' : `${count} agendamentos`}`;
}

export function Dashboard({ company = null, competence, canWrite = false }: { company?: Company | null; competence?: string; canWrite?: boolean }) {
  const month = parseMonth(competence);
  const grid = monthGrid(month);
  const today = todayIso();
  const rawMonth = new Date(grid.year, grid.number - 1, 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
  const monthLabel = rawMonth.charAt(0).toUpperCase() + rawMonth.slice(1);
  const [rows, setRows] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(Boolean(company));
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const writable = canWrite && company?.status !== 'Inativa';
  useEffect(() => {
    if (!company) return;
    let active = true;
    setLoading(true); setError(''); setRows([]);
    appointments.list(company.id, month).then(data => { if (active) setRows(Array.isArray(data) ? data : []); }).catch(reason => { if (active) setError(errorMessage(reason)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [company, month, revision]);
  useEffect(() => { setSelected(current => current?.startsWith(month) ? current : null); }, [month, company?.id]);
  const byDay = new Map<string, Appointment[]>();
  for (const row of rows) {
    const list = byDay.get(row.scheduled_date) ?? [];
    list.push(row);
    byDay.set(row.scheduled_date, list);
  }
  const selectedRows = selected ? byDay.get(selected) ?? [] : [];
  async function schedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!company || !selected || busy) return;
    const data = new FormData(event.currentTarget);
    const details = String(data.get('details') ?? '').trim();
    setBusy(true); setError(''); setNotice('');
    try {
      await appointments.create(company.id, { scheduled_date: selected, starts_at: String(data.get('starts_at')), title: String(data.get('title')), details: details || null });
      setNotice('Agendamento salvo.');
      setRevision(value => value + 1);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <div className="agenda">
    <div className="page-heading agenda-heading"><div><p className="eyebrow">AGENDA</p><h1>Dashboard</h1></div><p className="agenda-month">{monthLabel}</p></div>
    {!company && <Alert>Selecione uma empresa.</Alert>}
    {company?.status === 'Inativa' && <Alert>Empresa inativa: a agenda está disponível somente para consulta.</Alert>}
    {error && <Alert variant="error">{error}</Alert>}{notice && <Alert variant="success">{notice}</Alert>}
    {loading ? <LoadingState /> : <div className={`agenda-board${selected ? ' has-day' : ''}`}>
      <section className="panel calendar-panel" aria-label={`Calendário de ${monthLabel}`} style={{ '--calendar-weeks': grid.weeks } as CSSProperties}>
        <div className="calendar">
          {weekdays.map((day, index) => <div key={day} className={`calendar-head${index >= 5 ? ' is-weekend' : ''}`}>{day}</div>)}
          {grid.cells.map(cell => {
            if (!cell.inMonth) return <div key={cell.iso} className={`calendar-outside${cell.weekend ? ' is-weekend' : ''}`} aria-hidden="true"><span>{cell.day}</span></div>;
            const items = byDay.get(cell.iso) ?? [];
            const shown = items.slice(0, 3);
            return <button key={cell.iso} type="button" className={`calendar-day${selected === cell.iso ? ' is-selected' : ''}${cell.iso === today ? ' is-today' : ''}${cell.weekend ? ' is-weekend' : ''}`} aria-pressed={selected === cell.iso} aria-label={dayName(cell.iso, items.length)} onClick={() => setSelected(cell.iso)}>
              <span className="calendar-date">{cell.day}</span>
              <span className="calendar-events">
                {shown.map(item => <span key={item.id} className="calendar-chip"><span className="calendar-time">{item.starts_at.slice(0, 5)}</span> <span className="calendar-title">{item.title}</span></span>)}
                {items.length > shown.length && <span className="calendar-more">+{items.length - shown.length}</span>}
              </span>
            </button>;
          })}
        </div>
      </section>
      {selected && <section className="panel day-detail" aria-label="Agendamentos do dia"><h2>{formatDay(selected)}</h2>
        {selectedRows.length === 0 ? <p>Nenhum agendamento neste dia.</p> : <ul>{selectedRows.map(item => <li key={item.id}><strong>{item.starts_at.slice(0, 5)} · {item.title}</strong>{item.details && <p>{item.details}</p>}</li>)}</ul>}
        {writable && <form onSubmit={schedule} key={`${selected}:${revision}`}><fieldset disabled={busy}><FormField label="Título" name="title" required maxLength={120} /><FormField label="Hora" name="starts_at" type="time" required /><label className="form-field">Detalhes<textarea name="details" maxLength={500} aria-label="Detalhes" /></label><div className="actions"><button type="submit">Agendar</button></div></fieldset></form>}
      </section>}
    </div>}
  </div>;
}
