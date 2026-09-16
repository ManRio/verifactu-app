import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { login } from '../services/auth';

function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError('');
    setIsLoading(true);

    try {
      const response = await login({
        email,
        password,
      });

      localStorage.setItem('access_token', response.access_token);

      navigate('/products');
    } catch {
      setError('Email o contraseña incorrectos');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className='flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white'>
      <section className='w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl'>
        <div className='mb-8'>
          <p className='text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400'>
            VeriFactu App
          </p>

          <h1 className='mt-3 text-3xl font-bold'>Iniciar sesión</h1>

          <p className='mt-2 text-sm text-slate-400'>
            Accede a la gestión de tu negocio.
          </p>
        </div>

        <form className='space-y-5' onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor='email'
              className='mb-2 block text-sm font-medium text-slate-200'
            >
              Email
            </label>

            <input
              id='email'
              type='email'
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder='tu@email.com'
              autoComplete='email'
              required
              className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-emerald-500'
            />
          </div>

          <div>
            <label
              htmlFor='password'
              className='mb-2 block text-sm font-medium text-slate-200'
            >
              Contraseña
            </label>

            <input
              id='password'
              type='password'
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder='••••••••'
              autoComplete='current-password'
              required
              className='w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-emerald-500'
            />
          </div>

          {error && (
            <p className='rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-sm text-red-300'>
              {error}
            </p>
          )}

          <button
            type='submit'
            disabled={isLoading}
            className='w-full rounded-lg bg-emerald-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60'
          >
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </section>
    </main>
  );
}

export default LoginPage;
