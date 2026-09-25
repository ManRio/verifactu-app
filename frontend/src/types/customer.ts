export type Customer = {
  id: number;
  business_id: number;
  tax_id: string | null;
  legal_name: string;
  trade_name: string | null;
  address: string | null;
  postal_code: string | null;
  city: string | null;
  province: string | null;
  country_code: string;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
