import { afterEach, describe, expect, it, vi } from 'vitest'
import request from './request'
import * as auth from './auth'

describe('request client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('injects bearer token into request headers', async () => {
    vi.spyOn(auth, 'getAuthToken').mockReturnValue('token-123')

    const response = await request.get('/task/list', {
      adapter: async (config) => ({
        data: { code: 200, message: 'success', data: null },
        status: 200,
        statusText: 'OK',
        headers: config.headers,
        config,
        request: {},
      }),
    })

    expect((response.config.headers as Record<string, string>).Authorization).toBe('Bearer token-123')
  })

  it('rejects Java R payloads with non-success business code', async () => {
    const businessError = { code: 403, message: '无权访问该任务', data: null }

    await expect(
      request.get('/task/task-1/status', {
        adapter: async (config) => ({
          data: businessError,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          request: {},
        }),
      }),
    ).rejects.toThrow('无权访问该任务')
  })

  it('clears stale auth state when Java R payload returns 401', async () => {
    const clearAuthState = vi.spyOn(auth, 'clearAuthState').mockImplementation(() => {})
    const businessError = { code: 401, message: '未登录或登录已过期', data: null }

    await expect(
      request.get('/task/list', {
        adapter: async (config) => ({
          data: businessError,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          request: {},
        }),
      }),
    ).rejects.toThrow('未登录或登录已过期')

    expect(clearAuthState).toHaveBeenCalled()
  })
})
