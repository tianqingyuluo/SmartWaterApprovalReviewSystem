const AUTH_KEY = 'smartwater-auth-token'

export function getAuthToken(): string {
  return localStorage.getItem(AUTH_KEY) || ''
}

export function setAuthToken(token: string): void {
  localStorage.setItem(AUTH_KEY, token)
}

export function clearAuthToken(): void {
  localStorage.removeItem(AUTH_KEY)
}

export function isAuthenticated(): boolean {
  return Boolean(getAuthToken())
}
