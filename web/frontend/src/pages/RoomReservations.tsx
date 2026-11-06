import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from 'react';
import { reservations, type Reservation } from '../api/reservations';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';
import { LoadingState } from '../components/LoadingState';
import { Users } from './Users';
import { errorMessage } from '../api/client';

const weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
const title = 'Reserva de Sala - Versal';
function currentTime() { return new Date(); }

function monthKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function shiftMonth(month: string, delta: number) {
  const [year, number] = month.split('-').map(Number);
  return monthKey(new Date(year, number - 1 + delta, 1));
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

function formatDay(iso: string) {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' });
}

function dayName(iso: string, count: number) {
  const formatted = formatDay(iso);
  if (count === 0) return `${formatted}, sem reservas`;
  return `${formatted}, ${count === 1 ? '1 reserva' : `${count} reservas`}`;
}

function clockOf(value: string) {
  const [hour, minute] = value.split(':').map(Number);
  return hour * 60 + minute;
}

function at(day: string, value: string) {
  const [year, month, date] = day.split('-').map(Number);
  const [hour, minute] = value.split(':').map(Number);
  return new Date(year, month - 1, date, hour, minute);
}

function reservationAction(item: Reservation, now: Date) {
  return at(item.scheduled_date, item.ends_at) <= now ? 'Finalizado' : 'Agendada';
}

function reservationError(day: string, starts: string, ends: string, now: Date) {
  const span = clockOf(ends) - clockOf(starts);
  if (span <= 0) return 'O horário final precisa ser depois do início.';
  if (span > 120) return 'O intervalo da reserva não pode passar de 2 horas.';
  if (at(day, starts).getTime() < now.getTime() + 30 * 60 * 1000) return 'A reserva precisa começar pelo menos 30 minutos após o horário atual.';
  return '';
}

function SavedDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!element || !open) return;
    if (typeof element.showModal === 'function') element.showModal();
    else element.open = true;
    return () => { if (typeof element.close === 'function') element.close(); element.open = false; };
  }, [open]);
  return <dialog ref={dialog} aria-labelledby="reservation-saved" onCancel={event => { event.preventDefault(); onClose(); }}>
    <h2 id="reservation-saved">Reserva gravada</h2>
    <p>A reserva foi gravada com sucesso.</p>
    <div className="actions"><button type="button" onClick={onClose} autoFocus>OK</button></div>
  </dialog>;
}

const menus = ['Calendário', 'Mês seguinte', 'Usuários'] as const;
type Menu = typeof menus[number];

