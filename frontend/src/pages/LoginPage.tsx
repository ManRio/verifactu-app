import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { consumeSessionNotice, saveSession } from '../lib/session';
import { login } from '../services/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice] = useState(() => consumeSessionNotice());
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(''); setLoading(true);
    try {
      const result = await login({ email, password });
      saveSession(result.access_token);
      navigate('/products', { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : '';
      setError(message.includes('Incorrect email') ? 'Correo o contraseña incorrectos.' : message || 'No se pudo iniciar sesión.');
    } finally { setLoading(false); }
  }

  return (
    <main className='flex min-h-screen items-center justify-center bg-[#070b17] px-5 py-12 text-white'>
      <div className='w-full max-w-md'>
        <Link to='/' className='text-xl font-extrabold'>Veri<span className='text-emerald-400'>Factu.</span></Link>
        <div className='mt-8 rounded-2xl border border-slate-700/70 bg-slate-900 p-7 shadow-2xl sm:p-9'>
          <p className='text-xs font-semibold uppercase tracking-widest text-emerald-400'>Bienvenido de nuevo</p>
          <h1 className='mt-3 text-3xl font-bold'>Iniciar sesión</h1>
          <p className='mt-2 text-sm text-slate-400'>Accede al espacio de gestión de tu negocio.</p>
          {notice && <p role='status' className='mt-5 rounded-lg border border-amber-700/50 bg-amber-900/25 px-4 py-3 text-sm text-amber-200'>{notice}</p>}
          {error && <p role='alert' className='mt-5 rounded-lg border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-200'>{error}</p>}
          <form onSubmit={submit} className='mt-7 space-y-5'>
            <div><label htmlFor='login-email' className='mb-2 block text-sm font-medium'>Correo electrónico</label><input id='login-email' autoComplete='email' type='email' required value={email} onChange={e=>setEmail(e.target.value)} placeholder='tu@email.com' className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-emerald-400'/></div>
            <div><label htmlFor='login-password' className='mb-2 block text-sm font-medium'>Contraseña</label><input id='login-password' autoComplete='current-password' type='password' minLength={8} required value={password} onChange={e=>setPassword(e.target.value)} className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-emerald-400'/></div>
            <button type='submit' disabled={loading} className='w-full rounded-lg bg-emerald-400 px-5 py-3 font-bold text-slate-950 hover:bg-emerald-300 disabled:opacity-60'>{loading?'Accediendo...':'Entrar a mi espacio →'}</button>
          </form>
          <p className='mt-7 text-center text-sm text-slate-400'>¿Aún no tienes cuenta? <Link to='/register' className='font-semibold text-emerald-300 hover:underline'>Crear cuenta</Link></p>
        </div>
        <p className='mt-5 text-center text-xs text-slate-500'>Prototipo técnico · No conforme a VERI*FACTU</p>
      </div>
    </main>
  );
}
