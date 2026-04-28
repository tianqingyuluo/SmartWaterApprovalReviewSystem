import request from '@/utils/request'
import type { R, SubmitResponse, ReviewTask } from '@/types'

export function submitTask(formData: FormData) {
  return request.post<R<SubmitResponse>>('/task/submit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getTask(taskId: string, sessionId: string) {
  return request.get<R<ReviewTask>>(`/task/${taskId}`, {
    params: { sessionId },
  })
}
