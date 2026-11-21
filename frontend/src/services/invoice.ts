import type {
  Invoice,
  CreateInvoiceData,
  UpdateInvoiceData,
  IssueInvoiceData,
} from '../types/invoice';

const API_URL = 'http://127.0.0.1:8000';

// Cabeceras de autenticación
function getAuthHeaders() {
  const token = localStorage.getItem('access_token');

  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

// Extrae los errores devueltos por FastAPI
async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data: unknown = await response.json();

    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof data.detail === 'string'
    ) {
      return data.detail;
    }
  } catch {
    // Respuesta sin JSON válido.
  }

  return fallback;
}

// Obtener todas las facturas de la empresa
export async function getInvoices(): Promise<Invoice[]> {
  const response = await fetch(`${API_URL}/invoices`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudieron cargar las facturas'),
    );
  }

  return response.json();
}

// Obtener una factura por ID
export async function getInvoice(invoiceId: number): Promise<Invoice> {
  const response = await fetch(`${API_URL}/invoices/${invoiceId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo cargar la factura'),
    );
  }

  return response.json();
}

// Crear una factura en estado DRAFT
export async function createInvoice(data: CreateInvoiceData): Promise<Invoice> {
  const response = await fetch(`${API_URL}/invoices`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo crear la factura'),
    );
  }

  return response.json();
}

// Actualizar una factura en estado DRAFT
export async function updateInvoice(
  invoiceId: number,
  data: UpdateInvoiceData,
): Promise<Invoice> {
  const response = await fetch(`${API_URL}/invoices/${invoiceId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo actualizar la factura'),
    );
  }

  return response.json();
}

// Emitir una factura y asignar numeración
export async function issueInvoice(
  invoiceId: number,
  data: IssueInvoiceData,
): Promise<Invoice> {
  const response = await fetch(`${API_URL}/invoices/${invoiceId}/issue`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo emitir la factura'),
    );
  }

  return response.json();
}
