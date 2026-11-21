import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import { getMySubscription } from '../services/subscription';

/** Gate de onboarding; el backend también exige un plan demo activo en sus APIs privadas. */
export default function SubscriptionGate() {
  const [status, setStatus] = useState<'loading' | 'allowed' | 'pending' | 'error'>('loading');
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let live = true;
    void getMySubscription().then(subscription => {
      if (live) setStatus(subscription && subscription.status !== 'DEMO_ACTIVE' ? 'pending' : 'allowed');
    }).catch(() => { if (live) setStatus('error'); });
    return () => { live = false; };
  }, [retry]);

  if (status === 'pending') return <Navigate to='/checkout' replace />;
  if (status === 'loading') return <div role='status' className='min-h-screen bg-slate-950 p-10 text-center text-slate-300'>Preparando tu espacio...</div>;
  if (status === 'error') return (
    <div className='flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 p-6 text-white'>
      <p>No se pudo verificar tu suscripción de demostración.</p>
      <button className='rounded-lg bg-emerald-500 px-5 py-2 font-semibold text-slate-950' onClick={() => { setStatus('loading'); setRetry(n => n + 1); }}>Reintentar</button>
    </div>
  );
  return <Outlet />;
}
