import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import DashboardLayout from './components/DashboardLayout';
import SessionGuard from './components/SessionGuard';
import SubscriptionGate from './components/SubscriptionGate';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CheckoutPage from './pages/CheckoutPage';
import SubscriptionPage from './pages/SubscriptionPage';
import ProductsPage from './pages/ProductsPage';
import CustomerPage from './pages/CustomerPage';
import OrdersPage from './pages/OrdersPage';
import OrderDetailPage from './pages/OrderDetailPage';
import DeliveryNotesPage from './pages/DeliveryNotesPage';
import DeliveryNoteDetailPage from './pages/DeliveryNoteDetailPage';
import InvoicesPage from './pages/InvoicesPage';
import InvoiceDetailPage from './pages/InvoiceDetailPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path='/' element={<LandingPage />} />
        <Route path='/login' element={<LoginPage />} />
        <Route path='/register' element={<RegisterPage />} />

        <Route element={<SessionGuard />}>
          <Route path='/checkout' element={<CheckoutPage />} />
          <Route element={<SubscriptionGate />}>
            <Route element={<DashboardLayout />}>
              <Route path='/subscription' element={<SubscriptionPage />} />
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
        </Route>

        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
