import request from '@/utils/request'
import { MATERIAL_LABELS } from '@/types'
import type {
  CheckCompletenessRequest,
  CheckCompletenessResponseDto,
  CheckCompletenessView,
  CompletenessFindingDto,
  KnowledgeSearchRequest,
  KnowledgeSearchResponseDto,
  KnowledgeSearchResultDto,
  KnowledgeSearchView,
  McpCallSource,
  McpToolContractExample,
  McpToolName,
  MaterialType,
} from '@/types'

const DEMO_VERSION = 'water-permit-mvp-2026-04-27'

interface McpCallOptions {
  allowDemoFallback?: boolean
}

const SECTION_LABELS: Record<string, string> = {
  materialChecklist: '材料清单',
  applicationFieldRules: '字段规则',
  reviewBasis: '审查依据',
  promptSnippets: '提示片段',
  manualReviewRules: '人工复核规则',
}

const REQUIRED_MATERIALS: MaterialType[] = ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD']

const DEMO_KNOWLEDGE_RESULTS: KnowledgeSearchResultDto[] = [
  {
    section: 'materialChecklist',
    id: 'MATERIAL_APPLICATION_FORM',
    title: '取水许可申请书',
    materialType: 'APPLICATION_FORM',
    fieldPath: null,
    excerpt: '申请书用于承载申请人、取水地点、取水用途、计划取水量等基础信息，是完整审查的核心材料。',
    score: 3,
    rank: 1,
    sourceRefs: ['water-permit:mvp:material-checklist'],
    sourceIds: ['WATER_PERMIT_MVP_CHECKLIST'],
    basisRefs: ['BASIS_WATER_LAW_PERMIT_REQUIREMENT'],
  },
  {
    section: 'applicationFieldRules',
    id: 'FIELD_DAILY_WATER_USE',
    title: '计划取水量字段完整性',
    materialType: 'APPLICATION_FORM',
    fieldPath: 'application.dailyWaterUse',
    excerpt: '计划取水量需要与申请用途、项目规模和材料描述保持一致，缺失或明显异常时应提示人工复核。',
    score: 2,
    rank: 2,
    sourceRefs: ['water-permit:mvp:field-rules'],
    sourceIds: ['WATER_PERMIT_MVP_FIELD_RULES'],
    basisRefs: ['BASIS_WATER_RESOURCE_REVIEW'],
  },
  {
    section: 'reviewBasis',
    id: 'BASIS_PUBLIC_NOTICE',
    title: '取水许可公示要求',
    materialType: null,
    fieldPath: null,
    excerpt: '涉及公共利益或重大取水影响的事项，应结合公示、论证和主管部门要求进行人工判断。',
    score: 1,
    rank: 3,
    sourceRefs: [],
    sourceIds: ['WATER_PERMIT_REVIEW_BASIS'],
    basisRefs: [],
  },
  {
    section: 'manualReviewRules',
    id: 'RULE_MULTI_WATER_SOURCE',
    title: '多水源场景人工复核',
    materialType: null,
    fieldPath: 'waterSources',
    excerpt: 'MVP 不自动判定多水源复杂场景，识别到多水源或取水点描述冲突时输出人工复核提示。',
    score: 1,
    rank: 4,
    sourceRefs: ['water-permit:mvp:manual-review'],
    sourceIds: ['WATER_PERMIT_MANUAL_REVIEW'],
    basisRefs: ['BASIS_WATER_RESOURCE_REVIEW'],
  },
]

export async function callKnowledgeSearch(
  requestBody: KnowledgeSearchRequest,
  options: McpCallOptions = {},
): Promise<KnowledgeSearchView> {
  const requestedAt = new Date().toISOString()
  try {
    const response = await request.post<KnowledgeSearchResponseDto>('/mcp/tools/knowledge_search', {
      query: requestBody.query,
      top_k: requestBody.topK,
    })
    return toKnowledgeSearchView(response.data, 'live', requestedAt)
  } catch {
    if (options.allowDemoFallback === false) {
      throw new Error('MCP knowledge_search 服务暂不可用，请确认 MCP HTTP 适配服务已启动。')
    }
    return toKnowledgeSearchView(buildDemoKnowledgeSearch(requestBody), 'demo', requestedAt)
  }
}

export async function callCheckCompleteness(
  requestBody: CheckCompletenessRequest,
  options: McpCallOptions = {},
): Promise<CheckCompletenessView> {
  const requestedAt = new Date().toISOString()
  try {
    const response = await request.post<CheckCompletenessResponseDto>('/mcp/tools/check_completeness', {
      materials: requestBody.materials,
    })
    return toCheckCompletenessView(response.data, 'live', requestedAt)
  } catch {
    if (options.allowDemoFallback === false) {
      throw new Error('MCP check_completeness 服务暂不可用，请确认 MCP HTTP 适配服务已启动。')
    }
    return toCheckCompletenessView(buildDemoCompleteness(requestBody.materials), 'demo', requestedAt)
  }
}

