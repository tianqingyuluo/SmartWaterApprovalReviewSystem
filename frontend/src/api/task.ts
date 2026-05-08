import request from '@/utils/request'
import type {
  R,
  SubmitResponse,
  TaskStatusResponse,
  ApplicantResultResponse,
  ReviewerResultResponse,
  ApplicantResultView,
  ReviewerResultView,
} from '@/types'

// ── API functions ──

export function submitTask(formData: FormData) {
  return request.post<R<SubmitResponse>>('/task/submit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getTaskStatus(taskId: string, sessionId: string) {
  return request.get<R<TaskStatusResponse>>(`/task/${taskId}/status`, {
    params: { sessionId },
  })
}

export function getApplicantResult(taskId: string, sessionId: string) {
  return request.get<R<ApplicantResultResponse>>(`/task/${taskId}/result/applicant`, {
    params: { sessionId },
  })
}

export function getReviewerResult(taskId: string, sessionId: string) {
  return request.get<R<ReviewerResultResponse>>(`/task/${taskId}/result/reviewer`, {
    params: { sessionId },
  })
}

// ── Adapters: backend DTO → page view model ──

export function toApplicantResultView(dto: ApplicantResultResponse): ApplicantResultView {
  return {
    status: dto.status,
    missingMaterials: dto.missingMaterials,
    fieldIssues: dto.issues,
    suggestions: buildApplicantSuggestions(dto),
  }
}

export function toReviewerResultView(
  statusDto: TaskStatusResponse,
  resultDto: ReviewerResultResponse,
): ReviewerResultView {
  return {
    status: resultDto.status,
    materials: statusDto.materials,
    summary: resultDto.summary,
    extractedFields: resultDto.extractedFields,
    fieldConfidence: resultDto.fieldConfidence ?? null,
    materialSummaries: resultDto.materialSummaries ?? {},
    findings: resultDto.issues,
    riskHints: resultDto.riskHints,
    draftOpinion: resultDto.draftOpinion,
    manualReviewNotice: resultDto.manualReviewNotice ?? '',
    failureCategory: resultDto.failureCategory ?? null,
    failureReason: resultDto.failureReason ?? null,
  }
}

function buildApplicantSuggestions(dto: ApplicantResultResponse): string[] {
  const suggestions: string[] = []

  if (dto.missingMaterials.length > 0) {
    suggestions.push('请补充缺失材料后重新提交，以获取完整的审核辅助结果。')
  }

  const blockerCount = dto.issues.filter((f) => f.severity === 'BLOCKER').length
  if (blockerCount > 0) {
    suggestions.push(`存在 ${blockerCount} 项阻断性问题，请在提交前修正。`)
  }

  if (dto.missingMaterials.length === 0 && blockerCount === 0) {
    suggestions.push('材料预检查已完成，审批人员将进行进一步审核。')
  }

  return suggestions
}
