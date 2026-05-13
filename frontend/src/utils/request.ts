import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.response.use(
  (response) => {
    const payload: unknown = response.data
    if (isBusinessResponse(payload) && payload.code !== 200) {
      return Promise.reject(new Error(payload.message || `请求失败，业务状态码：${payload.code}`))
    }

    return response
  },
  (error) => {
    const message = extractBusinessMessage(error.response?.data) || error.message || '网络错误'
    return Promise.reject(new Error(message))
  },
)

function isBusinessResponse(value: unknown): value is { code: number; message?: string } {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return false
  }

  const candidate = value as Record<string, unknown>
  return typeof candidate.code === 'number'
    && (typeof candidate.message === 'string' || typeof candidate.message === 'undefined')
}

function extractBusinessMessage(value: unknown): string {
  return isBusinessResponse(value) ? value.message || '' : ''
}

export default request
