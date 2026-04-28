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

export interface MaterialSlot {
  materialType: MaterialType
  originalFileName: string | null
  fileExtension: string | null
  fileSize: number | null
  uploadedAt: string | null
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

export interface ApplicantResult {
  missingMaterials: MaterialType[]
  fieldIssues: Finding[]
  suggestions: string[]
}

export interface ReviewerResult {
  extractedFields: Record<string, string>
  fieldConfidence: Record<string, number>
  materialSummaries: Record<string, string>
  findings: Finding[]
  draftOpinion: string
  riskHints: string[]
  manualReviewNotice: string
  failureCategory: string | null
  failureReason: string | null
}

export interface ReviewTask {
  taskId: string
  sessionId: string
  status: ProcessingStatus
  submittedAt: string
  updatedAt: string
  materialSlots: MaterialSlot[]
  resultSummary: ResultSummary | null
  applicantResult: ApplicantResult | null
  reviewerResult: ReviewerResult | null
}

export interface SubmitResponse {
  taskId: string
  sessionId: string
}

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
