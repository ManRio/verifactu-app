import type {
  DeliveryNote,
  DeliveryNoteLineInput,
} from '../types/deliveryNote';

const API_URL = 'http://127.0.0.1:8000';

export type CreateDeliveryNoteData = {
  order_id: number;
  delivery_date: string;
  notes: string | null;
  lines: DeliveryNoteLineInput[];
};

export type UpdateDeliveryNoteData = {
  delivery_date?: string;
  notes?: string | null;
  lines?: DeliveryNoteLineInput[];
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

export async function getDeliveryNotes(): Promise<DeliveryNote[]> {
  const response = await fetch(`${API_URL}/delivery-notes`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('No se pudieron cargar los albaranes');
  }

  return response.json();
}

export async function getDeliveryNote(
  deliveryNoteId: number,
): Promise<DeliveryNote> {
  const response = await fetch(`${API_URL}/delivery-notes/${deliveryNoteId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo cargar el albarán'),
    );
  }

  return response.json();
}

export async function createDeliveryNote(
  data: CreateDeliveryNoteData,
): Promise<DeliveryNote> {
  const response = await fetch(`${API_URL}/delivery-notes`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo crear el albarán'),
    );
  }

  return response.json();
}

export async function updateDeliveryNote(
  deliveryNoteId: number,
  data: UpdateDeliveryNoteData,
): Promise<DeliveryNote> {
  const response = await fetch(`${API_URL}/delivery-notes/${deliveryNoteId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo actualizar el albarán'),
    );
  }

  return response.json();
}

export async function confirmDeliveryNote(
  deliveryNoteId: number,
): Promise<DeliveryNote> {
  const response = await fetch(
    `${API_URL}/delivery-notes/${deliveryNoteId}/confirm`,
    {
      method: 'PATCH',
      headers: getAuthHeaders(),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo confirmar el albarán'),
    );
  }

  return response.json();
}

export async function cancelDeliveryNote(
  deliveryNoteId: number,
): Promise<DeliveryNote> {
  const response = await fetch(
    `${API_URL}/delivery-notes/${deliveryNoteId}/cancel`,
    {
      method: 'PATCH',
      headers: getAuthHeaders(),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo cancelar el albarán'),
    );
  }

  return response.json();
}
