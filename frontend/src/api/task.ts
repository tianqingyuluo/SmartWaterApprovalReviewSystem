import request from '@/utils/request'
import type {
  R,
  SubmitResponse,
  TaskStatusResponse,
  ApplicantResultResponse,
  ReviewerResultResponse,
  TaskListResponse,
  ApplicantResultView,
  ReviewerResultView,
  FailureCategory,
  ApplicantIssueDto,
  ReviewerIssueDto,
  RiskHintDto,
  Finding,
  ResultSummary,
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

export function getTaskList(page = 1, size = 20) {
  return request.get<R<TaskListResponse>>('/task/list', {
    params: { page, size },
  })
}

// ── Adapters: backend DTO → page view model ──

export function toApplicantResultView(dto: ApplicantResultResponse): ApplicantResultView {
  return {
    status: dto.status,
    missingMaterials: dto.missingMaterials,
    fieldIssues: dto.issues.map(toApplicantFinding),
    suggestions: buildApplicantSuggestions(dto),
  }
}

export function toReviewerResultView(
  statusDto: TaskStatusResponse,
  resultDto: ReviewerResultResponse,
): ReviewerResultView {
  const { failureCategory, failureReason } = extractFailureInfo(resultDto)
  const hasBlocker = resultDto.issues.some((f) => f.severity === 'BLOCKER')
  const manualReviewNotice = resultDto.manualReviewNotice ?? ''

  return {
    status: resultDto.status,
    materials: statusDto.materials,
    summary: summarizeIssues(resultDto.issues),
    extractedFields: normalizeExtractedFields(resultDto.extractedFields),
    fieldConfidence: null,
    materialSummaries: {},
    findings: resultDto.issues.map(toReviewerFinding),
    riskHints: resultDto.riskHints.map(formatRiskHint),
    draftOpinion: resultDto.draftOpinion,
    manualReviewNotice,
    failureCategory,
    failureReason,
    requiresManualReview: failureCategory !== null || hasBlocker || manualReviewNotice !== '',
  }
}

function extractFailureInfo(resultDto: ReviewerResultResponse): { failureCategory: FailureCategory; failureReason: string | null } {
  const issueCategory = resultDto.issues
    .map((issue) => toFailureCategory(issue.code))
    .find((category): category is NonNullable<FailureCategory> => category !== null)
  if (issueCategory) {
    return { failureCategory: issueCategory, failureReason: resultDto.summary || null }
  }

  const meta = resultDto.modelMetadata
  if (meta) {
    const matched = FAILURE_CATEGORIES.find((category) => meta.includes(category))
    if (matched) {
      return { failureCategory: matched, failureReason: resultDto.summary || null }
    }
  }

  if (resultDto.status !== 'FAILED') {
    return { failureCategory: null, failureReason: null }
  }

  return { failureCategory: 'SYSTEM_ERROR', failureReason: resultDto.summary || null }
}

const FAILURE_CATEGORIES: NonNullable<FailureCategory>[] = [
  'SYSTEM_ERROR',
  'AUTH_ERROR',
  'RATE_LIMIT',
  'TIMEOUT',
  'UPSTREAM_5XX',
  'INVALID_JSON',
  'SCHEMA_MISMATCH',
  'CONTENT_FILTERED',
]

function toFailureCategory(code: string): FailureCategory {
  return FAILURE_CATEGORIES.includes(code as NonNullable<FailureCategory>)
    ? code as NonNullable<FailureCategory>
    : null
}

function toApplicantFinding(issue: ApplicantIssueDto): Finding {
  return {
    findingType: issue.code,
    severity: issue.severity,
    audience: 'APPLICANT',
    description: issue.message,
    basis: null,
  }
}

function toReviewerFinding(issue: ReviewerIssueDto): Finding {
  return {
    findingType: issue.code,
    severity: issue.severity,
    audience: issue.applicantVisible ? 'APPLICANT' : 'REVIEWER',
    description: issue.message,
    basis: issue.basisRefs?.join('、') ?? null,
  }
}

function formatRiskHint(hint: RiskHintDto): string {
  const basisText = hint.basisRefs?.length ? ` 依据: ${hint.basisRefs.join('、')}` : ''
  const manualText = hint.requiresManualReview ? ' 需人工复核。' : ''
  return `[${hint.riskLevel}] ${hint.description}${basisText}${manualText}`
}

function summarizeIssues(issues: Array<{ severity: string }>): ResultSummary {
  return {
    totalFindings: issues.length,
    blockerCount: issues.filter((f) => f.severity === 'BLOCKER').length,
    warningCount: issues.filter((f) => f.severity === 'WARNING').length,
    infoCount: issues.filter((f) => f.severity === 'INFO').length,
  }
}

function normalizeExtractedFields(value: unknown): Record<string, string> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, fieldValue]) => [key, String(fieldValue ?? '')]),
  )
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
