import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { activateDemoPlan, getPlans } from '../services/subscription';
import type { DemoPlan } from '../types/subscription';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const selected = params.get('plan') === 'PRO' ? 'PRO' : 'STARTER';
  const [plans, setPlans] = useState<DemoPlan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let live = true;
    void getPlans().then(data => { if (live) { setPlans(data); setError(''); } })
      .catch(err => { if (live) setError(err instanceof Error ? err.message : 'No se pudieron cargar los planes'); })
      .finally(() => { if (live) setLoadingPlans(false); });
    return () => { live = false; };
  }, []);

  const plan = plans.find(item => item.code === selected);

  async function activate() {
    if (!plan || saving) return;
    setError(''); setSaving(true);
    try {
      await activateDemoPlan(plan.code);
      navigate('/products', {replace:true});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error en la activación');
    } finally { setSaving(false); }
  }

  return <main className='min-h-screen bg-[#070b17] px-5 py-12 text-white'>
    <div className='mx-auto max-w-4xl'>
      <div className='flex flex-wrap justify-between gap-4'><Link to='/' className='text-xl font-extrabold'>Veri<span className='text-emerald-400'>Factu.</span></Link><Link to='/subscription' className='text-sm text-slate-400 hover:text-white'>Consultar mi suscripción</Link></div>
      <p className='mt-12 text-xs font-bold uppercase tracking-widest text-emerald-400'>Paso 2 de 2 · Contratación simulada</p>
      <h1 className='mt-3 text-4xl font-bold'>Elige tu plan mensual.</h1>
      <p className='mt-4 max-w-2xl leading-7 text-slate-300'>Activaremos una suscripción <strong>de demostración</strong> vinculada a tu empresa. No introduzcas tarjeta ni datos bancarios: no existe cobro real.</p>

      {error && <p role='alert' className='mt-6 rounded-xl border border-red-800 bg-red-950/40 p-4 text-sm text-red-200'>{error}</p>}
      {loadingPlans && <p className='mt-8 text-slate-400'>Consultando planes...</p>}
      {!loadingPlans && <div className='mt-9 grid gap-5 md:grid-cols-2'>
        {plans.map(item => <button type='button' key={item.code} aria-pressed={selected===item.code} onClick={() => setParams({plan:item.code})} className={`rounded-2xl border p-6 text-left transition ${selected===item.code ? 'border-emerald-400 bg-emerald-400/10':'border-slate-700 bg-slate-900 hover:border-slate-500'}`}>
          <div className='flex justify-between'><h2 className='text-xl font-bold'>{item.name}</h2><span className='text-emerald-300'>{selected===item.code?'● Seleccionado':'○ Elegir'}</span></div>
          <p className='mt-6 text-3xl font-bold'>{Number(item.monthly_price_eur).toLocaleString('es-ES',{style:'currency',currency:'EUR'})}<span className='ml-2 text-sm font-normal text-slate-400'>/ mes (ficticio)</span></p>
          <ul className='mt-6 space-y-3 text-sm text-slate-300'>{item.features.map(feature=><li key={feature}>✓ {feature}</li>)}</ul>
        </button>)}
      </div>}

      <div className='mt-9 rounded-2xl border border-slate-700 bg-slate-900 p-7'>
        <h2 className='text-xl font-semibold'>Resumen de la demostración</h2>
        <div className='mt-5 flex flex-wrap justify-between gap-3 border-b border-slate-700 pb-5 text-slate-300'><span>Plan mensual: {plan?.name ?? '—'}</span><span>{plan ? Number(plan.monthly_price_eur).toLocaleString('es-ES',{style:'currency',currency:'EUR'}) : '—'} / mes*</span></div>
        <div className='mt-5 flex justify-between font-bold'><span>Importe que se cobrará</span><span className='text-emerald-300'>0,00 €</span></div>
        <p className='mt-5 text-xs leading-6 text-slate-400'>* Precio ilustrativo. Se registrará una fecha de fin del período de demostración, sin renovación automática ni solicitud de tarjeta. Esto no es una contratación comercial real.</p>
        <button type='button' disabled={!plan || saving} onClick={() => void activate()} className='mt-7 w-full rounded-xl bg-emerald-400 px-6 py-4 font-bold text-slate-950 hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50'>{saving?'Activando...':'Confirmar suscripción simulada →'}</button>
      </div>
    </div>
  </main>;
}
