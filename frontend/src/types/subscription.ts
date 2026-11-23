export type DemoPlan = {
  code: 'STARTER' | 'PRO' | 'BUSINESS';
  name: string;
  monthly_price_eur: string;
  features: string[];
  max_workers: number;
};

export type DemoSubscription = {
  status: 'PENDING' | 'DEMO_ACTIVE' | 'DEMO_EXPIRED';
  plan_code: string | null;
  plan_name: string | null;
  monthly_price_eur: string | null;
  activated_at: string | null;
  period_end: string | null;
  is_demo: true;
  payment_collected: false;
  max_workers: number;
  active_workers: number;
  available_workers: number;
};
