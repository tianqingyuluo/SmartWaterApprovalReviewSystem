import { describe, expect, it } from 'vitest'
import { getMcpContractExamples, toCheckCompletenessView, toKnowledgeSearchView } from './mcpDemo'
import type { CheckCompletenessResponseDto, KnowledgeSearchResponseDto } from '@/types'

describe('MCP demo adapters', () => {
  it('maps knowledge_search DTO results to page view labels', () => {
    const dto: KnowledgeSearchResponseDto = {
      query: '取水许可',
      requestedTopK: 3,
      topK: 3,
      total: 1,
      knowledgePackVersion: 'water-permit-mvp-2026-04-27',
      results: [
        {
          section: 'reviewBasis',
          id: 'BASIS_PUBLIC_NOTICE',
          title: '公示要求',
          materialType: null,
          fieldPath: null,
          excerpt: '涉及公共利益的取水许可事项需要结合公示要求审查。',
          score: 2,
          rank: 1,
          sourceRefs: ['source-a'],
          sourceIds: ['WATER_PERMIT_REVIEW_BASIS'],
          basisRefs: [],
        },
      ],
    }

    const view = toKnowledgeSearchView(dto, 'live', '2026-05-19T10:00:00.000Z')

    expect(view.source).toBe('live')
    expect(view.results[0].sectionLabel).toBe('审查依据')
    expect(view.results[0].sourceIds).toEqual(['WATER_PERMIT_REVIEW_BASIS'])
  })

  it('keeps completeness response structure and source metadata', () => {
    const dto: CheckCompletenessResponseDto = {
      submitted: ['APPLICATION_FORM', 'BUSINESS_LICENSE'],
      required: ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD'],
      missing: ['ID_CARD'],
      complete: false,
      knowledgePackVersion: 'water-permit-mvp-2026-04-27',
      findings: [
        {
          code: 'MISSING_MATERIAL',
          severity: 'WARNING',
          materialType: 'ID_CARD',
          materialId: 'MATERIAL_ID_CARD',
          materialDisplayName: '身份证',
          message: '缺少身份证。',
          applicantMessage: '请补充身份证。',
          basisRefs: ['BASIS_WATER_LAW_PERMIT_REQUIREMENT'],
          sourceRefs: ['water-permit:mvp:material-checklist'],
        },
      ],
    }

    const view = toCheckCompletenessView(dto, 'demo', '2026-05-19T10:01:00.000Z')

    expect(view.source).toBe('demo')
    expect(view.complete).toBe(false)
    expect(view.missing).toEqual(['ID_CARD'])
    expect(view.findings[0].basisRefs).toContain('BASIS_WATER_LAW_PERMIT_REQUIREMENT')
  })

  it('exports request and response contract examples for CP2 docs', () => {
    const examples = getMcpContractExamples()

    expect(examples.map((item) => item.tool)).toEqual(['knowledge_search', 'check_completeness'])
    expect(examples[0].endpoint).toBe('POST /mcp/tools/knowledge_search')
    expect(examples[1].response).toHaveProperty('missing')
  })
})
