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
import OrderDetailPage from './pages/OrderDetailPage';
import DeliveryNotesPage from './pages/DeliveryNotesPage';
import DeliveryNoteDetailPage from './pages/DeliveryNoteDetailPage';
import InvoicesPage from './pages/InvoicesPage';
import InvoiceDetailPage from './pages/InvoiceDetailPage';

// Comprueba que exista un token de sesión.
function ProtectedRoute() {
  const token = localStorage.getItem('access_token');

  if (!token) {
    return <Navigate to='/login' replace />;
  }

  return <Outlet />;
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
            <Route path='/orders/:orderId' element={<OrderDetailPage />} />

            <Route path='/delivery-notes' element={<DeliveryNotesPage />} />
            <Route path='/delivery-notes/:deliveryNoteId' element={<DeliveryNoteDetailPage />} />

            <Route path='/invoices' element={<InvoicesPage />} />
            <Route path='/invoices/:invoiceId' element={<InvoiceDetailPage />} />
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
