import { afterEach, describe, expect, it, vi } from 'vitest'
import request from '@/utils/request'
import {
  callCheckCompletenessTool,
  callKnowledgeSearchTool,
  toKnowledgeStatusFromAiHealth,
} from './knowledge'
import type { AiHealthResponse, CompletenessResponse, KnowledgeSearchResponse, R } from '@/types'

describe('knowledge API adapters', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('maps Java AI health response to page status with real API source', () => {
    const health: AiHealthResponse = {
      baseUrl: 'http://localhost:8000',
      healthUrl: 'http://localhost:8000/health',
      reachable: true,
      statusCode: 200,
      message: 'AI service health endpoint is reachable',
      responseBody: '{"status":"ok","knowledgePackVersion":"water-permit-mvp-2026-04-27"}',
      mcpTransport: 'streamable-http',
      mcpUrl: 'http://localhost:8000/mcp',
      internalTokenConfigured: false,
      checkedAt: '2026-05-28T14:50:04',
    }

    expect(toKnowledgeStatusFromAiHealth(health, 'knowledge_search')).toEqual({
      knowledgeAvailable: true,
      mcpAvailable: true,
      knowledgePackVersion: 'water-permit-mvp-2026-04-27',
      lastToolName: 'knowledge_search',
      lastCalledAt: '2026-05-28T14:50:04',
      source: 'api',
      message: 'AI service health endpoint is reachable',
    })
  })

  it('marks MCP unavailable when Java health cannot reach Python service', () => {
    const health: AiHealthResponse = {
      baseUrl: 'http://localhost:8000',
      healthUrl: 'http://localhost:8000/health',
      reachable: false,
      statusCode: null,
      message: 'AI service health endpoint is unreachable: ResourceAccessException',
      responseBody: '',
      mcpTransport: 'streamable-http',
      mcpUrl: 'http://localhost:8000/mcp',
      internalTokenConfigured: false,
      checkedAt: '2026-05-28T14:50:04',
    }

    const status = toKnowledgeStatusFromAiHealth(health)

    expect(status.knowledgeAvailable).toBe(false)
    expect(status.mcpAvailable).toBe(false)
    expect(status.source).toBe('api')
    expect(status.knowledgePackVersion).toBe('unknown')
  })

  it('calls Java backend MCP knowledge_search proxy instead of local demo data', async () => {
    const payload: R<KnowledgeSearchResponse> = {
      code: 200,
      message: 'success',
      data: {
        query: '营业执照',
        requestedTopK: 3,
        topK: 3,
        total: 1,
        results: [
          {
            rank: 1,
            section: 'materialChecklist',
            id: 'MAT_BUSINESS_LICENSE',
            title: '营业执照',
            materialType: 'BUSINESS_LICENSE',
            fieldPath: null,
            excerpt: '营业执照用于校验申请主体。',
            score: 1,
            sourceIds: ['SRC_SAMPLE_BUSINESS_LICENSE'],
            sourceRefs: ['SRC_PROCESS_DOC'],
            basisRefs: ['BASIS_MATERIAL_INITIAL_LIST'],
          },
        ],
        knowledgePackVersion: 'water-permit-mvp-2026-04-27',
      },
    }
    const post = vi.spyOn(request, 'post').mockResolvedValueOnce({ data: payload })

    const result = await callKnowledgeSearchTool({ query: '营业执照', topK: 3 })

    expect(post).toHaveBeenCalledWith('/ai/mcp/knowledge-search', {
      query: '营业执照',
      topK: 3,
    })
    expect(result.results[0].id).toBe('MAT_BUSINESS_LICENSE')
  })

  it('calls Java backend MCP check_completeness proxy instead of local demo data', async () => {
    const payload: R<CompletenessResponse> = {
      code: 200,
      message: 'success',
      data: {
        submitted: ['APPLICATION_FORM', 'BUSINESS_LICENSE'],
        required: ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD'],
        missing: ['ID_CARD'],
        complete: false,
        findings: [
          {
            code: 'MISSING_MATERIAL',
            severity: 'WARNING',
            materialType: 'ID_CARD',
            materialId: 'MAT_ID_CARD',
            materialDisplayName: '法定代表人身份证',
            message: '缺少法定代表人身份证。',
            applicantMessage: '请补充身份证。',
            basisRefs: ['BASIS_MATERIAL_INITIAL_LIST'],
            sourceRefs: ['SRC_SAMPLE_ID_CARD'],
          },
        ],
        knowledgePackVersion: 'water-permit-mvp-2026-04-27',
      },
    }
    const post = vi.spyOn(request, 'post').mockResolvedValueOnce({ data: payload })

    const result = await callCheckCompletenessTool(['APPLICATION_FORM', 'BUSINESS_LICENSE'])

    expect(post).toHaveBeenCalledWith('/ai/mcp/check-completeness', {
      materials: ['APPLICATION_FORM', 'BUSINESS_LICENSE'],
    })
    expect(result.missing).toEqual(['ID_CARD'])
  })

  it('sends empty material selection to backend MCP check_completeness', async () => {
    const payload: R<CompletenessResponse> = {
      code: 200,
      message: 'success',
      data: {
        submitted: [],
        required: ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD'],
        missing: ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD'],
        complete: false,
        findings: [],
        knowledgePackVersion: 'water-permit-mvp-2026-04-27',
      },
    }
    const post = vi.spyOn(request, 'post').mockResolvedValueOnce({ data: payload })

    await callCheckCompletenessTool([])

    expect(post).toHaveBeenCalledWith('/ai/mcp/check-completeness', {
      materials: [],
    })
  })
})
