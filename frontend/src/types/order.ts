export type OrderStatus = 'DRAFT' | 'CONFIRMED' | 'CANCELLED';

export type OrderLine = {
  id: number;
  order_id: number;
  product_id: number;
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

export type Order = {
  id: number;
  business_id: number;
  customer_id: number;
  status: OrderStatus;
  notes: string | null;
  subtotal: string;
  tax_total: string;
  total_amount: string;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  lines: OrderLine[];
};

export type OrderLineInput = {
  product_id: number;
  quantity: string;
  position: number;
};
