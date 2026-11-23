import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { resendVerification, verifyEmail } from '../services/auth';

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const employee = params.get('type') === 'worker';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [email, setEmail] = useState(params.get('email') || '');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function activate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError('');
    if (employee && password !== confirm) { setError('Las contraseñas no coinciden.'); return; }
    setBusy(true);
    try {
      await verifyEmail(token, employee ? password : undefined);
      setMessage('Cuenta activada. Ya puedes iniciar sesión.');
    } catch (err) { setError(err instanceof Error ? err.message : 'No se pudo activar la cuenta.'); }
    finally { setBusy(false); }
  }
  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    try { await resendVerification(email.trim()); setMessage('Si la cuenta está pendiente, recibirás un nuevo enlace.'); }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo solicitar otro enlace'); }
    finally { setBusy(false); }
  }
  const input = 'mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white focus:border-emerald-400';
  return <main className='flex min-h-screen items-center justify-center bg-[#070b17] px-5 py-10 text-white'>
    <section className='w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-8 shadow-2xl'>
      <Link to='/' className='text-2xl font-black'>Veri<span className='text-emerald-400'>Factu.</span></Link>
      <h1 className='mt-8 text-2xl font-bold'>{token ? 'Activar cuenta' : 'Reenviar confirmación'}</h1>
      <p className='mt-2 text-sm text-slate-400'>{employee ? 'Elige una contraseña para activar tu acceso como trabajador.' : 'Confirma tu correo para acceder a la aplicación.'}</p>
      {error && <p role='alert' className='mt-5 rounded-lg border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-200'>{error}</p>}
      {message && <p role='status' className='mt-5 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm text-emerald-200'>{message}</p>}
      {token && !message && <form onSubmit={activate} className='mt-7 space-y-4'>
        {employee && <><label className='block text-sm'>Nueva contraseña
          <input className={input} type='password' minLength={8} maxLength={128} required autoComplete='new-password' value={password} onChange={e => setPassword(e.target.value)}/>
        </label><label className='block text-sm'>Repetir contraseña
          <input className={input} type='password' minLength={8} maxLength={128} required autoComplete='new-password' value={confirm} onChange={e => setConfirm(e.target.value)}/>
        </label></>}
        <button disabled={busy} className='w-full rounded-xl bg-emerald-400 py-3 font-bold text-slate-950 disabled:opacity-50'>{busy ? 'Activando...' : 'Confirmar y activar'}</button>
      </form>}
      {!token && <form onSubmit={resend} className='mt-7 space-y-4'>
        <label className='block text-sm'>Correo electrónico
          <input className={input} type='email' required value={email} onChange={e => setEmail(e.target.value)}/>
        </label>
        <button disabled={busy} className='w-full rounded-xl bg-emerald-400 py-3 font-bold text-slate-950 disabled:opacity-50'>Reenviar enlace</button>
      </form>}
      <div className='mt-7 flex flex-wrap justify-between gap-3 text-sm'>
        <Link to='/login' className='text-emerald-300 hover:underline'>Iniciar sesión</Link>
        {token && <Link to='/verify-email' className='text-slate-400 hover:underline'>Solicitar otro enlace</Link>}
      </div>
    </section>
  </main>;
}
