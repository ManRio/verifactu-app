import { useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { consumeSessionNotice, saveSession } from '../lib/session';
import { login, registerBusiness } from '../services/auth';
import '../styles/access.css';

type AccessMode = 'login' | 'register';
type RegistrationKey = keyof RegistrationFields;
type RegistrationFields = {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  legal_name: string;
  tax_id: string;
  trade_name: string;
  address: string;
  postal_code: string;
  city: string;
  province: string;
};

const initialRegistration: RegistrationFields = {
  full_name: '', email: '', password: '', confirm_password: '',
  legal_name: '', tax_id: '', trade_name: '', address: '',
  postal_code: '', city: '', province: '',
};
const fieldClass = 'mt-2 block w-full rounded-xl border border-slate-700 bg-[#0b1425] px-4 py-3 text-white outline-none placeholder:text-slate-500 transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/15';

function TextField({ label, value, onChange, type = 'text', required = true, maxLength, autoComplete, placeholder }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  maxLength?: number;
  autoComplete?: string;
  placeholder?: string;
}) {
  return (
    <label className='block text-sm font-medium text-slate-200'>
      {label}
      <input type={type} required={required} value={value} maxLength={maxLength} autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className={fieldClass}/>
    </label>
  );
}

function EyeIcon({ visible }: { visible: boolean }) {
  return (
    <svg aria-hidden='true' viewBox='0 0 24 24' width='20' height='20' fill='none' stroke='currentColor' strokeWidth='1.8' strokeLinecap='round' strokeLinejoin='round'>
      <path d='M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12Z'/>
      <circle cx='12' cy='12' r='2.5'/>
      {!visible && <path d='M3 21 21 3' strokeWidth='2.2'/>}
    </svg>
  );
}

function PasswordField({ label, value, onChange, autoComplete }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete: string;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <label className='block text-sm font-medium text-slate-200'>
      {label}
      <span className='relative block'>
        <input type={visible ? 'text' : 'password'} value={value} onChange={(event) => onChange(event.target.value)}
          required minLength={8} maxLength={128} autoComplete={autoComplete}
          className={`${fieldClass} pr-14`}/>
        <button type='button' aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'} aria-pressed={visible}
          onClick={() => setVisible((current) => !current)}
          className='absolute bottom-1 right-1 top-3 rounded-lg px-3 text-emerald-300 transition hover:bg-emerald-400/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400'>
          <EyeIcon visible={visible}/>
        </button>
      </span>
    </label>
  );
}

function Feedback({ children, kind }: { children: ReactNode; kind: 'error' | 'notice' }) {
  return (
    <div role={kind === 'error' ? 'alert' : 'status'}
      className={`mt-5 rounded-xl border px-4 py-3 text-sm leading-6 ${kind === 'error'
        ? 'border-rose-500/40 bg-rose-500/10 text-rose-200'
        : 'border-amber-500/30 bg-amber-500/10 text-amber-200'}`}>
      {children}
    </div>
  );
}

