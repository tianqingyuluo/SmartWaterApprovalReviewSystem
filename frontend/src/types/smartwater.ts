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
export type UserRole = 'APPLICANT' | 'REVIEWER' | 'ADMIN'
export type ReviewerActionCode = 'APPROVE_INITIAL_REVIEW' | 'RETURN_FOR_CORRECTION' | 'TRANSFER_MANUAL_REVIEW'
export type HandlingStatus = 'INITIAL_REVIEW_PASSED' | 'CORRECTION_REQUIRED' | 'MANUAL_REVIEW_REQUIRED' | null

export const MATERIAL_LABELS: Record<MaterialType, string> = {
  APPLICATION_FORM: '取水许可申请书',
  BUSINESS_LICENSE: '营业执照',
  ID_CARD: '身份证',
}

export const MATERIAL_SLOTS: MaterialType[] = ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD']

export const ACCEPTED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'pdf', 'docx']

export const REVIEWER_ACTION_LABELS: Record<ReviewerActionCode, string> = {
  APPROVE_INITIAL_REVIEW: '通过初审',
  RETURN_FOR_CORRECTION: '退回补正',
  TRANSFER_MANUAL_REVIEW: '转人工复核',
}

export const HANDLING_STATUS_LABELS: Record<Exclude<HandlingStatus, null>, string> = {
  INITIAL_REVIEW_PASSED: '通过初审',
  CORRECTION_REQUIRED: '退回补正',
  MANUAL_REVIEW_REQUIRED: '转人工复核',
}

export type FailureCategory =
  | 'SYSTEM_ERROR'
  | 'AUTH_ERROR'
  | 'RATE_LIMIT'
  | 'TIMEOUT'
  | 'UPSTREAM_5XX'
  | 'INVALID_JSON'
  | 'SCHEMA_MISMATCH'
  | 'CONTENT_FILTERED'
  | null

export const FAILURE_CATEGORY_LABELS: Record<string, string> = {
  SYSTEM_ERROR: '系统处理异常',
  AUTH_ERROR: '服务认证失败',
  RATE_LIMIT: '请求过于频繁',
  TIMEOUT: '处理超时',
  UPSTREAM_5XX: '上游服务异常',
  INVALID_JSON: '结果格式异常',
  SCHEMA_MISMATCH: '结果结构不匹配',
  CONTENT_FILTERED: '内容被过滤',
}

/** 任务状态标签颜色，用于列表和表格展示 */
export const STATUS_TAG_COLORS: Record<ProcessingStatus, { bg: string; text: string; border: string }> = {
  SUBMITTED: { bg: '#f5f5f5', text: '#999', border: '#d9d9d9' },
  QUEUED: { bg: '#f5f5f5', text: '#999', border: '#d9d9d9' },
  PROCESSING: { bg: '#e6f7ff', text: '#1890ff', border: '#91d5ff' },
  PARTIAL_SUCCESS: { bg: '#fff7e6', text: '#fa8c16', border: '#ffd591' },
  COMPLETED: { bg: '#f6ffed', text: '#52c41a', border: '#b7eb8f' },
  FAILED: { bg: '#fff2f0', text: '#ff4d4f', border: '#ffccc7' },
}

/** MaterialType 到 Java 后端 multipart 字段名的映射 */
export const MATERIAL_FORM_FIELDS: Record<MaterialType, string> = {
  APPLICATION_FORM: 'applicationForm',
  BUSINESS_LICENSE: 'businessLicense',
  ID_CARD: 'idCard',
}

// 共享子 DTO

export interface MaterialSlot {
  materialType: MaterialType
  originalFileName: string | null
  uploaded: boolean
  fileSize?: number | null
  fileExtension?: string | null
  uploadedAt?: string | null
}

export type MaterialPreviewKind = 'IMAGE' | 'PDF' | 'UNSUPPORTED'

