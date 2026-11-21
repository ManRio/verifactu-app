import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getMySubscription } from '../services/subscription';
import type { DemoSubscription } from '../types/subscription';

function date(value: string | null) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('es-ES', { dateStyle:'long' }).format(new Date(value));
}

export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<DemoSubscription | null>(null);
  const [state, setState] = useState<'loading'|'ready'|'error'>('loading');
  useEffect(()=>{
    let live=true;
    void getMySubscription().then(data=>{if(live){setSubscription(data);setState('ready');}})
      .catch(()=>{if(live)setState('error');});
    return ()=>{live=false;};
  },[]);
  return <main className='min-h-screen bg-slate-950 px-5 py-10 text-white sm:px-8'>
    <div className='mx-auto max-w-4xl'>
      <p className='text-xs font-bold uppercase tracking-widest text-emerald-400'>Cuenta y facturación de la plataforma</p>
      <h1 className='mt-3 text-3xl font-bold'>Mi suscripción</h1>
      <p className='mt-3 text-slate-400'>Este módulo es una simulación comercial. Los pagos del SaaS no están habilitados.</p>
      {state==='loading' && <p className='mt-9 text-slate-400'>Cargando suscripción...</p>}
      {state==='error' && <p className='mt-9 text-red-300'>No se pudo consultar la información de tu plan.</p>}
      {state==='ready' && <section className='mt-9 rounded-2xl border border-slate-800 bg-slate-900 p-7'>
        <span className='rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300'>Modo demostración</span>
        <h2 className='mt-5 text-2xl font-bold'>{subscription?.plan_name ?? 'Sin plan activo'}</h2>
        <p className='mt-2 text-slate-400'>{subscription?.status==='DEMO_ACTIVE'?'Suscripción simulada activada.': 'Este negocio aún no ha activado un plan simulado.'}</p>
        {subscription?.status==='DEMO_ACTIVE' && <dl className='mt-7 grid gap-5 border-t border-slate-700 pt-6 sm:grid-cols-2'>
          <div><dt className='text-sm text-slate-400'>Precio de ejemplo</dt><dd className='mt-1 font-semibold'>{subscription.monthly_price_eur ? Number(subscription.monthly_price_eur).toLocaleString('es-ES',{style:'currency',currency:'EUR'}) : '—'} / mes</dd></div>
          <div><dt className='text-sm text-slate-400'>Inicio del período</dt><dd className='mt-1 font-semibold'>{date(subscription.activated_at)}</dd></div>
          <div><dt className='text-sm text-slate-400'>Fin del período ilustrativo</dt><dd className='mt-1 font-semibold'>{date(subscription.period_end)}</dd></div>
          <div><dt className='text-sm text-slate-400'>Pagos reales procesados</dt><dd className='mt-1 font-semibold text-emerald-300'>Ninguno</dd></div>
        </dl>}
        <Link to='/checkout' className='mt-8 inline-block rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 hover:bg-emerald-300'>{subscription?.status==='DEMO_ACTIVE'?'Cambiar plan demo':'Activar plan demo'}</Link>
      </section>}
      <p className='mt-6 text-sm text-slate-500'>No hay renovación real automática, recibos ni integración con una pasarela de pago.</p>
    </div>
  </main>;
}
