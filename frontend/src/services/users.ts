import { API_URL, apiFetch, readApiError } from '../lib/api';
import { getToken } from '../lib/session';

export type BusinessUser = {
  id: number;
  business_id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  role: 'SUPERUSER' | 'WORKER';
  email_verified: boolean;
  created_at: string;
};

function authHeaders(json = false): HeadersInit {
  return {
    Authorization: `Bearer ${getToken() ?? ''}`,
    ...(json ? { 'Content-Type': 'application/json' } : {}),
  };
}
export async function listWorkers(): Promise<BusinessUser[]> {
  const response = await apiFetch(`${API_URL}/users`, { headers: authHeaders() });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudieron consultar los usuarios'));
  return response.json();
}
export async function inviteWorker(payload: { email: string; full_name: string }): Promise<BusinessUser> {
  const response = await apiFetch(`${API_URL}/users`, {
    method: 'POST', headers: authHeaders(true), body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudo enviar la invitación'));
  return response.json();
}


export async function setWorkerActive(userId: number, isActive: boolean): Promise<BusinessUser> {
  const response = await apiFetch(`${API_URL}/users/${userId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken() ?? ''}` },
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!response.ok) throw new Error(await readApiError(response, 'No se pudo cambiar el estado del trabajador'));
  return response.json();
}
