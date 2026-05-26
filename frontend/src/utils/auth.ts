import type { UserProfile, UserRole } from '@/types'

const AUTH_KEY = 'smartwater-auth-token'
const AUTH_USER_KEY = 'smartwater-auth-user'

export function getAuthToken(): string {
  if (typeof localStorage === 'undefined') return ''
  return localStorage.getItem(AUTH_KEY) || ''
}

export function setAuthToken(token: string): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(AUTH_KEY, token)
}

export function clearAuthToken(): void {
  if (typeof localStorage === 'undefined') return
  localStorage.removeItem(AUTH_KEY)
}

export function isAuthenticated(): boolean {
  return Boolean(getAuthToken())
}

export function setCurrentUser(user: UserProfile): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
}

export function getCurrentUser(): UserProfile | null {
  if (typeof localStorage === 'undefined') return null
  const value = localStorage.getItem(AUTH_USER_KEY)
  if (!value) return null
  try {
    return JSON.parse(value) as UserProfile
  } catch {
    return null
  }
}

export function clearCurrentUser(): void {
  if (typeof localStorage === 'undefined') return
  localStorage.removeItem(AUTH_USER_KEY)
}

export function clearAuthState(): void {
  clearAuthToken()
  clearCurrentUser()
}

export function getCurrentRole(): UserRole | null {
  return getCurrentUser()?.role ?? null
}
