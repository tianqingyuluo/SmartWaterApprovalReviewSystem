import axios from 'axios'
import { clearAuthState, getAuthToken } from '@/utils/auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.response.use(
  (response) => {
    const payload: unknown = response.data
    if (isBusinessResponse(payload) && payload.code !== 200) {
      if (payload.code === 401) {
        clearAuthState()
        redirectToLogin()
      }
      return Promise.reject(new Error(payload.message || `请求失败，业务状态码：${payload.code}`))
    }

    return response
  },
  (error) => {
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      clearAuthState()
      redirectToLogin()
    }
    const message = extractBusinessMessage(error.response?.data) || error.message || '网络错误'
    return Promise.reject(new Error(message))
  },
)

request.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

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

function redirectToLogin(): void {
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}

export default request
