export type InvoiceStatus = 'DRAFT' | 'ISSUED';

export type InvoiceLine = {
  id: number;
  invoice_id: number;
  delivery_note_line_id: number;
  order_line_id: number;

  description: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;

  base_amount: string;
  tax_amount: string;
  total_amount: string;

  position: number;
  created_at: string;
};

export type InvoiceDeliveryNote = {
  id: number;
  invoice_id: number;
  delivery_note_id: number;
  created_at: string;
};

export type Invoice = {
  id: number;
  business_id: number;
  customer_id: number;

  status: InvoiceStatus;
  invoice_type: string;

  series: string | null;
  number: number | null;
  full_number: string | null;

  issue_date: string | null;
  operation_date: string | null;

  // Datos históricos del emisor
  issuer_legal_name: string;
  issuer_tax_id: string;
  issuer_address: string;
  issuer_postal_code: string;
  issuer_city: string;
  issuer_province: string;
  issuer_country_code: string;

  // Datos históricos del cliente
  customer_legal_name: string;
  customer_tax_id: string | null;
  customer_address: string | null;
  customer_postal_code: string | null;
  customer_city: string | null;
  customer_province: string | null;
  customer_country_code: string;

  // Importes calculados por el backend
  subtotal: string;
  tax_total: string;
  total_amount: string;

  notes: string | null;

  created_at: string;
  updated_at: string;
  issued_at: string | null;

  lines: InvoiceLine[];
  delivery_notes: InvoiceDeliveryNote[];
};

// Datos necesarios para crear una factura
export type CreateInvoiceData = {
  delivery_note_ids: number[];
  operation_date?: string | null;
  notes?: string | null;
};

// Solo pueden modificarse borradores
export type UpdateInvoiceData = {
  delivery_note_ids?: number[];
  operation_date?: string | null;
  notes?: string | null;
};

// Datos necesarios para emitir una factura
export type IssueInvoiceData = {
  series_code: string;
  issue_date: string;
};
