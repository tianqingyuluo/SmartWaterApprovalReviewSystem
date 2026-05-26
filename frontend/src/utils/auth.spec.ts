import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { clearAuthState, getCurrentRole, getCurrentUser, setAuthToken, setCurrentUser } from './auth'

describe('auth storage helpers', () => {
  beforeEach(() => {
    const store = new Map<string, string>()
    const localStorageMock = {
      get length() {
        return store.size
      },
      clear() {
        store.clear()
      },
      getItem(key: string) {
        return store.get(key) ?? null
      },
      key(index: number) {
        return Array.from(store.keys())[index] ?? null
      },
      removeItem(key: string) {
        store.delete(key)
      },
      setItem(key: string, value: string) {
        store.set(key, value)
      },
    } satisfies Storage

    vi.stubGlobal('localStorage', localStorageMock)
  })

  afterEach(() => {
    clearAuthState()
    vi.unstubAllGlobals()
  })

  it('returns a stored user only when the profile shape is valid', () => {
    setCurrentUser({
      userId: 1001,
      username: 'reviewer',
      displayName: '审批员',
      role: 'REVIEWER',
    })

    expect(getCurrentUser()).toMatchObject({
      userId: 1001,
      username: 'reviewer',
      role: 'REVIEWER',
    })
    expect(getCurrentRole()).toBe('REVIEWER')
  })

  it('does not guess a role from malformed localStorage user data', () => {
    localStorage.setItem('smartwater-auth-user', JSON.stringify({
      userId: 1001,
      username: 'reviewer',
      displayName: '审批员',
      role: 'AUDITOR',
    }))
    setAuthToken('token-123')

    expect(getCurrentUser()).toBeNull()
    expect(getCurrentRole()).toBeNull()
  })
})