export function RoomReservations({ canWrite = false, canManageUsers = false, now = currentTime, onLogout }: { canWrite?: boolean; canManageUsers?: boolean; now?: () => Date; onLogout?: () => void }) {
  const currentMonth = monthKey(now());
  const nextMonth = shiftMonth(currentMonth, 1);
  const [month, setMonth] = useState(currentMonth);
  const [menu, setMenu] = useState<Menu>('Calendário');
  const [open, setOpen] = useState(false);
  const shell = useRef<HTMLDivElement>(null);
  const wasOpen = useRef(false);
  const grid = monthGrid(month);
  const today = monthKey(now()) === month ? `${month}-${String(now().getDate()).padStart(2, '0')}` : '';
  const rawMonth = new Date(grid.year, grid.number - 1, 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
  const monthLabel = rawMonth.charAt(0).toUpperCase() + rawMonth.slice(1);
  const [rows, setRows] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [clock, setClock] = useState(() => now());
  const close = () => setOpen(false);
  function choose(next: Menu) {
    setMenu(next);
    if (next === 'Calendário') setMonth(currentMonth);
    if (next === 'Mês seguinte') setMonth(nextMonth);
    close();
  }
  useEffect(() => { document.title = title; return () => { document.title = 'Versal Folha TXT'; }; }, []);
  useEffect(() => {
    if (!open) {
      if (wasOpen.current) shell.current?.querySelector<HTMLButtonElement>('.menu-trigger')?.focus();
      wasOpen.current = false;
      return;
    }
    wasOpen.current = true;
    const desktop = window.matchMedia('(min-width: 901px)');
    const handleViewport = () => { if (desktop.matches) setOpen(false); };
    desktop.addEventListener('change', handleViewport);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    shell.current?.querySelector<HTMLButtonElement>('.drawer-close')?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close();
      if (event.key !== 'Tab') return;
      const buttons = shell.current?.querySelectorAll<HTMLButtonElement>('.sidebar button');
      if (!buttons?.length) return;
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', handleKey);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', handleKey); desktop.removeEventListener('change', handleViewport); };
  }, [open]);
  useEffect(() => { const timer = window.setInterval(() => setClock(now()), 30000); return () => window.clearInterval(timer); }, [now]);
  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); setRows([]);
    reservations.list(month).then(data => { if (active) setRows(Array.isArray(data) ? data : []); }).catch(reason => { if (active) setError(errorMessage(reason)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [month, revision]);
  useEffect(() => { setSelected(current => current?.startsWith(month) ? current : null); }, [month]);
  const byDay = new Map<string, Reservation[]>();
  for (const row of rows) {
    const list = byDay.get(row.scheduled_date) ?? [];
    list.push(row);
    byDay.set(row.scheduled_date, list);
  }
  const selectedRows = selected ? byDay.get(selected) ?? [] : [];
  async function schedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || busy) return;
    const data = new FormData(event.currentTarget);
    const starts = String(data.get('starts_at'));
    const ends = String(data.get('ends_at'));
    const details = String(data.get('details') ?? '').trim();
    const invalid = reservationError(selected, starts, ends, now());
    setError(invalid);
    if (invalid) return;
    setBusy(true);
    try {
      await reservations.create({ scheduled_date: selected, starts_at: starts, ends_at: ends, title: String(data.get('title')), details: details || null });
      setSaved(true);
      setRevision(value => value + 1);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <div className="app-shell reservation-shell" ref={shell}><a className="skip-link" href="#page-content">Ir para o conteúdo</a>
    {open && <button className="drawer-backdrop" aria-label="Fechar menu pelo fundo" tabIndex={-1} onClick={close} />}
    <aside id="sidebar" className={`sidebar${open ? ' is-open' : ''}`}>
      <button className="drawer-close" onClick={close} aria-label="Fechar menu">×</button>
      <div className="brand"><img src="/assets/logo_versal_agro.png" alt="Versal Agro Contabilidade" /><strong>{title}</strong></div>
      <nav aria-label="Navegação principal">{menus.map(item => <button key={item} type="button" aria-current={menu === item ? 'page' : undefined} onClick={() => choose(item)}>{item}</button>)}</nav>
      <footer>Reserva de Sala · Versal<br />© Versal Agro Contabilidade</footer>
    </aside>
    <div className="workspace" inert={open || undefined}>
    <header className="top-header"><button className="menu-trigger" type="button" aria-label="Abrir menu" aria-controls="sidebar" aria-expanded={open} onClick={() => setOpen(true)}>☰</button><div><p className="eyebrow">RESERVA</p><h1>{title}</h1></div><div className="reservation-toolbar">{menu !== 'Usuários' && <p className="agenda-month">{monthLabel}</p>}{onLogout && <button type="button" className="secondary" onClick={onLogout}>Sair</button>}</div></header>
    <main id="page-content">{menu === 'Usuários' ? <Users canWrite={canManageUsers} /> : <div className="agenda">
      {error && <Alert variant="error">{error}</Alert>}
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
                  {shown.map(item => <span key={item.id} className="calendar-chip"><span className="calendar-time">{item.starts_at.slice(0, 5)}–{item.ends_at.slice(0, 5)}</span> <span className="calendar-title">{item.title}</span></span>)}
                  {items.length > shown.length && <span className="calendar-more">+{items.length - shown.length}</span>}
                </span>
              </button>;
            })}
          </div>
        </section>
        {selected && <section className="panel day-detail" aria-label="Reservas do dia"><h2>{formatDay(selected)}</h2>
          {selectedRows.length === 0 ? <p>Nenhuma reserva neste dia.</p> : <ul>{selectedRows.map(item => <li key={item.id}><strong>{item.starts_at.slice(0, 5)}–{item.ends_at.slice(0, 5)} · {item.title}</strong><p>Ação: {reservationAction(item, clock)}</p>{item.details && <p>{item.details}</p>}</li>)}</ul>}
          {canWrite && <form onSubmit={schedule} key={`${selected}:${revision}`}><fieldset disabled={busy}><FormField label="Título" name="title" required maxLength={120} /><FormField label="Início" name="starts_at" type="time" required /><FormField label="Fim" name="ends_at" type="time" required /><label className="form-field">Detalhes<textarea name="details" maxLength={500} aria-label="Detalhes" /></label><div className="actions"><button type="submit">Reservar</button></div></fieldset></form>}
        </section>}
      </div>}
      <SavedDialog open={saved} onClose={() => setSaved(false)} />
    </div>}</main>
  </div></div>;
}
