import { API_URL, apiFetch, readApiError } from '../lib/api';
import { getToken } from '../lib/session';
import type { DemoPlan, DemoSubscription } from '../types/subscription';

function headers() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken() ?? ''}`,
  };
}

export async function getPlans(): Promise<DemoPlan[]> {
  const response = await fetch(`${API_URL}/subscriptions/plans`);
  if (!response.ok) throw new Error('No se pudieron obtener los planes');
  return response.json();
}

export async function getMySubscription(): Promise<DemoSubscription | null> {
  const response = await apiFetch(`${API_URL}/subscriptions/me`, {
    headers: headers(),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response, 'No se pudo consultar la suscripción'));
  }
  return response.json();
}

export async function activateDemoPlan(planCode: DemoPlan['code']): Promise<DemoSubscription> {
  const response = await apiFetch(`${API_URL}/subscriptions/demo-checkout`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ plan_code: planCode }),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response, 'No se pudo activar el plan de demostración'));
  }
  return response.json();
}
