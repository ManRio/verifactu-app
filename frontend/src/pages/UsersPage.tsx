import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { inviteWorker, listWorkers, setWorkerActive } from '../services/users';
import { getMySubscription } from '../services/subscription';
import type { DemoSubscription } from '../types/subscription';
import type { BusinessUser } from '../services/users';

export default function UsersPage() {
  const [users, setUsers] = useState<BusinessUser[]>([]);
  const [plan, setPlan] = useState<DemoSubscription | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function reload() {
    try { const [items, subscription] = await Promise.all([listWorkers(), getMySubscription()]); setUsers(items); setPlan(subscription); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Error al consultar usuarios'); }
  }
  useEffect(() => {
    let mounted = true;
    void listWorkers()
      .then((data) => {
        if (mounted) {
          setUsers(data);
          setError('');
        }
      })
      .catch((err: unknown) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Error al consultar usuarios');
        }
      });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let live = true;
    void getMySubscription().then(data => { if (live) setPlan(data); }).catch(() => {});
    return () => { live = false; };
  }, []);

  async function toggleWorker(user: BusinessUser) {
    if (user.role !== 'WORKER') return;
    setBusy(true); setError(''); setMessage('');
    try {
      await setWorkerActive(user.id, !user.is_active);
      await reload();
      setMessage(user.is_active ? 'Trabajador desactivado.' : 'Trabajador reactivado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo modificar el estado');
    } finally { setBusy(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      await inviteWorker({ email: email.trim().toLowerCase(), full_name: name.trim() });
      setName(''); setEmail('');
      setMessage('Invitación preparada. El trabajador debe activar su cuenta desde el enlace recibido.');
      await reload();
    } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo crear el usuario'); }
    finally { setBusy(false); }
  }

  return <main className='min-h-screen bg-slate-950 px-4 py-9 text-white sm:px-7'>
    <div className='mx-auto max-w-5xl space-y-8'>
      <header><p className='text-xs font-bold uppercase tracking-widest text-emerald-400'>Solo superusuario</p>
        <h1 className='mt-2 text-3xl font-bold'>Trabajadores</h1>
        <p className='mt-2 text-slate-400'>Invita a personas de tu empresa. Podrán gestionar la actividad comercial, pero no crear cuentas ni consultar el resumen contable global.</p>
      </header>
      <section className='rounded-2xl border border-slate-800 bg-slate-900 p-6'>
        <h2 className='mb-2 text-lg font-semibold'>Invitar trabajador</h2>
        {plan && <p className='mb-5 text-sm text-slate-400'>Plan: {plan.plan_name ?? 'Sin plan'} · {plan.active_workers} / {plan.max_workers} trabajadores · {plan.available_workers} plazas libres.</p>}
        {error && <p role='alert' className='mb-4 rounded-xl border border-rose-600/40 bg-rose-500/10 px-4 py-3 text-rose-200'>{error}</p>}
        {message && <p role='status' className='mb-4 rounded-xl border border-emerald-500/30 bg-emerald-400/10 px-4 py-3 text-emerald-200'>{message}</p>}
        <form onSubmit={submit} className='grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end'>
          <label className='block text-sm text-slate-300'>Nombre y apellidos
            <input required maxLength={150} value={name} onChange={e => setName(e.target.value)} className='mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white'/>
          </label>
          <label className='block text-sm text-slate-300'>Correo de trabajo
            <input required type='email' value={email} onChange={e => setEmail(e.target.value)} className='mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white'/>
          </label>
          <button disabled={busy} className='rounded-xl bg-emerald-400 px-5 py-3 font-bold text-slate-950 disabled:opacity-50'>{busy ? 'Enviando...' : 'Enviar invitación'}</button>
        </form>
        <p className='mt-4 text-xs text-slate-500'>El trabajador elige su propia contraseña cuando verifica el correo. El enlace caduca a las 24 horas.</p>
      </section>
      <section className='overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900'>
        <table className='w-full min-w-[650px] text-left text-sm'>
          <thead className='border-b border-slate-800 text-slate-400'><tr><th className='p-5'>Nombre</th><th className='p-5'>Correo</th><th className='p-5'>Rol</th><th className='p-5'>Activación</th><th className='p-5'>Estado / acción</th></tr></thead>
          <tbody className='divide-y divide-slate-800'>{users.map(user => <tr key={user.id}>
            <td className='p-5 font-medium'>{user.full_name}</td><td className='p-5 text-slate-300'>{user.email}</td>
            <td className='p-5'>{user.role === 'SUPERUSER' ? 'Superusuario' : 'Trabajador'}</td>
            <td className='p-5 text-slate-300'>{user.email_verified ? 'Verificado' : 'Pendiente de email'}</td>
            <td className='p-5'><button type='button' disabled={busy || user.role !== 'WORKER'} onClick={() => void toggleWorker(user)} className='rounded-lg border border-slate-700 px-3 py-2 text-xs text-emerald-300 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40'>{user.role === 'SUPERUSER' ? 'Propietario' : user.is_active ? 'Desactivar' : 'Reactivar'}</button></td>
          </tr>)}</tbody>
        </table>
        {users.length === 0 && <p className='p-6 text-slate-400'>Todavía no se muestran usuarios.</p>}
      </section>
    </div>
  </main>;
}
