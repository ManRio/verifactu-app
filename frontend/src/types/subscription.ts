export type DemoPlan = {
  code: 'STARTER' | 'PRO';
  name: string;
  monthly_price_eur: string;
  features: string[];
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
};
