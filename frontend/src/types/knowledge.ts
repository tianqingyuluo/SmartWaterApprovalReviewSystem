import type { MaterialType } from './smartwater'

export type McpToolName = 'knowledge_search' | 'check_completeness'

export type DemoSource = 'api' | 'demo'

export interface KnowledgeStatusView {
  knowledgeAvailable: boolean
  mcpAvailable: boolean
  knowledgePackVersion: string
  lastToolName: McpToolName | null
  lastCalledAt: string | null
  source: DemoSource
  message: string
}

export interface KnowledgeSearchRequest {
  query: string
  topK: number
}

export interface KnowledgeSearchResultItem {
  rank: number
  section: string
  id: string
  title: string
  materialType: MaterialType | null
  fieldPath: string | null
  excerpt: string
  score: number
  sourceIds: string[]
  sourceRefs: string[]
  basisRefs: string[]
}

export interface KnowledgeSearchResponse {
  query: string
  requestedTopK: number | string
  topK: number
  total: number
  results: KnowledgeSearchResultItem[]
  knowledgePackVersion: string
}

export interface CompletenessFinding {
  code: string
  severity: string
  materialType: MaterialType
  materialId: string
  materialDisplayName: string
  message: string
  applicantMessage: string
  basisRefs: string[]
  sourceRefs: string[]
}

export interface CompletenessResponse {
  submitted: MaterialType[]
  required: MaterialType[]
  missing: MaterialType[]
  complete: boolean
  findings: CompletenessFinding[]
  knowledgePackVersion: string
}
