import type { Order, OrderLineInput } from '../types/order';

const API_URL = 'http://127.0.0.1:8000';

export type CreateOrderData = {
  customer_id: number;
  notes: string | null;
  lines: OrderLineInput[];
};

export type UpdateOrderData = {
  customer_id?: number;
  notes?: string | null;
  lines?: OrderLineInput[];
};

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');

  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data = await response.json();

    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof data.detail === 'string'
    ) {
      return data.detail;
    }
  } catch {
    // La respuesta no contiene JSON utilizable.
  }

  return fallback;
}

export async function getOrders(): Promise<Order[]> {
  const response = await fetch(`${API_URL}/orders`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('No se pudieron cargar los pedidos');
  }

  return response.json();
}

export async function getOrder(
  orderId: number,
): Promise<Order> {
  const response = await fetch(
    `${API_URL}/orders/${orderId}`,
    {
      headers: getAuthHeaders(),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'No se pudo cargar el pedido',
      ),
    );
  }

  return response.json();
}

export async function createOrder(
  data: CreateOrderData,
): Promise<Order> {
  const response = await fetch(`${API_URL}/orders`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'No se pudo crear el pedido',
      ),
    );
  }

  return response.json();
}

export async function updateOrder(
  orderId: number,
  data: UpdateOrderData,
): Promise<Order> {
  const response = await fetch(
    `${API_URL}/orders/${orderId}`,
    {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'No se pudo actualizar el pedido',
      ),
    );
  }

  return response.json();
}

export async function confirmOrder(
  orderId: number,
): Promise<Order> {
  const response = await fetch(
    `${API_URL}/orders/${orderId}/confirm`,
    {
      method: 'PATCH',
      headers: getAuthHeaders(),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'No se pudo confirmar el pedido',
      ),
    );
  }

  return response.json();
}

export async function cancelOrder(
  orderId: number,
): Promise<Order> {
  const response = await fetch(
    `${API_URL}/orders/${orderId}/cancel`,
    {
      method: 'PATCH',
      headers: getAuthHeaders(),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'No se pudo cancelar el pedido',
      ),
    );
  }

  return response.json();
}