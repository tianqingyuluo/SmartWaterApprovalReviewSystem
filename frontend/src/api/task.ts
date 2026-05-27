import request from '@/utils/request'
import type {
  R,
  SubmitResponse,
  TaskStatusResponse,
  ApplicantResultResponse,
  ReviewerResultResponse,
  TaskListResponse,
  ReviewerActionSubmitRequest,
  ReviewerActionResponse,
  ApplicantResultView,
  ReviewerResultView,
  TaskResultView,
  ReviewActionLogDto,
  ReviewActionLogView,
  HandlingStatus,
  FailureCategory,
  ApplicantIssueDto,
  ReviewerIssueDto,
  RiskHintDto,
  Finding,
  ResultSummary,
  MaterialPreviewItem,
  MaterialSlot,
} from '@/types'
import { REVIEWER_ACTION_LABELS } from '@/types'

// ── API functions ──

export function submitTask(formData: FormData) {
  return request.post<R<SubmitResponse>>('/task/submit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getTaskStatus(taskId: string, sessionId?: string | null) {
  return request.get<R<TaskStatusResponse>>(`/task/${taskId}/status`, {
    params: sessionId ? { sessionId } : undefined,
  })
}

export function getApplicantResult(taskId: string, sessionId?: string | null) {
  return request.get<R<ApplicantResultResponse>>(`/task/${taskId}/result/applicant`, {
    params: sessionId ? { sessionId } : undefined,
  })
}

export function getReviewerResult(taskId: string, sessionId?: string | null) {
  return request.get<R<ReviewerResultResponse>>(`/task/${taskId}/result/reviewer`, {
    params: sessionId ? { sessionId } : undefined,
  })
}

export function getTaskList(page = 1, size = 20) {
  return request.get<R<TaskListResponse>>('/task/list', {
    params: { page, size },
  })
}

export function submitReviewerAction(taskId: string, payload: ReviewerActionSubmitRequest) {
  return request.post<R<ReviewerActionResponse>>(`/task/${taskId}/reviewer-action`, payload)
}

export async function fetchMaterialPreviewBlob(previewPath: string) {
  const response = await request.get<Blob>(previewPath, {
    responseType: 'blob',
  })
  return response.data
}

// ── Adapters: backend DTO → page view model ──

export function toApplicantResultView(dto: ApplicantResultResponse): ApplicantResultView {
  return {
    status: dto.status,
    missingMaterials: dto.missingMaterials,
    fieldIssues: dto.issues.map(toApplicantFinding),
    suggestions: buildApplicantSuggestions(dto),
    handlingStatus: dto.handlingStatus ?? null,
    handlingStatusLabel: dto.handlingStatusLabel ?? '',
    reviewerRemark: dto.reviewerRemark ?? '',
    reviewerActionAt: dto.reviewerActionAt ?? null,
  }
}

export function toApplicantTaskResultView(
  statusDto: TaskStatusResponse,
  resultView: ApplicantResultView,
): TaskResultView {
  const summary = summarizeIssues(resultView.fieldIssues)

  return {
    viewMode: 'APPLICANT',
    status: resultView.status,
    handlingStatus: resultView.handlingStatus ?? statusDto.handlingStatus ?? null,
    handlingStatusLabel: resultView.handlingStatusLabel || statusDto.handlingStatusLabel || '',
    reviewerRemark: resultView.reviewerRemark || statusDto.reviewerRemark || '',
    reviewerActionCode: null,
    reviewerUserId: null,
    reviewerDisplayName: '',
    reviewerActionAt: resultView.reviewerActionAt,
    reviewActionLogs: [],
    materials: statusDto.materials,
    previewMaterials: statusDto.materials.map(toMaterialPreviewItem),
    summary,
    extractedFields: {},
    fieldConfidence: null,
    materialSummaries: {},
    findings: resultView.fieldIssues,
    riskHints: [],
    draftOpinion: '',
    manualReviewNotice: resultView.suggestions.join(' '),
    failureCategory: resultView.status === 'FAILED' ? 'SYSTEM_ERROR' : null,
    failureReason: resultView.status === 'FAILED'
      ? '暂无法生成结果，请检查材料文件是否可读，或重新提交新的任务。'
      : null,
    requiresManualReview:
      resultView.status === 'FAILED'
      || summary.blockerCount > 0
      || resultView.missingMaterials.length > 0,
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
    handlingStatus: resultDto.handlingStatus ?? statusDto.handlingStatus ?? null,
    handlingStatusLabel: resultDto.handlingStatusLabel ?? statusDto.handlingStatusLabel ?? '',
    reviewerRemark: resultDto.reviewerRemark ?? statusDto.reviewerRemark ?? '',
    reviewerActionCode: resultDto.reviewerActionCode ?? null,
    reviewerUserId: resultDto.reviewerUserId ?? null,
    reviewerDisplayName: resultDto.reviewerDisplayName ?? '',
    reviewerActionAt: resultDto.reviewerActionAt ?? null,
    reviewActionLogs: normalizeReviewActionLogs(resultDto.actionLogs, resultDto.reviewActionLogs),
    materials: statusDto.materials,
    previewMaterials: statusDto.materials.map(toMaterialPreviewItem),
    summary: summarizeIssues(resultDto.issues),
    extractedFields: normalizeExtractedFields(resultDto.extractedFields),
    fieldConfidence: normalizeFieldConfidence(resultDto.extractedFields),
    materialSummaries: {},
    findings: resultDto.issues.map(toReviewerFinding),
    riskHints: resultDto.riskHints.map(formatRiskHint),
    draftOpinion: resultDto.draftOpinion,
    manualReviewNotice,
    failureCategory,
    failureReason,
    requiresManualReview:
      failureCategory !== null
      || hasBlocker
      || manualReviewNotice !== ''
      || (resultDto.handlingStatus ?? statusDto.handlingStatus ?? null) === 'MANUAL_REVIEW_REQUIRED',
  }
}

function normalizeReviewActionLogs(
  actionLogs: ReviewActionLogDto[] | null | undefined,
  reviewActionLogs: ReviewActionLogDto[] | null | undefined,
): ReviewActionLogView[] {
  const logs = actionLogs && actionLogs.length > 0
    ? actionLogs
    : (reviewActionLogs ?? [])
  if (!Array.isArray(logs)) {
    return []
  }

  return logs.map((log) => ({
    actionCode: log.actionCode,
    actionLabel: log.actionLabel ?? inferActionLabel(log.actionCode),
    reviewerRemark: log.reviewerRemark ?? '',
    operatorUserId: typeof log.operatorUserId === 'number' ? log.operatorUserId : null,
    operatorDisplayName: log.operatorDisplayName ?? '',
    fromHandlingStatus: log.fromHandlingStatus ?? null,
    toHandlingStatus: log.toHandlingStatus ?? null,
    operatedAt: log.operatedAt ?? null,
  }))
}

function toMaterialPreviewItem(slot: MaterialSlot): MaterialPreviewItem {
  return {
    materialType: slot.materialType,
    originalFileName: slot.originalFileName,
    uploaded: slot.uploaded,
    previewPath: slot.previewPath ?? null,
    kind: inferPreviewKind(slot),
  }
}

function inferPreviewKind(slot: MaterialSlot): MaterialPreviewItem['kind'] {
  if (!slot.uploaded) {
    return 'missing'
  }

  const fileName = slot.originalFileName?.toLowerCase() ?? ''
  if (fileName.endsWith('.pdf')) {
    return 'pdf'
  }
  if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || fileName.endsWith('.png')) {
    return 'image'
  }
  return 'unsupported'
}

