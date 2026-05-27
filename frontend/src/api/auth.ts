import request from '@/utils/request'
import type { LoginResponse, R, UserProfile } from '@/types'

export interface LoginPayload {
  username: string
  password: string
}

export function login(payload: LoginPayload) {
  return request.post<R<LoginResponse>>('/auth/login', payload)
}

export function getCurrentUser() {
  return request.get<R<UserProfile>>('/auth/me')
}
