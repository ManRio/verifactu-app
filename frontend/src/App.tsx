import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import LoginPage from './pages/LoginPage'
import ProductsPage from './pages/ProductsPage'
import CustomerPage from './pages/CustomerPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path='/customers' element={<CustomerPage />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App