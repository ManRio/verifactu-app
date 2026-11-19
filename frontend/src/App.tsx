import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom';

import DashboardLayout from './components/DashboardLayout';

import LoginPage from './pages/LoginPage';
import ProductsPage from './pages/ProductsPage';
import CustomerPage from './pages/CustomerPage';
import OrdersPage from './pages/OrdersPage';
import DeliveryNotesPage from './pages/DeliveryNotesPage';

// Comprueba que exista un token de sesión.
function ProtectedRoute() {
  const token = localStorage.getItem('access_token');

  if (!token) {
    return <Navigate to='/login' replace />;
  }

  return <Outlet />;
}

// Pantalla informativa mientras desarrollamos Facturas.
function InvoicesPendingPage() {
  return (
    <main className='min-h-screen bg-slate-950 px-6 py-12 text-white'>
      <div className='mx-auto max-w-3xl rounded-2xl border border-slate-800 bg-slate-900 p-8'>
        <span className='rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-300'>
          En desarrollo
        </span>

        <h1 className='mt-6 text-3xl font-bold'>Facturas</h1>

        <p className='mt-4 leading-7 text-slate-400'>
          El backend de facturación ya cuenta con funcionalidades implementadas.
          La interfaz de usuario para gestionar facturas todavía está pendiente
          de desarrollo.
        </p>

        <p className='mt-4 text-sm text-slate-500'>
          Puedes continuar trabajando con productos, clientes, pedidos y
          albaranes desde el menú.
        </p>
      </div>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Acceso público */}
        <Route path='/login' element={<LoginPage />} />

        {/* Rutas que requieren sesión */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path='/products' element={<ProductsPage />} />

            <Route path='/customers' element={<CustomerPage />} />

            <Route path='/orders' element={<OrdersPage />} />

            <Route path='/delivery-notes' element={<DeliveryNotesPage />} />

            <Route path='/invoices' element={<InvoicesPendingPage />} />
          </Route>
        </Route>

        {/* Ruta principal */}
        <Route path='/' element={<Navigate to='/products' replace />} />

        {/* URLs desconocidas */}
        <Route path='*' element={<Navigate to='/products' replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
