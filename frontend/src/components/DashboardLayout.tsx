import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { endSession } from '../lib/session';

const navigation = [
  { label: 'Productos', path: '/products', icon: '▦' },
  { label: 'Clientes', path: '/customers', icon: '♙' },
  { label: 'Pedidos', path: '/orders', icon: '▤' },
  { label: 'Albaranes', path: '/delivery-notes', icon: '⇄' },
  { label: 'Facturas', path: '/invoices', icon: '▣' },
  { label: 'Cobros', path: '/payments', icon: '€' },
  { label: 'Mi plan demo', path: '/subscription', icon: '◇' },
];

function DashboardLayout() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    endSession();
    navigate('/login', { replace: true });
  }

  return (
    <div className='min-h-screen bg-slate-950 text-white'>
      <div className='lg:flex'>
        {/* Cabecera móvil */}
        <header className='sticky top-0 z-30 flex items-center justify-between border-b border-slate-800 bg-slate-900 px-5 py-4 lg:hidden'>
          <div>
            <p className='font-bold text-emerald-400'>VeriFactu App</p>
            <p className='text-xs text-slate-400'>Gestión comercial</p>
          </div>

          <button
            type='button'
            onClick={() => setMenuOpen(!menuOpen)}
            aria-expanded={menuOpen}
            aria-controls='dashboard-navigation'
            className='rounded-lg border border-slate-700 px-3 py-2 text-sm'
          >
            {menuOpen ? 'Cerrar' : 'Menú'}
          </button>
        </header>

        {/* Navegación lateral */}
        <aside
          id='dashboard-navigation'
          className={`border-r border-slate-800 bg-slate-900 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col ${
            menuOpen ? 'block' : 'hidden lg:flex'
          }`}
        >
          <div className='hidden border-b border-slate-800 px-6 py-7 lg:block'>
            <p className='text-xl font-bold tracking-tight'>
              VeriFactu<span className='text-emerald-400'>.</span>
            </p>
            <p className='mt-1 text-xs text-slate-400'>
              Panel de gestión comercial
            </p>
          </div>

          <nav
            aria-label='Navegación principal'
            className='flex-1 space-y-2 p-4'
          >
            <p className='px-3 pb-2 pt-3 text-xs font-semibold uppercase tracking-widest text-slate-500'>
              Gestión
            </p>

            {navigation.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/20'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <span aria-hidden='true' className='w-5 text-center text-lg'>
                  {item.icon}
                </span>
                {item.label}
              </NavLink>
            ))}

          </nav>

          <div className='border-t border-slate-800 p-4'>
            <div className='mb-4 rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-3'>
              <p className='text-sm font-medium text-white'>
                Entorno de desarrollo
              </p>
              <p className='mt-1 text-xs text-slate-400'>
                Aplicación en construcción
              </p>
            </div>

            <button
              type='button'
              onClick={handleLogout}
              className='w-full rounded-xl border border-slate-700 px-4 py-3 text-left text-sm font-medium text-slate-300 transition hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-300'
            >
              Cerrar sesión
            </button>
          </div>
        </aside>

        {/* Pantalla del módulo activo */}
        <div className='min-w-0 flex-1'>
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export default DashboardLayout;
