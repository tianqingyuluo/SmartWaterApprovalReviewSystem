import { describe, expect, it } from 'vitest'
import { toApplicantResultView, toReviewerResultView } from './task'
import type { ApplicantResultResponse, ReviewerResultResponse, TaskStatusResponse } from '@/types'

describe('task API adapters', () => {
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
    })
    expect('riskHints' in view).toBe(false)
    expect('draftOpinion' in view).toBe(false)
    expect('extractedFields' in view).toBe(false)
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
    expect(view.requiresManualReview).toBe(true)
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