export default function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const planCode = searchParams.get('plan') === 'PRO' ? 'PRO' : 'STARTER';
  const [mode, setMode] = useState<AccessMode>(() =>
    location.pathname === '/register' || searchParams.get('mode') === 'register' ? 'register' : 'login',
  );
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [registration, setRegistration] = useState<RegistrationFields>(initialRegistration);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [notice] = useState(() => consumeSessionNotice());
  const [loading, setLoading] = useState(false);

  function changeMode(next: AccessMode) {
    if (loading || next === mode) return;
    setError('');
    setSuccess('');
    setMode(next);
  }

  function updateRegistration(key: RegistrationKey, value: string) {
    setRegistration((current) => ({ ...current, [key]: value }));
  }

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    setError('');
    setLoading(true);
    try {
      const result = await login({ email: loginEmail.trim().toLowerCase(), password: loginPassword });
      saveSession(result.access_token);
      navigate('/products', { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : '';
      setError(message.includes('Incorrect email') || message.includes('Invalid credentials')
        ? 'El correo electrónico o la contraseña no son correctos.'
        : message || 'No se pudo iniciar sesión.');
    } finally {
      setLoading(false);
    }
  }

  async function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    if (registration.password !== registration.confirm_password) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    if (!accepted) {
      setError('Debes aceptar las condiciones de la demostración.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await registerBusiness({
        business: {
          legal_name: registration.legal_name.trim(),
          tax_id: registration.tax_id.trim().toUpperCase(),
          trade_name: registration.trade_name.trim() || null,
          address: registration.address.trim(),
          postal_code: registration.postal_code.trim(),
          city: registration.city.trim(),
          province: registration.province.trim(),
          country_code: 'ES',
        },
        user: {
          full_name: registration.full_name.trim(),
          email: registration.email.trim().toLowerCase(),
          password: registration.password,
        },
      });
      setLoginEmail(registration.email.trim().toLowerCase());
      setMode('login');
      setSuccess('Cuenta creada. Comprueba tu correo y activa la cuenta antes de iniciar sesión. Después podrás elegir tu plan de demostración.');
    } catch (err) {
      const message = err instanceof Error ? err.message : '';
      if (message.includes('tax ID already exists')) setError('Ya existe una empresa con ese NIF/CIF.');
      else if (message.includes('email already exists')) setError('Ese correo electrónico ya está registrado.');
      else setError(message || 'No se pudo crear la cuenta.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className='access-page relative isolate flex min-h-screen items-center justify-center overflow-hidden bg-[#070b17] px-4 py-9 text-white sm:px-6'>
      <div aria-hidden='true' className='access-glow access-glow-left pointer-events-none absolute -left-44 top-[-190px] h-[540px] w-[540px] rounded-full bg-emerald-500/10 blur-3xl'/>
      <div aria-hidden='true' className='access-glow access-glow-right pointer-events-none absolute -right-48 bottom-[-250px] h-[620px] w-[620px] rounded-full bg-teal-500/10 blur-3xl'/>
      <div className='relative z-10 grid w-full max-w-6xl overflow-hidden rounded-[28px] border border-slate-700/70 bg-[#0f172a] shadow-[0_35px_110px_rgba(0,0,0,0.48)] lg:grid-cols-[0.92fr_1.08fr]'>
        <aside className='access-brand relative hidden min-h-[610px] flex-col justify-between overflow-hidden border-r border-emerald-400/10 bg-gradient-to-br from-[#064e3b] via-[#073a36] to-[#0b1729] p-11 lg:flex'>
          <div aria-hidden='true' className='pointer-events-none absolute -right-32 top-28 h-72 w-72 rotate-45 rounded-[55px] border border-white/10 bg-white/5'/>
          <div aria-hidden='true' className='pointer-events-none absolute -left-40 bottom-10 h-96 w-96 rounded-full border border-emerald-300/15'/>
          <Link className='relative text-2xl font-black tracking-tight' to='/'>Veri<span className='text-emerald-300'>Factu.</span></Link>
          <div key={`hero-${mode}`} className='access-mode-enter relative'>
            <p className='text-xs font-bold uppercase tracking-[0.25em] text-emerald-200'>{mode === 'login' ? 'Tu espacio de trabajo' : 'Empieza por aquí'}</p>
            <h1 className='mt-5 max-w-sm text-5xl font-extrabold leading-tight'>{mode === 'login' ? 'Todo tu negocio, conectado.' : 'Una cuenta. Todo organizado.'}</h1>
            <p className='mt-6 max-w-sm text-base leading-8 text-emerald-50/75'>Clientes, productos, pedidos, albaranes, facturas y cobros en un mismo espacio.</p>
          </div>
          <p className='relative text-xs leading-6 text-emerald-100/65'>Proyecto de demostración · Sin cobros reales · Todavía no conforme a VERI*FACTU</p>
        </aside>

        <div className='min-w-0 px-5 py-7 sm:px-9 sm:py-10 lg:px-11'>
          <div className='flex items-center justify-between gap-3'>
            <Link to='/' className='text-xl font-black lg:hidden'>Veri<span className='text-emerald-400'>Factu.</span></Link>
            <Link to='/' className='ml-auto text-sm text-slate-400 transition hover:text-emerald-300'>← Volver a inicio</Link>
          </div>

          <div className='mt-8 grid grid-cols-2 gap-1 rounded-xl border border-slate-700 bg-[#0b1425] p-1' aria-label='Tipo de acceso'>
            <button type='button' onClick={() => changeMode('login')} aria-pressed={mode === 'login'} disabled={loading}
              className={`access-switch relative rounded-lg px-3 py-3 text-sm font-bold transition-colors disabled:opacity-60 ${mode === 'login' ? 'bg-emerald-400 text-slate-950 shadow-sm' : 'text-slate-300 hover:bg-slate-800'}`}>
              Iniciar sesión
            </button>
            <button type='button' onClick={() => changeMode('register')} aria-pressed={mode === 'register'} disabled={loading}
              className={`access-switch relative rounded-lg px-3 py-3 text-sm font-bold transition-colors disabled:opacity-60 ${mode === 'register' ? 'bg-emerald-400 text-slate-950 shadow-sm' : 'text-slate-300 hover:bg-slate-800'}`}>
              Crear cuenta
            </button>
          </div>

          <div key={mode} className='access-mode-enter'>
            <p className='mt-8 text-xs font-bold uppercase tracking-[0.24em] text-emerald-400'>{mode === 'login' ? 'Bienvenido de nuevo' : 'Alta de negocio · Paso 1 de 2'}</p>
            <h2 className='mt-3 text-3xl font-extrabold tracking-tight'>{mode === 'login' ? 'Accede a tu espacio' : 'Crea tu espacio'}</h2>
            <p className='mt-2 text-sm leading-6 text-slate-400'>{mode === 'login'
              ? 'Introduce tus credenciales para continuar.'
              : `Registra tu empresa y activa el plan de demostración ${planCode === 'PRO' ? 'Profesional' : 'Inicio'}.`}</p>

            {mode === 'login' && notice && <Feedback kind='notice'>{notice}</Feedback>}
            {success && <Feedback kind='notice'>{success} <Link className='font-bold underline' to='/verify-email'>Reenviar enlace</Link></Feedback>}
            {mode === 'login' && <p className='mt-3 text-right text-sm'><Link className='text-emerald-300 hover:underline' to='/verify-email'>¿No has recibido el correo de activación?</Link></p>}
            {error && <Feedback kind='error'><strong>No se ha podido completar la operación.</strong><p className='mt-1'>{error}</p></Feedback>}

            {mode === 'login' ? (
              <form onSubmit={(event) => void submitLogin(event)} className='mt-7 space-y-5'>
                <TextField label='Correo electrónico' value={loginEmail} onChange={setLoginEmail}
                  type='email' required maxLength={254} autoComplete='email' placeholder='tu@empresa.com'/>
                <PasswordField label='Contraseña' value={loginPassword} onChange={setLoginPassword} autoComplete='current-password'/>
                <button type='submit' disabled={loading}
                  className='w-full rounded-xl bg-emerald-400 px-5 py-3.5 font-extrabold text-slate-950 transition hover:bg-emerald-300 disabled:opacity-60'>
                  {loading ? 'Comprobando datos…' : 'Entrar a mi espacio →'}
                </button>
              </form>
            ) : (
              <form onSubmit={(event) => void submitRegistration(event)} className='mt-7 space-y-6'>
                <fieldset>
                  <legend className='mb-4 border-b border-slate-700 pb-3 text-base font-bold'>Tu cuenta</legend>
                  <div className='grid gap-4 sm:grid-cols-2'>
                    <TextField label='Nombre y apellidos' value={registration.full_name} onChange={(v) => updateRegistration('full_name', v)} maxLength={150} autoComplete='name'/>
                    <TextField label='Correo electrónico' type='email' value={registration.email} onChange={(v) => updateRegistration('email', v)} maxLength={254} autoComplete='email'/>
                    <PasswordField label='Contraseña (mínimo 8 caracteres)' value={registration.password} onChange={(v) => updateRegistration('password', v)} autoComplete='new-password'/>
                    <PasswordField label='Confirmar contraseña' value={registration.confirm_password} onChange={(v) => updateRegistration('confirm_password', v)} autoComplete='new-password'/>
                  </div>
                </fieldset>
                <fieldset>
                  <legend className='mb-4 border-b border-slate-700 pb-3 text-base font-bold'>Datos de la empresa</legend>
                  <div className='grid gap-4 sm:grid-cols-2'>
                    <TextField label='Razón social / nombre fiscal' value={registration.legal_name} onChange={(v) => updateRegistration('legal_name', v)} maxLength={150}/>
                    <TextField label='NIF / CIF / NIE' value={registration.tax_id} onChange={(v) => updateRegistration('tax_id', v)} maxLength={20}/>
                    <div className='sm:col-span-2'>
                      <TextField label='Nombre comercial (opcional)' value={registration.trade_name} onChange={(v) => updateRegistration('trade_name', v)} required={false} maxLength={150}/>
                    </div>
                    <div className='sm:col-span-2'>
                      <TextField label='Dirección fiscal' value={registration.address} onChange={(v) => updateRegistration('address', v)} maxLength={255} autoComplete='street-address'/>
                    </div>
                    <TextField label='Código postal' value={registration.postal_code} onChange={(v) => updateRegistration('postal_code', v)} maxLength={10} autoComplete='postal-code'/>
                    <TextField label='Ciudad' value={registration.city} onChange={(v) => updateRegistration('city', v)} maxLength={100} autoComplete='address-level2'/>
                    <TextField label='Provincia' value={registration.province} onChange={(v) => updateRegistration('province', v)} maxLength={100} autoComplete='address-level1'/>
                    <div><span className='block text-sm font-medium text-slate-200'>País</span><span className='mt-2 block rounded-xl border border-slate-700 bg-[#0b1425] px-4 py-3 text-sm text-slate-300'>España (ES)</span></div>
                  </div>
                </fieldset>
                <label className='flex items-start gap-3 text-sm leading-6 text-slate-300'>
                  <input type='checkbox' required checked={accepted} onChange={(event) => setAccepted(event.target.checked)}
                    className='mt-1.5 h-4 w-4 shrink-0 accent-emerald-400'/>
                  <span>Entiendo que este proyecto es una demostración: los planes son ficticios, no hay cobros reales y todavía no cumple VERI*FACTU.</span>
                </label>
                <button type='submit' disabled={loading}
                  className='w-full rounded-xl bg-emerald-400 px-5 py-3.5 font-extrabold text-slate-950 transition hover:bg-emerald-300 disabled:opacity-60'>
                  {loading ? 'Creando cuenta…' : 'Crear cuenta y continuar →'}
                </button>
              </form>
            )}
            <p className='mt-7 text-center text-sm text-slate-400'>
              {mode === 'login' ? '¿No tienes cuenta?' : '¿Ya tienes una cuenta?'}{' '}
              <button type='button' onClick={() => changeMode(mode === 'login' ? 'register' : 'login')}
                className='font-bold text-emerald-300 hover:underline'>
                {mode === 'login' ? 'Crear cuenta' : 'Iniciar sesión'}
              </button>
            </p>
            <p className='mt-5 text-center text-xs leading-5 text-slate-500'>No introduzcas datos fiscales reales para probar esta versión.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
