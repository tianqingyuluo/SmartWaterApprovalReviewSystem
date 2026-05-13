import { describe, expect, it } from 'vitest'
import request from './request'

describe('request client', () => {
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
})
