import type {
  CompletenessResponse,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  KnowledgeStatusView,
  MaterialType,
  McpToolName,
} from '@/types'
import { MATERIAL_LABELS } from '@/types'

const DEMO_KNOWLEDGE_PACK_VERSION = 'water-permit-mvp-2026-05'

export function buildDemoStatus(toolName: McpToolName | null = null, message = '当前后端未暴露 MCP HTTP 代理，页面使用与 Python 工具同结构的演示数据。'): KnowledgeStatusView {
  return {
    knowledgeAvailable: true,
    mcpAvailable: true,
    knowledgePackVersion: DEMO_KNOWLEDGE_PACK_VERSION,
    lastToolName: toolName,
    lastCalledAt: toolName ? new Date().toISOString() : null,
    source: 'demo',
    message,
  }
}

export function buildDemoKnowledgeSearch(params: KnowledgeSearchRequest): KnowledgeSearchResponse {
  const normalizedQuery = params.query.trim()
  const topK = Math.max(1, Math.min(50, Number.isFinite(params.topK) ? params.topK : 5))
  const allResults = [
    {
      rank: 1,
      section: 'materialChecklist',
      id: 'mvp-required-application-form',
      title: '取水许可申请书',
      materialType: 'APPLICATION_FORM' as MaterialType,
      fieldPath: null,
      excerpt: '取水许可申请书是完整初审的必需材料，用于核对申请主体、取水地点、取水量和用途。',
      score: 3,
      sourceIds: ['water-permit:mvp:application'],
      sourceRefs: ['取水许可办理材料清单'],
      basisRefs: ['BASIS_APPLICATION_FORM_REQUIRED'],
    },
    {
      rank: 2,
      section: 'materialChecklist',
      id: 'mvp-required-business-license',
      title: '营业执照',
      materialType: 'BUSINESS_LICENSE' as MaterialType,
      fieldPath: null,
      excerpt: '营业执照用于校验申请单位名称、统一社会信用代码与申请书主体信息是否一致。',
      score: 2,
      sourceIds: ['water-permit:mvp:identity'],
      sourceRefs: ['主体资格核验规则'],
      basisRefs: ['BASIS_BUSINESS_LICENSE_REQUIRED'],
    },
    {
      rank: 3,
      section: 'applicationFieldRules',
      id: 'field-annual-water-use',
      title: '年取水量字段核验',
      materialType: 'APPLICATION_FORM' as MaterialType,
      fieldPath: 'application.annualWaterUse',
      excerpt: '申请书中的年取水量需要结合项目类型、用途说明和行业分类进行人工复核。',
      score: 1,
      sourceIds: ['water-permit:mvp:field-rules'],
      sourceRefs: ['取水许可字段核验规则'],
      basisRefs: ['BASIS_WATER_AMOUNT_REVIEW'],
    },
  ]

  const filtered = normalizedQuery
    ? allResults.filter((item) => {
      const haystack = `${item.title} ${item.excerpt} ${item.id}`.toLowerCase()
      return normalizedQuery.toLowerCase().split(/\s+/).some((token) => haystack.includes(token))
    })
    : allResults

  return {
    query: normalizedQuery,
    requestedTopK: params.topK,
    topK,
    total: filtered.slice(0, topK).length,
    results: filtered.slice(0, topK).map((item, index) => ({ ...item, rank: index + 1 })),
    knowledgePackVersion: DEMO_KNOWLEDGE_PACK_VERSION,
  }
}

export function buildDemoCompleteness(materials: MaterialType[]): CompletenessResponse {
  const required: MaterialType[] = ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD']
  const submitted = required.filter((type) => materials.includes(type))
  const missing = required.filter((type) => !submitted.includes(type))

  return {
    submitted,
    required,
    missing,
    complete: missing.length === 0,
    findings: missing.map((materialType) => ({
      code: 'MISSING_MATERIAL',
      severity: materialType === 'ID_CARD' ? 'BLOCKER' : 'WARNING',
      materialType,
      materialId: materialType.toLowerCase(),
      materialDisplayName: MATERIAL_LABELS[materialType],
      message: `${MATERIAL_LABELS[materialType]}未提交，完整性检查不通过。`,
      applicantMessage: `请补充${MATERIAL_LABELS[materialType]}后重新提交。`,
      basisRefs: ['BASIS_MVP_REQUIRED_MATERIALS'],
      sourceRefs: ['取水许可 MVP 材料清单'],
    })),
    knowledgePackVersion: DEMO_KNOWLEDGE_PACK_VERSION,
  }
}

