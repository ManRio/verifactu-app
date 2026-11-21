import { API_URL, apiFetch, readApiError } from '../lib/api';
import { getToken } from '../lib/session';
import type { LoginRequest, TokenResponse } from '../types/auth';

export type RegistrationRequest = {
  business: {
    legal_name: string;
    tax_id: string;
    trade_name: string | null;
    address: string;
    postal_code: string;
    city: string;
    province: string;
    country_code: 'ES';
  };
  user: {
    email: string;
    password: string;
    full_name: string;
  };
};

export type AuthenticatedUser = {
  id: number;
  business_id: number;
  email: string;
  full_name: string;
  is_active: boolean;
};

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response, 'No se pudo iniciar sesión'));
  }
  return response.json();
}

export async function registerBusiness(data: RegistrationRequest): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response, 'No se pudo registrar el negocio'));
  }
  return response.json();
}

export async function getMe(): Promise<AuthenticatedUser> {
  const response = await apiFetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${getToken() ?? ''}` },
  });
  if (!response.ok) {
    throw new Error(await readApiError(response, 'No se pudo validar la sesión'));
  }
  return response.json();
}
