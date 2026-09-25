import type { Customer } from '../types/customer';

const API_URL = 'http://127.0.0.1:8000';

export type CreateCustomerData = {
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
};

export type UpdateCustomerData = {
  tax_id?: string | null;
  legal_name?: string;
  trade_name?: string | null;
  address?: string | null;
  postal_code?: string | null;
  city?: string | null;
  province?: string | null;
  country_code?: string;
  email?: string | null;
  phone?: string | null;
};

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');

  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function getCustomers(): Promise<Customer[]> {
  const response = await fetch(`${API_URL}/customers`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('No se pudieron cargar los clientes');
  }

  return response.json();
}

export async function createCustomer(
  data: CreateCustomerData,
): Promise<Customer> {
  const response = await fetch(`${API_URL}/customers`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (response.status === 409) {
    throw new Error('Ya existe un cliente con ese NIF/CIF');
  }

  if (!response.ok) {
    throw new Error('No se pudo crear el cliente');
  }

  return response.json();
}

export async function updateCustomer(
  customerId: number,
  data: UpdateCustomerData,
): Promise<Customer> {
  const response = await fetch(`${API_URL}/customers/${customerId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (response.status === 409) {
    throw new Error('Ya existe un cliente con ese NIF/CIF');
  }

  if (!response.ok) {
    throw new Error('No se pudo actualizar el cliente');
  }

  return response.json();
}

export async function activateCustomer(
  customerId: number,
): Promise<Customer> {
  const response = await fetch(`${API_URL}/customers/${customerId}/activate`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('No se pudo activar el cliente');
  }

  return response.json();
}

export async function deactivateCustomer(
  customerId: number,
): Promise<Customer> {
  const response = await fetch(`${API_URL}/customers/${customerId}/deactivate`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('No se pudo desactivar el cliente');
  }

  return response.json();
}