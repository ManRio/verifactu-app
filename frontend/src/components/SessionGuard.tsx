import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { SESSION_EVENT, endSession, getToken, tokenExpired } from '../lib/session';
import { getMe } from '../services/auth';

/** Protege rutas: exp local, verificación real /auth/me y expiración en peticiones. */
export default function SessionGuard() {
  const location = useLocation();
  const [state, setState] = useState<'checking' | 'valid' | 'invalid' | 'error'>(
    () => { const token = getToken(); return !token || tokenExpired(token) ? 'invalid' : 'checking'; },
  );
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    function onSessionEnded() { setState('invalid'); }
    function onStorage(event: StorageEvent) {
      if (event.key === 'access_token' && !event.newValue) setState('invalid');
    }
    window.addEventListener(SESSION_EVENT, onSessionEnded);
    function onFocus() { const token = getToken(); if (token && tokenExpired(token)) endSession('Tu sesión ha caducado. Vuelve a entrar.'); }
    window.addEventListener('storage', onStorage);
    window.addEventListener('focus', onFocus);
    return () => {
      window.removeEventListener(SESSION_EVENT, onSessionEnded);
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('focus', onFocus);
    };
  }, []);

  useEffect(() => {
    let live = true;
    const token = getToken();
    if (!token || tokenExpired(token)) {
      if (token) endSession('Tu sesión ha caducado. Vuelve a entrar.');
      return;
    }

    void getMe().then(() => {
      if (live) setState('valid');
    }).catch(() => {
      if (!live) return;
      setState(getToken() ? 'error' : 'invalid');
    });

    return () => { live = false; };
  }, [retry]);

  if (state === 'invalid') {
    return <Navigate to='/login' replace state={{ from: location.pathname }} />;
  }
  if (state === 'checking') {
    return <div role='status' className='min-h-screen bg-slate-950 p-10 text-center text-slate-300'>Validando sesión...</div>;
  }
  if (state === 'error') {
    return (
      <div className='flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 p-6 text-white'>
        <p>No se pudo contactar con el servidor para verificar la sesión.</p>
        <button className='rounded-lg bg-emerald-500 px-5 py-2 font-semibold text-slate-950' onClick={() => { setState('checking'); setRetry(n => n + 1); }}>Reintentar</button>
      </div>
    );
  }
  return <Outlet />;
}