export function toKnowledgeSearchView(
  dto: KnowledgeSearchResponseDto,
  source: McpCallSource,
  requestedAt: string,
): KnowledgeSearchView {
  return {
    ...dto,
    source,
    requestedAt,
    results: dto.results.map((item) => ({
      ...item,
      sectionLabel: SECTION_LABELS[item.section] ?? item.section,
    })),
  }
}

export function toCheckCompletenessView(
  dto: CheckCompletenessResponseDto,
  source: McpCallSource,
  requestedAt: string,
): CheckCompletenessView {
  return {
    ...dto,
    source,
    requestedAt,
  }
}

export function getMcpContractExamples(): McpToolContractExample[] {
  return [
    {
      tool: 'knowledge_search',
      endpoint: 'POST /mcp/tools/knowledge_search',
      request: {
        query: '取水许可 材料',
        top_k: 5,
      },
      response: buildDemoKnowledgeSearch({ query: '取水许可 材料', topK: 2 }),
      fields: [
        { name: 'query', description: '原始查询文本，服务端会去除首尾空格。' },
        { name: 'topK/requestedTopK', description: '实际检索数量和调用方请求数量，topK 会被限制在 1-50。' },
        { name: 'results[].basisRefs', description: '结果引用的知识依据 ID，仅允许来自输入知识片段。' },
        { name: 'knowledgePackVersion', description: '当前 MCP 工具加载的知识包版本。' },
      ],
    },
    {
      tool: 'check_completeness',
      endpoint: 'POST /mcp/tools/check_completeness',
      request: {
        materials: ['APPLICATION_FORM', 'BUSINESS_LICENSE'],
      },
      response: buildDemoCompleteness(['APPLICATION_FORM', 'BUSINESS_LICENSE']),
      fields: [
        { name: 'submitted', description: '识别出的已提交 MVP 材料类型，未知材料会被忽略。' },
        { name: 'missing', description: '仍缺失的必需材料类型。' },
        { name: 'findings[]', description: '一项缺失材料对应一条结构化问题提示。' },
        { name: 'complete', description: '仅在 missing 为空时为 true。' },
      ],
    },
  ]
}

export function formatToolName(toolName: McpToolName): string {
  return toolName === 'knowledge_search' ? 'knowledge_search' : 'check_completeness'
}

function buildDemoKnowledgeSearch(requestBody: KnowledgeSearchRequest): KnowledgeSearchResponseDto {
  const query = requestBody.query.trim()
  const safeTopK = Math.max(1, Math.min(50, requestBody.topK || 5))
  const normalized = query.toLowerCase()
  const matched = normalized
    ? DEMO_KNOWLEDGE_RESULTS.filter((item) => {
        const haystack = [
          item.id,
          item.title,
          item.materialType ?? '',
          item.fieldPath ?? '',
          item.excerpt,
          ...item.basisRefs,
          ...item.sourceIds,
        ].join(' ').toLowerCase()
        return normalized.split(/\s+/).some((token) => token && haystack.includes(token))
      })
    : DEMO_KNOWLEDGE_RESULTS

  const results = (matched.length ? matched : []).slice(0, safeTopK).map((item, index) => ({
    ...item,
    rank: index + 1,
  }))

  return {
    query,
    requestedTopK: requestBody.topK,
    topK: safeTopK,
    total: results.length,
    results,
    knowledgePackVersion: DEMO_VERSION,
  }
}

function buildDemoCompleteness(materials: MaterialType[]): CheckCompletenessResponseDto {
  const submitted = dedupeMaterials(materials)
  const submittedSet = new Set(submitted)
  const missing = REQUIRED_MATERIALS.filter((material) => !submittedSet.has(material))
  const findings = missing.map((materialType): CompletenessFindingDto => ({
    code: 'MISSING_MATERIAL',
    severity: 'WARNING',
    materialType,
    materialId: `MATERIAL_${materialType}`,
    materialDisplayName: MATERIAL_LABELS[materialType],
    message: `缺少${MATERIAL_LABELS[materialType]}，需要人工确认材料是否可补正。`,
    applicantMessage: `请补充${MATERIAL_LABELS[materialType]}后重新提交。`,
    basisRefs: ['BASIS_WATER_LAW_PERMIT_REQUIREMENT'],
    sourceRefs: ['water-permit:mvp:material-checklist'],
  }))

  return {
    submitted,
    required: REQUIRED_MATERIALS,
    missing,
    complete: missing.length === 0,
    findings,
    knowledgePackVersion: DEMO_VERSION,
  }
}

function dedupeMaterials(materials: MaterialType[]): MaterialType[] {
  const seen = new Set<MaterialType>()
  return materials.filter((material) => {
    if (seen.has(material)) {
      return false
    }
    seen.add(material)
    return true
  })
}
