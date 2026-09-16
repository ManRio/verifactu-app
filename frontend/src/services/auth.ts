import type { LoginRequest, TokenResponse } from '../types/auth'

const API_URL = 'http://localhost:8000'

export async function login(
  credentials: LoginRequest,
): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  })

  if (!response.ok) {
    throw new Error('Credenciales incorrectas')
  }

  return response.json()
}