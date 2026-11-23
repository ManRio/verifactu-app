import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { getMe } from '../services/auth';

export default function SuperuserGate() {
  const [result, setResult] = useState<'loading' | 'allowed' | 'blocked' | 'error'>('loading');
  useEffect(() => {
    let active = true;
    void getMe().then(user => { if (active) setResult(user.role === 'SUPERUSER' ? 'allowed' : 'blocked'); })
      .catch(() => { if (active) setResult('error'); });
    return () => { active = false; };
  }, []);
  if (result === 'blocked') return <Navigate to='/products' replace/>;
  if (result === 'loading') return <div role='status' className='min-h-screen bg-slate-950 p-8 text-slate-300'>Validando permisos...</div>;
  if (result === 'error') return <p role='alert' className='p-8 text-red-300'>No se pudieron validar tus permisos.</p>;
  return <Outlet/>;
}
