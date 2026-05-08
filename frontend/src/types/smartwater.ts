export type MaterialType = 'APPLICATION_FORM' | 'BUSINESS_LICENSE' | 'ID_CARD'

export type ProcessingStatus =
  | 'SUBMITTED'
  | 'QUEUED'
  | 'PROCESSING'
  | 'PARTIAL_SUCCESS'
  | 'COMPLETED'
  | 'FAILED'

export type Severity = 'INFO' | 'WARNING' | 'BLOCKER'

export type Audience = 'APPLICANT' | 'REVIEWER' | 'SYSTEM'

export const MATERIAL_LABELS: Record<MaterialType, string> = {
  APPLICATION_FORM: '取水许可申请书',
  BUSINESS_LICENSE: '营业执照',
  ID_CARD: '身份证',
}

export const MATERIAL_SLOTS: MaterialType[] = ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD']

export const ACCEPTED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'pdf']

/** MaterialType → multipart form field name expected by Java backend */
export const MATERIAL_FORM_FIELDS: Record<MaterialType, string> = {
  APPLICATION_FORM: 'applicationForm',
  BUSINESS_LICENSE: 'businessLicense',
  ID_CARD: 'idCard',
}

// ── Shared sub-DTOs ──

export interface MaterialSlot {
  materialType: MaterialType
  originalFileName: string | null
  uploaded: boolean
  fileExtension?: string | null
  fileSize?: number | null
  uploadedAt?: string | null
}

export interface Finding {
  findingType: string
  severity: Severity
  audience: Audience
  description: string
  basis: string | null
}

export interface ResultSummary {
  totalFindings: number
  blockerCount: number
  warningCount: number
  infoCount: number
}

export interface ApplicantIssueDto {
  code: string
  severity: Severity
  message: string
}

export interface ReviewerIssueDto extends ApplicantIssueDto {
  materialType?: MaterialType | null
  fieldKey?: string | null
  basisRefs?: string[] | null
  applicantVisible?: boolean | null
}

export interface RiskHintDto {
  riskLevel: string
  description: string
  basisRefs?: string[] | null
  requiresManualReview?: boolean | null
}

// ── Submit ──

export interface SubmitResponse {
  taskId: string
  sessionId: string
  status?: ProcessingStatus
  submittedAt?: string
  materials?: MaterialSlot[]
}

// ── Backend DTOs (match actual endpoint response shapes) ──

/** GET /task/{taskId}/status */
export interface TaskStatusResponse {
  taskId: string
  status: ProcessingStatus
  submittedAt: string
  updatedAt: string
  materials: MaterialSlot[]
  message?: string
}

/** GET /task/{taskId}/result/applicant */
export interface ApplicantResultResponse {
  taskId: string
  status: ProcessingStatus
  summary: string
  issues: ApplicantIssueDto[]
  missingMaterials: MaterialType[]
}

/** GET /task/{taskId}/result/reviewer */
export interface ReviewerResultResponse {
  taskId: string
  status: ProcessingStatus
  summary: string
  issues: ReviewerIssueDto[]
  riskHints: RiskHintDto[]
  draftOpinion: string
  manualReviewNotice?: string | null
  missingMaterials: MaterialType[]
  extractedFields: unknown
  modelMetadata?: string | null
}

// ── View models (transformed from backend DTOs for page consumption) ──

export interface ApplicantResultView {
  status: ProcessingStatus
  missingMaterials: MaterialType[]
  fieldIssues: Finding[]
  suggestions: string[]
}

export interface ReviewerResultView {
  status: ProcessingStatus
  materials: MaterialSlot[]
  summary: ResultSummary | null
  extractedFields: Record<string, string>
  fieldConfidence: Record<string, number> | null
  materialSummaries: Record<string, string>
  findings: Finding[]
  riskHints: string[]
  draftOpinion: string
  manualReviewNotice: string
  failureCategory: string | null
  failureReason: string | null
}

// ── Status labels ──

export const STATUS_LABELS_APPLICANT: Record<ProcessingStatus, string> = {
  SUBMITTED: '已提交',
  QUEUED: '等待处理',
  PROCESSING: '智能审核处理中',
  PARTIAL_SUCCESS: '部分结果已生成',
  COMPLETED: '审核辅助结果已生成',
  FAILED: '暂无法生成结果',
}

export const STATUS_LABELS_REVIEWER: Record<ProcessingStatus, string> = {
  SUBMITTED: '已提交',
  QUEUED: '等待 Worker 处理',
  PROCESSING: 'OCR/抽取/审核处理中',
  PARTIAL_SUCCESS: '部分材料或步骤处理失败',
  COMPLETED: '完整审核辅助结果已生成',
  FAILED: '处理失败，查看失败原因',
}
