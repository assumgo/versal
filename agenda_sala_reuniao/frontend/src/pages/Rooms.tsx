import { useEffect, useState, type FormEvent } from 'react';
import { createRoom, listRooms, updateRoom, type Room } from '../api/rooms';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/AuthProvider';
import { Alert } from '../components/Alert';
import { FormField } from '../components/FormField';

const empty = { name: '', location: '', capacity: '8', active: true };

export function Rooms() {
  const auth = useAuth();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);

  function load() {
    return listRooms().then(setRooms).catch(cause => setError(errorMessage(cause)));
  }
  useEffect(() => { void load(); }, []);

  function edit(room: Room) {
    setEditing(room.id);
    setForm({ name: room.name, location: room.location, capacity: String(room.capacity), active: room.is_active });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');
    const body = { name: form.name, location: form.location, capacity: Number(form.capacity), is_active: form.active };
    try {
      if (editing === null) await createRoom(body);
      else await updateRoom(editing, body);
      setEditing(null);
      setForm(empty);
      await load();
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return <>
    <header className="page-heading">
      <h1>Salas</h1>
      <p>Cadastre as salas e desative as que não puderem ser reservadas.</p>
    </header>
    {error && <Alert variant="error">{error}</Alert>}
    <div className={auth.user?.is_admin ? 'split' : ''}>
      <section className="panel">
        <div className="table-scroll">
          <table>
            <caption>Salas cadastradas</caption>
            <thead><tr><th>Nome</th><th>Local</th><th>Capacidade</th><th>Situação</th>{auth.user?.is_admin && <th>Ação</th>}</tr></thead>
            <tbody>
              {rooms.map(room => <tr key={room.id}>
                <td>{room.name}</td>
                <td>{room.location || '—'}</td>
                <td>{room.capacity}</td>
                <td><span className={room.is_active ? 'status-badge' : 'status-badge inactive'}>{room.is_active ? 'Ativa' : 'Inativa'}</span></td>
                {auth.user?.is_admin && <td><button type="button" className="secondary" onClick={() => edit(room)}>Editar</button></td>}
              </tr>)}
            </tbody>
          </table>
          {rooms.length === 0 && <p className="empty">Nenhuma sala cadastrada.</p>}
        </div>
      </section>
      {auth.user?.is_admin && <section className="panel">
        <form className="form-grid" onSubmit={submit}>
          <h2>{editing === null ? 'Nova sala' : 'Editar sala'}</h2>
          <FormField label="Nome" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} required />
          <FormField label="Local" value={form.location} onChange={event => setForm({ ...form, location: event.target.value })} />
          <FormField label="Capacidade" type="number" min={1} max={500} value={form.capacity} onChange={event => setForm({ ...form, capacity: event.target.value })} required />
          <label className="check-field"><input type="checkbox" checked={form.active} onChange={event => setForm({ ...form, active: event.target.checked })} /> Sala ativa</label>
          <div className="actions">
            {editing !== null && <button type="button" className="secondary" onClick={() => { setEditing(null); setForm(empty); }}>Cancelar</button>}
            <button type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Salvar'}</button>
          </div>
        </form>
      </section>}
    </div>
  </>;
}
