import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { saveSession } from '../lib/session';
import { registerBusiness } from '../services/auth';

const inputClass = 'mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-emerald-400';

type FieldProps = {
  label: string; value: string; onChange: (value:string)=>void;
  required?: boolean; type?: string;
  autoComplete?: string; maxLength?: number;
  placeholder?: string;
};
function Field({label,value,onChange,required=true,type='text',autoComplete,maxLength,placeholder}:FieldProps) {
  return <label className='block text-sm font-medium text-slate-200'>{label}
    <input className={inputClass} type={type} value={value} onChange={e=>onChange(e.target.value)} required={required} maxLength={maxLength} autoComplete={autoComplete} placeholder={placeholder}/>
  </label>;
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const planCode = searchParams.get('plan') === 'PRO' ? 'PRO' : 'STARTER';
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', confirm_password: '',
    legal_name: '', tax_id: '', trade_name: '', address: '', postal_code: '', city: '', province: '',
  });
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  function update(name: keyof typeof form, value:string) {
    setForm(previous => ({...previous,[name]:value}));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError('');
    if (form.password.length < 8) { setError('La contraseña debe tener al menos ocho caracteres.'); return; }
    if (form.password !== form.confirm_password) { setError('Las contraseñas no coinciden.'); return; }
    if (!agreed) { setError('Confirma que comprendes que se trata de una demostración.'); return; }
    setLoading(true);
    try {
      const result = await registerBusiness({
        business: {
          legal_name:form.legal_name.trim(), tax_id:form.tax_id.trim().toUpperCase(),
          trade_name:form.trade_name.trim() || null,
          address:form.address.trim(), postal_code:form.postal_code.trim(),
          city:form.city.trim(), province:form.province.trim(), country_code:'ES',
        },
        user: { full_name:form.full_name.trim(), email:form.email.trim(), password:form.password },
      });
      saveSession(result.access_token);
      navigate(`/checkout?plan=${planCode}`, { replace:true });
    } catch(err) {
      const message = err instanceof Error ? err.message : 'No se pudo crear la cuenta.';
      if (message.includes('tax ID already exists')) setError('Ya hay una empresa registrada con ese NIF/CIF.');
      else if (message.includes('email already exists')) setError('El correo electrónico ya está registrado.');
      else setError(message);
    } finally { setLoading(false); }
  }

  return <main className='min-h-screen bg-[#070b17] px-5 py-10 text-white'>
    <div className='mx-auto max-w-3xl'>
      <div className='flex flex-wrap items-center justify-between gap-4'><Link to='/' className='text-xl font-extrabold'>Veri<span className='text-emerald-400'>Factu.</span></Link><Link to='/login' className='text-sm text-slate-300 hover:text-emerald-300'>Ya tengo una cuenta →</Link></div>
      <div className='mt-9 rounded-2xl border border-slate-700/70 bg-slate-900 p-6 shadow-2xl sm:p-9'>
        <p className='text-xs font-semibold uppercase tracking-widest text-emerald-400'>Paso 1 de 2 · Alta de negocio</p>
        <h1 className='mt-3 text-3xl font-bold'>Crea tu espacio</h1>
        <p className='mt-3 text-sm leading-6 text-slate-400'>Registra una empresa y su usuario administrador. A continuación podrás activar el plan mensual simulado <strong className='text-slate-200'>{planCode==='PRO'?'Profesional':'Inicio'}</strong>.</p>
        {error && <p role='alert' className='mt-6 rounded-lg border border-red-900 bg-red-900/30 px-4 py-3 text-sm text-red-200'>{error}</p>}
        <form onSubmit={submit} className='mt-8 space-y-8'>
          <fieldset><legend className='mb-5 border-b border-slate-700 pb-3 text-lg font-semibold'>Tu cuenta</legend>
            <div className='grid gap-5 sm:grid-cols-2'>
              <Field label='Nombre y apellidos' value={form.full_name} onChange={v=>update('full_name',v)} maxLength={150} autoComplete='name'/>
              <Field label='Correo electrónico' value={form.email} onChange={v=>update('email',v)} type='email' autoComplete='email'/>
              <Field label='Contraseña (mínimo 8 caracteres)' value={form.password} onChange={v=>update('password',v)} type='password' autoComplete='new-password' maxLength={128}/>
              <Field label='Confirmar contraseña' value={form.confirm_password} onChange={v=>update('confirm_password',v)} type='password' autoComplete='new-password' maxLength={128}/>
            </div>
          </fieldset>
          <fieldset><legend className='mb-5 border-b border-slate-700 pb-3 text-lg font-semibold'>Datos de tu negocio</legend>
            <div className='grid gap-5 sm:grid-cols-2'>
              <Field label='Razón social / nombre fiscal' value={form.legal_name} onChange={v=>update('legal_name',v)} maxLength={150}/>
              <Field label='NIF / CIF / NIE' value={form.tax_id} onChange={v=>update('tax_id',v)} maxLength={20}/>
              <div className='sm:col-span-2'><Field label='Nombre comercial (opcional)' value={form.trade_name} onChange={v=>update('trade_name',v)} required={false} maxLength={150}/></div>
              <div className='sm:col-span-2'><Field label='Dirección fiscal' value={form.address} onChange={v=>update('address',v)} maxLength={255} autoComplete='street-address'/></div>
              <Field label='Código postal' value={form.postal_code} onChange={v=>update('postal_code',v)} maxLength={10} autoComplete='postal-code'/>
              <Field label='Ciudad' value={form.city} onChange={v=>update('city',v)} maxLength={100} autoComplete='address-level2'/>
              <Field label='Provincia' value={form.province} onChange={v=>update('province',v)} maxLength={100} autoComplete='address-level1'/>
              <div><p className='text-sm font-medium text-slate-200'>País</p><p className='mt-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-300'>España (ES)</p></div>
            </div>
          </fieldset>
          <label className='flex items-start gap-3 text-sm leading-6 text-slate-300'><input type='checkbox' checked={agreed} onChange={e=>setAgreed(e.target.checked)} required className='mt-1 h-4 w-4 accent-emerald-400'/><span>Comprendo que es una demostración técnica, que el plan y los precios son ficticios y que no se realizará ningún cobro. La aplicación todavía no cumple los requisitos fiscales de VERI*FACTU.</span></label>
          <button disabled={loading} type='submit' className='w-full rounded-lg bg-emerald-400 px-6 py-4 font-bold text-slate-950 hover:bg-emerald-300 disabled:opacity-60'>{loading?'Creando cuenta...':'Crear cuenta y continuar →'}</button>
        </form>
      </div>
      <p className='mt-5 text-center text-xs text-slate-500'>No introduzcas datos fiscales reales si solo deseas probar el prototipo.</p>
    </div>
  </main>;
}
