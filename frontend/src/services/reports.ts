import { API_URL, apiFetch, readApiError } from '../lib/api';
import { getToken } from '../lib/session';

export type TopProduct = { product_id: number; name: string; units: string; total_amount: string };
export type MonthTrend = { month: string; invoiced: string; received: string };
export type AccountingSummary = {
  period: string;
  issued_invoice_count: number;
  total_invoiced: string;
  cash_received_month: string;
  paid_for_month_invoices: string;
  outstanding_month_invoices: string;
  total_outstanding: string;
  cash_gap: string;
  collection_rate: string;
  top_products: TopProduct[];
  trend: MonthTrend[];
  scope: 'DEMO';
  disclaimer: string;
};

export async function getAccountingSummary(month: string): Promise<AccountingSummary> {
  const response = await apiFetch(`${API_URL}/reports/summary?month=${encodeURIComponent(month)}`, {
    headers: { Authorization: `Bearer ${getToken() ?? ''}` },
  });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudo cargar el resumen'));
  return response.json();
}
