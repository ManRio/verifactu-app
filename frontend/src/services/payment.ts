import { API_URL, apiFetch, readApiError } from '../lib/api';
import type { CreatePaymentData, InvoiceBalance, InvoicePayments, Payment } from '../types/payment';

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token ?? ''}`,
  };
}

export async function getPaymentBalances(): Promise<InvoiceBalance[]> {
  const response = await apiFetch(`${API_URL}/payments`, { headers: authHeaders() });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudieron cargar los saldos'));
  return response.json();
}

export async function getInvoicePayments(invoiceId: number): Promise<InvoicePayments> {
  const response = await apiFetch(`${API_URL}/payments/invoices/${invoiceId}`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudieron cargar los cobros'));
  return response.json();
}

export async function registerPayment(data: CreatePaymentData): Promise<Payment> {
  const response = await apiFetch(`${API_URL}/payments`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudo registrar el cobro'));
  return response.json();
}

export async function voidPayment(paymentId: number, reason: string): Promise<Payment> {
  const response = await apiFetch(`${API_URL}/payments/${paymentId}/void`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudo anular el registro'));
  return response.json();
}
