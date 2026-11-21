export type PaymentMethod = 'TRANSFER' | 'CASH' | 'CARD' | 'OTHER';
export type PaymentStatus = 'RECORDED' | 'VOIDED';
export type BalanceStatus = 'UNPAID' | 'PARTIAL' | 'PAID';

export type InvoiceBalance = {
  invoice_id: number;
  full_number: string;
  customer_legal_name: string;
  issue_date: string;
  total_amount: string;
  paid_amount: string;
  outstanding_amount: string;
  payment_status: BalanceStatus;
};

export type Payment = {
  id: number;
  business_id: number;
  invoice_id: number;
  amount: string;
  payment_date: string;
  method: PaymentMethod;
  reference: string | null;
  notes: string | null;
  status: PaymentStatus;
  created_by_user_id: number;
  voided_by_user_id: number | null;
  void_reason: string | null;
  created_at: string;
  voided_at: string | null;
};

export type InvoicePayments = {
  balance: InvoiceBalance;
  payments: Payment[];
};

export type CreatePaymentData = {
  invoice_id: number;
  amount: string;
  payment_date: string;
  method: PaymentMethod;
  reference: string | null;
  notes: string | null;
};
