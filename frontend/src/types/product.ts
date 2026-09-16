export type Product = {
  id: number;
  business_id: number;
  name: string;
  sku: string | null;
  description: string | null;
  unit_price: string;
  tax_rate: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