export interface MaterialPreviewState {
  materialType: MaterialType
  label: string
  fileName: string
  fileExtension: string
  kind: MaterialPreviewKind
  objectUrl: string | null
  loading: boolean
  error: string
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

export interface ToolCallTraceDto {
  toolName: string
  inputSummary?: string | null
  outputSummary?: string | null
  sourceRefs?: string[] | null
  status?: string | null
  latencyMs?: number | null
  error?: string | null
}

export interface ToolCallTraceView {
  toolName: string
  inputSummary: string
  outputSummary: string
  sourceRefs: string[]
  status: string
  latencyMs: number | null
  error: string
}

export interface ReviewActionLogDto {
  actionCode: string
  actionLabel?: string | null
  reviewerRemark?: string | null
  operatorUserId?: number | null
  operatorDisplayName?: string | null
  fromHandlingStatus?: string | null
  toHandlingStatus?: string | null
  operatedAt?: string | null
}

// 提交相关

export interface SubmitResponse {
  taskId: string
  sessionId?: string | null
  status?: ProcessingStatus
  submittedAt?: string
  materials?: MaterialSlot[]
}

export interface UserProfile {
  userId: number
  username: string
  displayName: string
  role: UserRole
}

export interface LoginResponse {
  token: string
  user: UserProfile
}

// 后端 DTO（与接口响应结构保持一致）

/** GET /task/{taskId}/status */
export interface TaskStatusResponse {
  taskId: string
  status: ProcessingStatus
  handlingStatus?: HandlingStatus
  handlingStatusLabel?: string | null
  reviewerRemark?: string | null
  submittedAt: string
  updatedAt: string
  materials: MaterialSlot[]
}

/** GET /task/{taskId}/result/applicant */
export interface ApplicantResultResponse {
  taskId: string
  status: ProcessingStatus
  handlingStatus?: HandlingStatus
  handlingStatusLabel?: string | null
  reviewerRemark?: string | null
  reviewerActionAt?: string | null
  summary: string
  issues: ApplicantIssueDto[]
  missingMaterials: MaterialType[]
}

/** GET /task/{taskId}/result/reviewer */
export interface ReviewerResultResponse {
  taskId: string
  status: ProcessingStatus
  handlingStatus?: HandlingStatus
  handlingStatusLabel?: string | null
  reviewerRemark?: string | null
  reviewerActionCode?: ReviewerActionCode | null
  reviewerUserId?: number | null
  reviewerDisplayName?: string | null
  reviewerActionAt?: string | null
  actionLogs?: ReviewActionLogDto[] | null
  reviewActionLogs?: ReviewActionLogDto[] | null
  summary: string
  issues: ReviewerIssueDto[]
  riskHints: RiskHintDto[]
  draftOpinion: string
  missingMaterials: MaterialType[]
  extractedFields: unknown
  manualReviewNotice?: string | null
  modelMetadata?: string | null
  toolCallTraces?: ToolCallTraceDto[] | null
}

// 任务列表

export interface TaskListItem {
  taskId: string
  sessionId?: string | null
  status: ProcessingStatus
  handlingStatus?: HandlingStatus
  handlingStatusLabel?: string | null
  reviewerRemark?: string | null
  reviewerDisplayName?: string | null
  reviewerActionAt?: string | null
  submittedAt: string
  updatedAt: string
  knowledgePackVersion: string | null
  materials: MaterialSlot[]
}

export interface TaskListResponse {
  items: TaskListItem[]
  total: number
  page: number
  size: number
}

// 页面使用的视图模型（由后端 DTO 转换而来）

export interface ApplicantResultView {
  status: ProcessingStatus
  missingMaterials: MaterialType[]
  fieldIssues: Finding[]
  suggestions: string[]
  handlingStatus: HandlingStatus
  handlingStatusLabel: string
  reviewerRemark: string
  reviewerActionAt: string | null
}

export interface ReviewActionLogView {
  actionCode: string
  actionLabel: string
  reviewerRemark: string
  operatorUserId: number | null
  operatorDisplayName: string
  fromHandlingStatus: string | null
  toHandlingStatus: string | null
  operatedAt: string | null
}

export interface ReviewerResultView {
  status: ProcessingStatus
  handlingStatus: HandlingStatus
  handlingStatusLabel: string
  reviewerRemark: string
  reviewerActionCode: ReviewerActionCode | null
  reviewerUserId: number | null
  reviewerDisplayName: string
  reviewerActionAt: string | null
  reviewActionLogs: ReviewActionLogView[]
  materials: MaterialSlot[]
  summary: ResultSummary | null
  extractedFields: Record<string, string>
  fieldConfidence: Record<string, number> | null
  materialSummaries: Record<string, string>
  findings: Finding[]
  riskHints: string[]
  draftOpinion: string
  manualReviewNotice: string
  toolCallTraces: ToolCallTraceView[]
  failureCategory: FailureCategory
  failureReason: string | null
  requiresManualReview: boolean
}

export interface TaskResultView extends ReviewerResultView {
  viewMode: 'APPLICANT' | 'REVIEWER'
}

export interface ReviewerActionSubmitRequest {
  actionCode: ReviewerActionCode
  reviewerRemark?: string
}

export interface ReviewerActionResponse {
  taskId: string
  actionCode: ReviewerActionCode
  actionLabel?: string | null
  handlingStatus: HandlingStatus
  handlingStatusLabel?: string | null
  reviewerRemark?: string | null
  operatorUserId?: number | null
  operatorDisplayName?: string | null
  operatedAt?: string | null
}

// 状态标签

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
