import { endSession } from './session';

// Misma URL para todos los servicios; editable mediante VITE_API_URL.
export const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '');

/** Desconecta solo si el 401 corresponde al token que todavía está activo. */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const suppliedToken = new Headers(init?.headers)
    .get('Authorization')?.replace(/^Bearer\s+/i, '');

  const response = await fetch(input, init);
  if (
    response.status === 401 &&
    suppliedToken &&
    suppliedToken === localStorage.getItem('access_token')
  ) {
    endSession('Tu sesión ha caducado o ya no es válida. Inicia sesión de nuevo.');
  }
  if (response.status === 402 && suppliedToken) {
    // El acceso a la API requiere reactivar el plan de demostración.
    window.location.assign('/checkout');
  }
  return response;
}

export async function readApiError(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const data: unknown = await response.json();
    if (typeof data === 'object' && data !== null && 'detail' in data) {
      const detail = data.detail;
      if (typeof detail === 'string') return detail;
    }
  } catch {
    // API no devolvió JSON.
  }
  return fallback;
}
