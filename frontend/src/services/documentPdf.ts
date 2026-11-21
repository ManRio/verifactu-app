/** Descarga protegida de PDFs de demostración (sin exponer el JWT en una URL). */

export type DocumentPdfKind = 'order' | 'delivery-note' | 'invoice';

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');

const paths: Record<DocumentPdfKind, string> = {
  order: 'orders',
  'delivery-note': 'delivery-notes',
  invoice: 'invoices',
};

const names: Record<DocumentPdfKind, string> = {
  order: 'pedido',
  'delivery-note': 'albaran',
  invoice: 'factura',
};

async function errorFromApi(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === 'object' && body !== null && 'detail' in body) {
      const detail = body.detail;
      if (typeof detail === 'string') return detail;
    }
  } catch {
    // La respuesta no incluye JSON.
  }
  return `No se pudo generar el PDF (HTTP ${response.status}).`;
}

export async function downloadDocumentPdf(kind: DocumentPdfKind, id: number): Promise<void> {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.assign('/login');
    throw new Error('Tu sesión ha terminado. Inicia sesión de nuevo.');
  }
  if (!Number.isSafeInteger(id) || id <= 0) {
    throw new Error('Identificador de documento no válido.');
  }

  const response = await fetch(`${API_URL}/${paths[kind]}/${id}/pdf`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (response.status === 401) {
    localStorage.removeItem('access_token');
    window.location.assign('/login?expired=1');
    throw new Error('Tu sesión ha caducado.');
  }
  if (!response.ok) throw new Error(await errorFromApi(response));

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/pdf')) {
    throw new Error('El servidor no devolvió un documento PDF válido.');
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement('a');
    link.href = url;
    link.download = `${names[kind]}-${id}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  } finally {
    // Permite al navegador completar la descarga antes de revocar la URL.
    window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
  }
}
