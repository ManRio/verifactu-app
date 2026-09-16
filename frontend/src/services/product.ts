import type { Product } from '../types/product';

const API_URL = 'http://127.0.0.1:8000';

export type CreateProductData = {
  name: string;
  sku: string | null;
  description: string | null;
  unit_price: string;
  tax_rate: string;
};

export type UpdateProductData = {
  name?: string;
  sku?: string | null;
  description?: string | null;
  unit_price?: string;
  tax_rate?: string;
};

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');

  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(`${API_URL}/products`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('No se pudieron cargar los productos');
  }

  return response.json();
}

export async function createProduct(data: CreateProductData): Promise<Product> {
  const response = await fetch(`${API_URL}/products`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (response.status === 409) {
    throw new Error('Ya existe un producto con ese SKU');
  }

  if (!response.ok) {
    throw new Error('No se pudo crear el producto');
  }

  return response.json();
}

export async function updateProduct(
  productId: number,
  data: UpdateProductData,
): Promise<Product> {
  const response = await fetch(`${API_URL}/products/${productId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (response.status === 409) {
    throw new Error('Ya existe un producto con ese SKU');
  }

  if (!response.ok) {
    throw new Error('No se pudo actualizar el producto');
  }

  return response.json();
}
