import { Link } from 'react-router-dom';
import { getToken, tokenExpired } from '../lib/session';

const features = [
  { icon: '▦', title: 'Productos y clientes', text: 'Tu catálogo y tus contactos en un mismo espacio, siempre organizados.' },
  { icon: '▤', title: 'Pedidos y entregas', text: 'De un pedido confirmado a uno o varios albaranes con seguimiento de cantidades.' },
  { icon: '▣', title: 'Facturación', text: 'Prepara borradores, consulta desgloses y emite facturas de prueba.' },
];

const plans = [
  { code: 'STARTER', name: 'Inicio', price: '12,90', subtitle: 'Para comenzar a organizar tu negocio.', features: ['Productos y clientes', 'Pedidos y albaranes', 'Facturas de prueba'] },
  { code: 'PRO', name: 'Profesional', price: '24,90', subtitle: 'Para un flujo de trabajo más completo.', features: ['Todas las funciones actuales', 'Gestión multiusuario mediante API', 'Novedades en desarrollo'] },
] as const;

export default function LandingPage() {
  const hasSession = Boolean(getToken() && !tokenExpired(getToken()!));

  return (
    <div className='min-h-screen bg-[#070b17] text-white'>
      <header className='sticky top-0 z-30 border-b border-white/10 bg-[#070b17]/90 backdrop-blur-xl'>
        <div className='mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-5 sm:px-8'>
          <Link to='/' className='text-xl font-extrabold tracking-tight'>Veri<span className='text-emerald-400'>Factu.</span></Link>
          <nav aria-label='Secciones públicas' className='hidden items-center gap-7 text-sm text-slate-300 md:flex'>
            <a href='#funciones' className='hover:text-white'>Funciones</a>
            <a href='#planes' className='hover:text-white'>Planes</a>
            <a href='#preguntas' className='hover:text-white'>Preguntas</a>
          </nav>
          <div className='flex items-center gap-2 sm:gap-4'>
            <Link to={hasSession ? '/products' : '/login'} className='rounded-lg px-3 py-2 text-sm font-medium text-slate-200 hover:text-emerald-300'>
              {hasSession ? 'Ir al panel' : 'Iniciar sesión'}
            </Link>
            <Link to='/register' className='rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-500/10 transition hover:bg-emerald-300'>Crear cuenta</Link>
          </div>
        </div>
      </header>

      <main>
        <section className='relative overflow-hidden border-b border-white/5'>
          <div aria-hidden='true' className='pointer-events-none absolute -top-36 right-[-8%] h-[620px] w-[620px] rounded-full bg-emerald-500/10 blur-[120px]' />
          <div className='relative mx-auto grid max-w-7xl items-center gap-16 px-5 pb-24 pt-20 sm:px-8 lg:grid-cols-[1fr_0.96fr] lg:pb-32 lg:pt-28'>
            <div>
              <span className='inline-flex items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-4 py-2 text-xs font-bold uppercase tracking-widest text-emerald-300'>● Gestión comercial simplificada</span>
              <h1 className='mt-7 max-w-2xl text-5xl font-extrabold leading-[1.08] tracking-tight sm:text-6xl'>Tu negocio, <span className='text-emerald-400'>bajo control.</span></h1>
              <p className='mt-7 max-w-xl text-lg leading-8 text-slate-300'>Organiza clientes, pedidos, albaranes y facturas desde un solo lugar. Menos tareas dispersas, más claridad para tu día a día.</p>
              <div className='mt-9 flex flex-wrap gap-3'>
                <Link to='/register' className='rounded-xl bg-emerald-400 px-7 py-4 font-bold text-slate-950 transition hover:bg-emerald-300'>Comenzar demostración →</Link>
                <a href='#funciones' className='rounded-xl border border-slate-600 bg-white/5 px-7 py-4 font-semibold text-white hover:bg-white/10'>Descubrir funciones</a>
              </div>
              <p className='mt-5 text-xs leading-6 text-slate-400'>Proyecto en desarrollo. Suscripción y precios simulados: sin tarjeta y sin cargos reales. No es todavía un sistema VERI*FACTU conforme.</p>
            </div>

            <div className='relative rounded-[26px] border border-slate-700/70 bg-[#10192b] p-4 shadow-2xl shadow-black/50 sm:p-6'>
              <div className='mb-5 flex items-center justify-between border-b border-white/10 pb-5'>
                <div><p className='text-xs font-semibold uppercase tracking-widest text-emerald-400'>Vista ilustrativa</p><h2 className='mt-1 text-xl font-bold'>Resumen del negocio</h2></div>
                <div className='flex gap-1.5'><span className='h-2.5 w-2.5 rounded-full bg-slate-600'/><span className='h-2.5 w-2.5 rounded-full bg-slate-600'/><span className='h-2.5 w-2.5 rounded-full bg-emerald-400'/></div>
              </div>
              <div className='grid grid-cols-3 gap-3'>
                {[
                  {label:'Pedidos',value:'18'}, {label:'Entregas',value:'12'}, {label:'Facturas',value:'9'},
                ].map(item => <div key={item.label} className='rounded-xl border border-slate-700/60 bg-slate-950/70 p-4'><p className='text-xs text-slate-400'>{item.label}</p><p className='mt-3 text-2xl font-bold'>{item.value}</p></div>)}
              </div>
              <div className='mt-5 rounded-xl border border-slate-700/60 bg-slate-950/50 p-5'>
                <p className='mb-5 text-sm font-semibold'>Actividad comercial</p>
                <div className='flex h-32 items-end gap-3'>
                  {[44,65,52,77,61,92,74,100,83,95].map((height, index)=><div key={index} className='flex-1 rounded-t-md bg-gradient-to-t from-emerald-700 to-emerald-400/85' style={{height:`${height}%`}} />)}
                </div>
                <div className='mt-3 flex justify-between text-[11px] text-slate-500'><span>Inicio</span><span>Actividad de ejemplo</span><span>Hoy</span></div>
              </div>
              <div className='mt-5 space-y-3'>
                {[{name:'Pedido #018',status:'Confirmado',color:'text-sky-300'},{name:'Albarán #012',status:'Entregado',color:'text-emerald-300'},{name:'Factura F-000009',status:'Emitida',color:'text-emerald-300'}].map(item=><div key={item.name} className='flex justify-between gap-2 rounded-lg border border-slate-700/50 bg-slate-900/70 px-4 py-3 text-sm'><span className='text-slate-200'>{item.name}</span><span className={item.color}>{item.status}</span></div>)}
              </div>
            </div>
          </div>
        </section>

        <section id='funciones' className='scroll-mt-24 mx-auto max-w-7xl px-5 py-24 sm:px-8'>
          <p className='text-sm font-bold uppercase tracking-[0.2em] text-emerald-400'>Todo conectado</p>
          <h2 className='mt-3 max-w-2xl text-3xl font-bold sm:text-4xl'>De la primera venta a la factura.</h2>
          <p className='mt-4 max-w-2xl text-slate-400'>Un flujo claro para consultar cada documento y encontrar su relación con los anteriores.</p>
          <div className='mt-12 grid gap-5 md:grid-cols-3'>
            {features.map(item=><article key={item.title} className='rounded-2xl border border-slate-800 bg-slate-900/70 p-7'><div className='mb-7 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-400/10 text-2xl text-emerald-300'>{item.icon}</div><h3 className='text-lg font-bold'>{item.title}</h3><p className='mt-3 leading-7 text-slate-400'>{item.text}</p></article>)}
          </div>
        </section>

        <section id='planes' className='scroll-mt-24 border-y border-white/5 bg-slate-900/30 px-5 py-24 sm:px-8'>
          <div className='mx-auto max-w-6xl'>
            <p className='text-center text-sm font-bold uppercase tracking-[0.2em] text-emerald-400'>Planes de demostración</p>
            <h2 className='mt-3 text-center text-3xl font-bold sm:text-4xl'>Un precio claro. Por ahora, ficticio.</h2>
            <p className='mx-auto mt-4 max-w-xl text-center text-slate-400'>Elige tu plan para recorrer la experiencia de contratación. No se realizará ningún pago ni renovación automática.</p>
            <div className='mx-auto mt-12 grid max-w-4xl gap-6 md:grid-cols-2'>
              {plans.map((plan,index)=><article key={plan.code} className={`rounded-2xl border p-8 ${index===1?'border-emerald-500/60 bg-emerald-400/5':'border-slate-700 bg-slate-900'}`}>
                {index===1 && <span className='mb-5 inline-block rounded-full bg-emerald-400 px-3 py-1 text-xs font-bold text-slate-950'>Plan destacado</span>}
                <h3 className='text-2xl font-bold'>{plan.name}</h3><p className='mt-2 text-sm text-slate-400'>{plan.subtitle}</p>
                <div className='my-8 flex items-baseline gap-2'><strong className='text-5xl font-extrabold'>{plan.price} €</strong><span className='text-slate-400'>/ mes *</span></div>
                <ul className='mb-9 space-y-4 text-sm text-slate-200'>{plan.features.map(feature=><li key={feature} className='flex gap-3'><span className='text-emerald-400'>✓</span>{feature}</li>)}</ul>
                <Link to={`/register?plan=${plan.code}`} className={`block rounded-xl px-5 py-3 text-center font-bold transition ${index===1?'bg-emerald-400 text-slate-950 hover:bg-emerald-300':'border border-slate-600 bg-slate-800 hover:bg-slate-700'}`}>Elegir {plan.name}</Link>
              </article>)}
            </div>
            <p className='mt-7 text-center text-xs text-slate-400'>* Importes meramente ilustrativos. No constituyen una oferta comercial ni se aplican cargos.</p>
          </div>
        </section>

        <section id='preguntas' className='scroll-mt-24 mx-auto max-w-4xl px-5 py-20 sm:px-8'>
          <h2 className='mb-9 text-3xl font-bold'>Preguntas frecuentes</h2>
          <div className='space-y-6'>
            <div><h3 className='font-semibold'>¿Se me cobrará la suscripción?</h3><p className='mt-2 text-slate-400'>No. Tanto los importes como la contratación son de demostración. No solicitamos datos de tarjeta.</p></div>
            <div><h3 className='font-semibold'>¿Puedo emitir facturas legalmente con esta versión?</h3><p className='mt-2 text-slate-400'>No debe utilizarse como sistema de facturación real conforme a VERI*FACTU. La integración normativa y la generación de documentos fiscales siguen pendientes.</p></div>
            <div><h3 className='font-semibold'>¿Qué ocurre cuando caduca mi sesión?</h3><p className='mt-2 text-slate-400'>Te pediremos iniciar sesión de nuevo. Tus datos guardados permanecen en la base de datos.</p></div>
          </div>
        </section>
      </main>

      <footer className='border-t border-white/10 px-5 py-8 text-sm text-slate-400 sm:px-8'><div className='mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3'><span className='font-bold text-white'>Veri<span className='text-emerald-400'>Factu.</span> <span className='ml-2 font-normal text-slate-400'>Prototipo de gestión comercial</span></span><span>Demostración sin cargos · Proyecto en desarrollo</span></div></footer>
    </div>
  );
}
