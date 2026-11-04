import { useEffect, useState, type FormEvent } from 'react';
import { cancelReservation, createReservation, listReservations, type Reservation } from '../api/reservations';
import { listRooms, type Room } from '../api/rooms';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';
import { dayRange, formatSlot, saoPauloToIso, TIME_24H, todayInSaoPaulo } from '../time';

export function Agenda() {
  const auth = useAuth();
  const today = todayInSaoPaulo();
  const [day, setDay] = useState(today);
  const [roomFilter, setRoomFilter] = useState('');
  const [rooms, setRooms] = useState<Room[]>([]);
  const [items, setItems] = useState<Reservation[]>([]);
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');
  const [title, setTitle] = useState('');
  const [roomId, setRoomId] = useState('');
  const [startDate, setStartDate] = useState(today);
  const [startTime, setStartTime] = useState('09:00');
  const [endDate, setEndDate] = useState(today);
  const [endTime, setEndTime] = useState('10:00');
  const [busy, setBusy] = useState(false);

  useEffect(() => { listRooms().then(setRooms).catch(cause => setError(errorMessage(cause))); }, []);
  useEffect(() => {
    const range = dayRange(day);
    listReservations(range.from, range.to, roomFilter).then(setItems).catch(cause => setError(errorMessage(cause)));
  }, [day, roomFilter]);

  const activeRooms = rooms.filter(room => room.is_active);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError('');
    setError('');
    if (!TIME_24H.test(startTime) || !TIME_24H.test(endTime)) {
      setFormError('Use o horário de 24 horas, como 09:30 ou 14:00.');
      return;
    }
    const startsAt = saoPauloToIso(`${startDate}T${startTime}`);
    const endsAt = saoPauloToIso(`${endDate}T${endTime}`);
    if (new Date(endsAt) <= new Date(startsAt)) {
      setFormError('O fim precisa ser posterior ao início');
      return;
    }
    setBusy(true);
    try {
      await createReservation({
        room_id: Number(roomId), title, starts_at: startsAt, ends_at: endsAt,
      });
      setTitle('');
      const range = dayRange(day);
      setItems(await listReservations(range.from, range.to, roomFilter));
    } catch (cause) {
      setFormError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function cancel(item: Reservation) {
    setError('');
    try {
      await cancelReservation(item.id);
      setItems(current => current.filter(row => row.id !== item.id));
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  return <>
    <header className="page-heading">
      <h1>Agenda</h1>
      <p>Horários em America/Sao_Paulo. Uma reserva pode começar no instante em que a anterior termina.</p>
    </header>
    {error && <Alert variant="error">{error}</Alert>}
    <section className="panel">
      <form className="filters" onSubmit={event => event.preventDefault()}>
        <FormField label="Dia" type="date" value={day} onChange={event => setDay(event.target.value)} required />
        <div className="form-field">
          <label htmlFor="room-filter">Filtrar por sala</label>
          <select id="room-filter" value={roomFilter} onChange={event => setRoomFilter(event.target.value)}>
            <option value="">Todas</option>
            {rooms.map(room => <option key={room.id} value={room.id}>{room.name}</option>)}
          </select>
        </div>
      </form>
      <div className="table-scroll">
        <table>
          <caption>Reservas do dia</caption>
          <thead><tr><th>Horário</th><th>Sala</th><th>Título</th><th>Responsável</th><th>Ação</th></tr></thead>
          <tbody>
            {items.map(item => <tr key={item.id}>
              <td>{formatSlot(item.starts_at)} – {formatSlot(item.ends_at)}</td>
              <td>{item.room_name}</td>
              <td>{item.title}</td>
              <td>{item.user_name}</td>
              <td>{(item.mine || auth.user?.is_admin) && <button type="button" className="secondary" onClick={() => void cancel(item)}>Cancelar</button>}</td>
            </tr>)}
          </tbody>
        </table>
        {items.length === 0 && <p className="empty">Nenhuma reserva neste dia.</p>}
      </div>
    </section>
    <section className="panel">
      <form className="form-grid" onSubmit={submit}>
        <h2>Nova reserva</h2>
        {formError && <Alert variant="error">{formError}</Alert>}
        <div className="form-field">
          <label htmlFor="booking-room">Sala</label>
          <select id="booking-room" value={roomId} onChange={event => setRoomId(event.target.value)} required>
            <option value="">Selecione</option>
            {activeRooms.map(room => <option key={room.id} value={room.id}>{room.name}</option>)}
          </select>
        </div>
        <FormField label="Título" value={title} onChange={event => setTitle(event.target.value)} required maxLength={120} />
        <div className="when">
          <FormField label="Data de início" type="date" value={startDate} onChange={event => setStartDate(event.target.value)} required />
          <FormField label="Hora de início" value={startTime} onChange={event => setStartTime(event.target.value)} required inputMode="numeric" pattern="([01][0-9]|2[0-3]):[0-5][0-9]" placeholder="09:00" maxLength={5} />
        </div>
        <div className="when">
          <FormField label="Data de fim" type="date" value={endDate} onChange={event => setEndDate(event.target.value)} required />
          <FormField label="Hora de fim" value={endTime} onChange={event => setEndTime(event.target.value)} required inputMode="numeric" pattern="([01][0-9]|2[0-3]):[0-5][0-9]" placeholder="10:00" maxLength={5} />
        </div>
        <div className="actions"><button type="submit" disabled={busy}>{busy ? 'Reservando…' : 'Reservar'}</button></div>
      </form>
    </section>
  </>;
}
