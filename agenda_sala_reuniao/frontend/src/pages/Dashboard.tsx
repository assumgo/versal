import { useEffect, useState } from 'react';
import { listReservations, type Reservation } from '../api/reservations';
import { errorMessage } from '../api/client';
import { Alert } from '../components/Alert';
import { addDays, dayRange, formatCivilDay, formatMonth, formatSlot, monthRange, todayInSaoPaulo, weekRange } from '../time';

function overlaps(item: Reservation, from: string, to: string) {
  return new Date(item.starts_at) < new Date(to) && new Date(item.ends_at) > new Date(from);
}

function ReservationTable({ caption, items, empty }: { caption: string; items: Reservation[]; empty: string }) {
  return <section className="panel">
    <div className="section-heading"><h2>{caption}</h2></div>
    <div className="table-scroll">
      <table>
        <caption>{caption}</caption>
        <thead><tr><th>Horário</th><th>Sala</th><th>Título</th><th>Responsável</th></tr></thead>
        <tbody>
          {items.map(item => <tr key={`${caption}-${item.id}`}>
            <td>{formatSlot(item.starts_at)} – {formatSlot(item.ends_at)}</td>
            <td>{item.room_name}</td>
            <td>{item.title}</td>
            <td>{item.user_name}</td>
          </tr>)}
        </tbody>
      </table>
      {items.length === 0 && <p className="empty">{empty}</p>}
    </div>
  </section>;
}

export function Dashboard() {
  const today = todayInSaoPaulo();
  const day = dayRange(today);
  const week = weekRange(today);
  const month = monthRange(today);
  const [weekItems, setWeekItems] = useState<Reservation[]>([]);
  const [monthItems, setMonthItems] = useState<Reservation[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([
      listReservations(week.from, week.to, ''),
      listReservations(month.from, month.to, ''),
    ]).then(([weekRows, monthRows]) => {
      if (!active) return;
      setWeekItems(weekRows);
      setMonthItems(monthRows);
    }).catch(cause => { if (active) setError(errorMessage(cause)); });
    return () => { active = false; };
  }, [week.from, week.to, month.from, month.to]);

  const dayItems = monthItems.filter(item => overlaps(item, day.from, day.to));

  return <>
    <header className="page-heading">
      <h1>Painel</h1>
      <p>Reservas de hoje, desta semana e deste mês. Horários em 24 horas, no fuso America/Sao_Paulo.</p>
    </header>
    {error && <Alert variant="error">{error}</Alert>}
    <div className="stats-grid">
      <article className="stat-card"><h2>Hoje</h2><strong>{dayItems.length}</strong><p>{formatCivilDay(today)}</p></article>
      <article className="stat-card"><h2>Esta semana</h2><strong>{weekItems.length}</strong><p>{formatCivilDay(week.start)} a {formatCivilDay(addDays(week.start, 6))}</p></article>
      <article className="stat-card"><h2>Este mês</h2><strong>{monthItems.length}</strong><p>{formatMonth(today)}</p></article>
    </div>
    <ReservationTable caption="Reservas do dia" items={dayItems} empty="Nenhuma reserva hoje." />
    <ReservationTable caption="Reservas da semana" items={weekItems} empty="Nenhuma reserva nesta semana." />
    <ReservationTable caption="Reservas do mês" items={monthItems} empty="Nenhuma reserva neste mês." />
  </>;
}
