import { describe, expect, it } from 'vitest'
import {
  getMaterialPreviewUrl,
  isReviewerActionCompleted,
  toApplicantResultView,
  toApplicantTaskResultView,
  toReviewerResultView,
} from './task'
import { ACCEPTED_EXTENSIONS } from '@/types'
import type { ApplicantResultResponse, ReviewerResultResponse, TaskStatusResponse } from '@/types'

describe('task API adapters', () => {
  it('keeps frontend upload extensions aligned with CP3.5 docx backend support', () => {
    expect(ACCEPTED_EXTENSIONS).toEqual(['jpg', 'jpeg', 'png', 'pdf', 'docx'])
  })

  it('builds browser-safe material preview URL without exposing storage key', () => {
    const url = getMaterialPreviewUrl('SW task/1', 'BUSINESS_LICENSE')

    expect(url).toBe('/task/SW%20task%2F1/material/BUSINESS_LICENSE/preview')
    expect(url).not.toContain('storageKey')
    expect(url).not.toContain('key=')
  })

  it('maps applicant Java DTO issue fields to page findings', () => {
    const dto: ApplicantResultResponse = {
      taskId: 'task-1',
      status: 'PARTIAL_SUCCESS',
      summary: '存在缺失材料',
      missingMaterials: ['ID_CARD'],
      issues: [
        {
          code: 'MISSING_MATERIAL',
          severity: 'BLOCKER',
          message: '身份证缺失',
        },
      ],
    }

    const view = toApplicantResultView(dto)

    expect(view.fieldIssues).toEqual([
      {
        findingType: 'MISSING_MATERIAL',
        severity: 'BLOCKER',
        audience: 'APPLICANT',
        description: '身份证缺失',
        basis: null,
      },
    ])
    expect(view.suggestions).toContain('请补充缺失材料后重新提交，以获取完整的审核辅助结果。')
  })

  it('keeps applicant projection free of reviewer-only fields', () => {
    const dto: ApplicantResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '申请人可见结果',
      missingMaterials: [],
      issues: [
        {
          code: 'MISSING_FIELD',
          severity: 'WARNING',
          message: '请补充联系电话',
        },
      ],
    }

    const view = toApplicantResultView(dto)

    expect(view).toEqual({
      status: 'COMPLETED',
      missingMaterials: [],
      fieldIssues: [
        {
          findingType: 'MISSING_FIELD',
          severity: 'WARNING',
          audience: 'APPLICANT',
          description: '请补充联系电话',
          basis: null,
        },
      ],
      suggestions: ['材料预检查已完成，审批人员将进行进一步审核。'],
      handlingStatus: null,
      handlingStatusLabel: '',
      reviewerRemark: '',
      reviewerActionAt: null,
    })
    expect('riskHints' in view).toBe(false)
    expect('draftOpinion' in view).toBe(false)
    expect('extractedFields' in view).toBe(false)
  })

  it('builds applicant task result view from applicant projection and status snapshot only', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      handlingStatus: 'CORRECTION_REQUIRED',
      handlingStatusLabel: '退回补正',
      reviewerRemark: '请补充营业执照副本',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [
        {
          materialType: 'BUSINESS_LICENSE',
          originalFileName: null,
          uploaded: false,
        },
      ],
    }
    const resultDto: ApplicantResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      handlingStatus: 'CORRECTION_REQUIRED',
      handlingStatusLabel: '退回补正',
      reviewerRemark: '请补充营业执照副本',
      reviewerActionAt: '2026-05-08T10:02:00',
      summary: '申请人可见结果',
      missingMaterials: ['BUSINESS_LICENSE'],
      issues: [
        {
          code: 'MISSING_MATERIAL',
          severity: 'BLOCKER',
          message: '营业执照缺失',
        },
      ],
    }

    const view = toApplicantTaskResultView(statusDto, toApplicantResultView(resultDto))

    expect(view.viewMode).toBe('APPLICANT')
    expect(view.handlingStatus).toBe('CORRECTION_REQUIRED')
    expect(view.handlingStatusLabel).toBe('退回补正')
    expect(view.reviewerRemark).toBe('请补充营业执照副本')
    expect(view.reviewActionLogs).toEqual([])
    expect(view.extractedFields).toEqual({})
    expect(view.riskHints).toEqual([])
    expect(view.draftOpinion).toBe('')
    expect(view.materials).toEqual(statusDto.materials)
    expect(view.requiresManualReview).toBe(true)
  })

  it('maps reviewer Java DTO objects to displayable view fields', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [
        {
          materialType: 'APPLICATION_FORM',
          originalFileName: 'application.pdf',
          uploaded: true,
        },
      ],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '审核辅助结果已生成',
      missingMaterials: [],
      draftOpinion: '建议人工复核后继续办理。',
      extractedFields: {
        applicantName: '某公司',
        annualWaterUse: 1200,
      },
      issues: [
        {
          code: 'WATER_AMOUNT_REVIEW_REQUIRED',
          severity: 'WARNING',
          message: '取水量需要人工复核',
          basisRefs: ['water-permit:mvp:process'],
          applicantVisible: false,
        },
      ],
      riskHints: [
        {
          riskLevel: 'WARNING',
          description: '取水量字段与材料描述需要复核',
          basisRefs: ['water-permit:mvp:application'],
          requiresManualReview: true,
        },
      ],
      manualReviewNotice: '请人工复核证照一致性。',
      handlingStatus: 'MANUAL_REVIEW_REQUIRED',
      handlingStatusLabel: '转人工复核',
      reviewerRemark: '需要核对证照一致性',
      reviewerActionCode: 'TRANSFER_MANUAL_REVIEW',
      reviewerUserId: 2001,
      reviewerDisplayName: '审批员甲',
      reviewerActionAt: '2026-05-08T10:02:00',
      actionLogs: [
        {
          actionCode: 'TRANSFER_MANUAL_REVIEW',
          actionLabel: '转人工复核',
          reviewerRemark: '需要核对证照一致性',
          operatorUserId: 2001,
          operatorDisplayName: '审批员甲',
          fromHandlingStatus: null,
          toHandlingStatus: 'MANUAL_REVIEW_REQUIRED',
          operatedAt: '2026-05-08T10:02:00',
        },
      ],
      toolCallTraces: [
        {
          toolName: 'knowledge_search',
          inputSummary: "query='营业执照', top_k=8",
          outputSummary: 'total=3, ids=[BASIS_MATERIAL_INITIAL_LIST]',
          sourceRefs: ['BASIS_MATERIAL_INITIAL_LIST'],
          status: 'SUCCESS',
          latencyMs: 42,
        },
      ],
      modelMetadata: null,
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.summary).toEqual({
      totalFindings: 1,
      blockerCount: 0,
      warningCount: 1,
      infoCount: 0,
    })
    expect(view.extractedFields).toEqual({
      applicantName: '某公司',
      annualWaterUse: '1200',
    })
    expect(view.findings[0]).toMatchObject({
      findingType: 'WATER_AMOUNT_REVIEW_REQUIRED',
      description: '取水量需要人工复核',
      basis: 'water-permit:mvp:process',
    })
    expect(view.riskHints[0]).toContain('取水量字段与材料描述需要复核')
    expect(view.manualReviewNotice).toBe('请人工复核证照一致性。')
    expect(view.handlingStatus).toBe('MANUAL_REVIEW_REQUIRED')
    expect(view.handlingStatusLabel).toBe('转人工复核')
    expect(view.reviewerRemark).toBe('需要核对证照一致性')
    expect(view.reviewerActionCode).toBe('TRANSFER_MANUAL_REVIEW')
    expect(view.reviewActionLogs).toHaveLength(1)
    expect(view.reviewActionLogs[0]).toMatchObject({
      actionCode: 'TRANSFER_MANUAL_REVIEW',
      actionLabel: '转人工复核',
      toHandlingStatus: 'MANUAL_REVIEW_REQUIRED',
    })
    expect(view.toolCallTraces).toEqual([
      {
        toolName: 'knowledge_search',
        inputSummary: "query='营业执照', top_k=8",
        outputSummary: 'total=3, ids=[BASIS_MATERIAL_INITIAL_LIST]',
        sourceRefs: ['BASIS_MATERIAL_INITIAL_LIST'],
        status: 'SUCCESS',
        latencyMs: 42,
        error: '',
      },
    ])
    expect(view.requiresManualReview).toBe(true)
  })

  it('accepts legacy reviewActionLogs alias when actionLogs is empty', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '审核辅助结果已生成',
      missingMaterials: [],
      draftOpinion: '',
      extractedFields: {},
      issues: [],
      riskHints: [],
      actionLogs: [],
      reviewActionLogs: [
        {
          actionCode: 'APPROVE_INITIAL_REVIEW',
          reviewerRemark: '已通过',
          operatorUserId: 2002,
          operatorDisplayName: '审批员乙',
          toHandlingStatus: 'INITIAL_REVIEW_PASSED',
          operatedAt: '2026-05-08T10:05:00',
        },
      ],
      modelMetadata: null,
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.reviewActionLogs).toHaveLength(1)
    expect(view.reviewActionLogs[0]).toMatchObject({
      actionCode: 'APPROVE_INITIAL_REVIEW',
      actionLabel: '通过初审',
      reviewerRemark: '已通过',
      operatorDisplayName: '审批员乙',
      toHandlingStatus: 'INITIAL_REVIEW_PASSED',
    })
  })

  it('falls back to shared action labels for action logs without backend labels', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '审核辅助结果已生成',
      missingMaterials: [],
      draftOpinion: '',
      extractedFields: {},
      issues: [],
      riskHints: [],
      actionLogs: [
        {
          actionCode: 'RETURN_FOR_CORRECTION',
          reviewerRemark: '补正材料',
          operatorUserId: 2002,
          operatorDisplayName: '审批员乙',
          toHandlingStatus: 'CORRECTION_REQUIRED',
          operatedAt: '2026-05-08T10:05:00',
        },
      ],
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.reviewActionLogs[0].actionLabel).toBe('退回补正')
  })

  it('detects completed initial-review handling statuses', () => {
    expect(isReviewerActionCompleted(null)).toBe(false)
    expect(isReviewerActionCompleted('INITIAL_REVIEW_PASSED')).toBe(true)
    expect(isReviewerActionCompleted('CORRECTION_REQUIRED')).toBe(true)
    expect(isReviewerActionCompleted('MANUAL_REVIEW_REQUIRED')).toBe(true)
  })

  it('normalizes reviewer extracted field snapshots from worker array payloads', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '字段快照已生成',
      missingMaterials: [],
      draftOpinion: '',
      extractedFields: [
        {
          fieldKey: 'applicant.name',
          fieldValue: '某某科技有限公司',
          confidence: 0.93,
          sourceMaterial: 'APPLICATION_FORM',
        },
      ],
      issues: [],
      riskHints: [],
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.extractedFields).toEqual({
      'applicant.name': '某某科技有限公司',
    })
    expect(view.fieldConfidence).toEqual({
      'applicant.name': 0.93,
    })
  })

  it('maps FAILED status to failure category and reason', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'FAILED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'FAILED',
      summary: '模型返回格式错误',
      missingMaterials: [],
      draftOpinion: '',
      extractedFields: {},
      issues: [],
      riskHints: [],
      modelMetadata: 'SCHEMA_MISMATCH',
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.status).toBe('FAILED')
    expect(view.failureCategory).toBe('SCHEMA_MISMATCH')
    expect(view.failureReason).toBe('模型返回格式错误')
    expect(view.requiresManualReview).toBe(true)
  })

  it('marks COMPLETED with BLOCKER as requiring manual review', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '审核辅助结果已生成',
      missingMaterials: [],
      draftOpinion: '建议人工复核后继续办理。',
      extractedFields: {},
      issues: [
        {
          code: 'INCONSISTENT_IDENTITY',
          severity: 'BLOCKER',
          message: '身份信息不一致需人工复核',
          applicantVisible: true,
        },
      ],
      riskHints: [],
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.status).toBe('COMPLETED')
    expect(view.failureCategory).toBeNull()
    expect(view.requiresManualReview).toBe(true)
    expect(view.findings[0].severity).toBe('BLOCKER')
  })

  it('marks completed model failure issue as requiring manual review', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: 'AI审核输出格式校验失败',
      missingMaterials: [],
      draftOpinion: '',
      extractedFields: {},
      issues: [
        {
          code: 'SCHEMA_MISMATCH',
          severity: 'BLOCKER',
          message: '审核输出格式不符合预期，需要人工复核。',
          applicantVisible: false,
        },
      ],
      riskHints: [],
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.status).toBe('COMPLETED')
    expect(view.failureCategory).toBe('SCHEMA_MISMATCH')
    expect(view.failureReason).toBe('AI审核输出格式校验失败')
    expect(view.requiresManualReview).toBe(true)
  })

  it('marks normal COMPLETED without manual review requirement', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'COMPLETED',
      summary: '审核辅助结果已生成',
      missingMaterials: [],
      draftOpinion: '建议通过。',
      extractedFields: {},
      issues: [
        {
          code: 'WATER_AMOUNT_REVIEW_REQUIRED',
          severity: 'WARNING',
          message: '取水量需复核',
          applicantVisible: false,
        },
      ],
      riskHints: [],
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.status).toBe('COMPLETED')
    expect(view.failureCategory).toBeNull()
    expect(view.requiresManualReview).toBe(false)
  })

  it('maps non-terminal reviewer placeholder result without manual review noise', () => {
    const statusDto: TaskStatusResponse = {
      taskId: 'task-1',
      status: 'PROCESSING',
      submittedAt: '2026-05-08T10:00:00',
      updatedAt: '2026-05-08T10:01:00',
      materials: [],
    }
    const resultDto: ReviewerResultResponse = {
      taskId: 'task-1',
      status: 'PROCESSING',
      summary: '审核结果处理中，请稍后查询。',
      missingMaterials: [],
      draftOpinion: '',
      extractedFields: undefined,
      issues: [],
      riskHints: [],
    }

    const view = toReviewerResultView(statusDto, resultDto)

    expect(view.status).toBe('PROCESSING')
    expect(view.extractedFields).toEqual({})
    expect(view.findings).toEqual([])
    expect(view.riskHints).toEqual([])
    expect(view.requiresManualReview).toBe(false)
  })
})