function inferActionLabel(actionCode: string): string {
  return isReviewerActionCode(actionCode) ? REVIEWER_ACTION_LABELS[actionCode] : actionCode
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

function isReviewerActionCode(value: string): value is keyof typeof REVIEWER_ACTION_LABELS {
  return value in REVIEWER_ACTION_LABELS
}

export function isReviewerActionCompleted(status: HandlingStatus): boolean {
  return status === 'INITIAL_REVIEW_PASSED'
    || status === 'CORRECTION_REQUIRED'
    || status === 'MANUAL_REVIEW_REQUIRED'
}

function normalizeExtractedFields(value: unknown): Record<string, string> {
  if (Array.isArray(value)) {
    return Object.fromEntries(
      value.flatMap((field) => {
        if (!isRecord(field) || typeof field.fieldKey !== 'string') {
          return []
        }
        return [[field.fieldKey, String(field.fieldValue ?? '')]]
      }),
    )
  }

  if (!isRecord(value)) {
    return {}
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, fieldValue]) => [key, String(fieldValue ?? '')]),
  )
}

function normalizeFieldConfidence(value: unknown): Record<string, number> | null {
  if (!Array.isArray(value)) {
    return null
  }

  const entries = value.flatMap((field) => {
    if (!isRecord(field) || typeof field.fieldKey !== 'string' || typeof field.confidence !== 'number') {
      return []
    }
    return [[field.fieldKey, field.confidence]]
  })

  return entries.length > 0 ? Object.fromEntries(entries) : null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
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
