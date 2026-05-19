import type { MaterialType, Severity } from './smartwater'

export type McpToolName = 'knowledge_search' | 'check_completeness'

export type McpCallSource = 'live' | 'demo'

export interface McpServiceStatusView {
  knowledgePackStatus: 'available' | 'demo' | 'unavailable'
  mcpStatus: 'connected' | 'demo' | 'unavailable'
  knowledgePackVersion: string
  lastToolName: McpToolName | null
  lastCalledAt: string | null
  lastSource: McpCallSource | null
  lastError: string | null
}

export interface KnowledgeSearchRequest {
  query: string
  topK: number
}

export interface KnowledgeSearchResultDto {
  section: string
  id: string
  title: string
  materialType: MaterialType | null
  fieldPath: string | null
  excerpt: string
  score: number
  rank: number
  sourceRefs: string[]
  sourceIds: string[]
  basisRefs: string[]
}

export interface KnowledgeSearchResponseDto {
  query: string
  requestedTopK: number | string
  topK: number
  total: number
  results: KnowledgeSearchResultDto[]
  knowledgePackVersion: string
}

export interface KnowledgeSearchResultView extends KnowledgeSearchResultDto {
  sectionLabel: string
}

export interface KnowledgeSearchView {
  query: string
  requestedTopK: number | string
  topK: number
  total: number
  results: KnowledgeSearchResultView[]
  knowledgePackVersion: string
  source: McpCallSource
  requestedAt: string
}

export interface CheckCompletenessRequest {
  materials: MaterialType[]
}

export interface CompletenessFindingDto {
  code: string
  severity: Severity
  materialType: MaterialType
  materialId: string
  materialDisplayName: string
  message: string
  applicantMessage: string
  basisRefs: string[]
  sourceRefs: string[]
}

export interface CheckCompletenessResponseDto {
  submitted: MaterialType[]
  required: MaterialType[]
  missing: MaterialType[]
  complete: boolean
  findings: CompletenessFindingDto[]
  knowledgePackVersion: string
}

export interface CheckCompletenessView extends CheckCompletenessResponseDto {
  source: McpCallSource
  requestedAt: string
}

export interface McpToolContractExample {
  tool: McpToolName
  endpoint: string
  request: unknown
  response: unknown
  fields: Array<{
    name: string
    description: string
  }>
}
