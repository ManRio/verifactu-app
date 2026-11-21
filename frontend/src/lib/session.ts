const TOKEN_KEY = 'access_token';
const NOTICE_KEY = 'auth_notice';
export const SESSION_EVENT = 'verifactu:session-ended';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveSession(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  sessionStorage.removeItem(NOTICE_KEY);
}

/** La comprobación local sirve solo a la UX; la validez la determina FastAPI. */
export function tokenExpired(token: string): boolean {
  try {
    const payloadPart = token.split('.')[1];
    if (!payloadPart) return true;
    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    const decoded: unknown = JSON.parse(atob(base64));
    if (typeof decoded !== 'object' || decoded === null || !('exp' in decoded)) {
      return true;
    }
    const expires = decoded.exp;
    return typeof expires !== 'number' || Date.now() >= expires * 1000;
  } catch {
    return true;
  }
}

export function endSession(message?: string) {
  localStorage.removeItem(TOKEN_KEY);
  if (message) sessionStorage.setItem(NOTICE_KEY, message);
  else sessionStorage.removeItem(NOTICE_KEY);
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function consumeSessionNotice(): string | null {
  const notice = sessionStorage.getItem(NOTICE_KEY);
  sessionStorage.removeItem(NOTICE_KEY);
  return notice;
}
